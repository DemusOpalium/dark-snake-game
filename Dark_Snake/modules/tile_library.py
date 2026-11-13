"""Searchable tile library opened from the level editor."""

from dataclasses import dataclass

import pygame

from modules.frostage_assets import load_frostage_image
from modules.tile_catalog import GROUPS, THEMES, TileEntry, load_tile_catalog


ROW_HEIGHT = 35
THUMBNAIL_SIZE = 26
PANEL_COLOR = (32, 31, 42)
LIST_COLOR = (25, 24, 32)
ROW_COLOR = (47, 44, 61)
TEXT_COLOR = (248, 244, 255)
MUTED_COLOR = (184, 177, 202)
ACCENT_COLOR = (200, 164, 255)
FAVORITES = "favorites"
FROST_CATEGORIES = {
    "ground": "Boden", "walls": "Wände", "objects": "Objekte", "roof": "Dächer",
    "aoe": "AoE", "enemies": "Gegner", "projectiles": "Projektile",
    "items": "Items",
}


@dataclass(frozen=True)
class _Row:
    kind: str
    label: str
    target: str | tuple[str, str]
    indent: int = 0


class TileLibrary:
    def __init__(self, tiles, favorites, bounds, font, select_tile, *, max_favorites=8,
                 frost_assets=None):
        self.tiles = tiles
        self.frost_assets = frost_assets or {}
        self._themes = {key: label for key, (label, _) in THEMES.items()}
        self._themes.update({f"frostage_{key}": f"FrostAge · {label}"
                             for key, label in FROST_CATEGORIES.items()})
        self.favorites = favorites
        self.font = font
        self.select_tile = select_tile
        self.max_favorites = max_favorites
        self.panel = pygame.Rect(0, 0, min(790, bounds.width - 64), min(735, bounds.height - 64))
        self.panel.center = bounds.center
        self.close_rect = pygame.Rect(self.panel.right - 113, self.panel.top + 13, 95, 28)
        self.search_rect = pygame.Rect(self.panel.left + 18, self.panel.top + 54,
                                       self.panel.width - 117, 34)
        self.clear_rect = pygame.Rect(self.search_rect.right + 7, self.search_rect.top, 74, 34)
        self.list_rect = pygame.Rect(self.panel.left + 18, self.panel.top + 99,
                                     self.panel.width - 36, self.panel.height - 153)
        self._entries: tuple[TileEntry, ...] = ()
        self._warnings: tuple[str, ...] = ()
        self._query = ""
        self._expanded: set[str] = set()
        self._closed_groups: set[tuple[str, str]] = set()
        self._search_closed: set[str] = set()
        self._search_closed_groups: set[tuple[str, str]] = set()
        self._scroll = 0
        self._rows: list[_Row] = []
        self._matches: tuple[TileEntry, ...] = ()
        self._thumbnails: dict[str, pygame.Surface] = {}

    def open(self):
        self._entries, self._warnings = load_tile_catalog(self.tiles)
        self._entries += tuple(
            TileEntry(asset.id, f"frostage_{asset.category}",
                      "single" if asset.cells == (1, 1) else "multi")
            for asset in self.frost_assets.values()
            if asset.category in FROST_CATEGORIES
        )
        self._refresh_rows()
        pygame.key.start_text_input()

    def close(self):
        pygame.key.stop_text_input()

    def _refresh_rows(self):
        terms = self._query.casefold().split()
        self._matches = tuple(entry for entry in self._entries if self._matches_terms(entry, terms))
        by_category = {category: [] for category in self._themes}
        for entry in self._matches:
            by_category[entry.category].append(entry)

        self._rows = []
        favorites = [entry for entry in self._matches if entry.key in self.favorites]
        categories = [(FAVORITES, "Favoriten", favorites)]
        categories.extend((category, label, by_category[category])
                          for category, label in self._themes.items())
        for category, label, entries in categories:
            if not entries and (terms or category != FAVORITES):
                continue
            expanded = (category not in self._search_closed if terms else category in self._expanded)
            marker = "▼" if expanded else "▶"
            self._rows.append(_Row("category", f"{marker}  {label} ({len(entries)})", category))
            if not expanded:
                continue
            if category == FAVORITES:
                if not entries:
                    self._rows.append(_Row("hint", "Rechtsklick auf eine Kachel fügt sie hinzu.", "", 16))
                self._add_tile_rows(entries, 16)
            else:
                self._add_group_rows(category, entries, bool(terms))
        if not self._rows:
            self._rows.append(_Row("hint", "Keine Kacheln gefunden.", ""))
        self._scroll_by(0)

    def _matches_terms(self, entry, terms):
        if not terms:
            return True
        searchable = (f"{self._tile_label(entry)} {entry.key} {entry.category} "
                      f"{self._themes[entry.category]} {entry.group} {GROUPS[entry.group]}").casefold()
        return all(term in searchable for term in terms)

    def _tile_label(self, entry):
        asset = self.frost_assets.get(entry.key)
        if asset is None:
            return f"{entry.key}.png"
        width, height = asset.cells
        return f"{asset.name} · {width}×{height}"

    def _add_group_rows(self, category, entries, searching):
        closed_groups = self._search_closed_groups if searching else self._closed_groups
        for group, label in GROUPS.items():
            members = [entry for entry in entries if entry.group == group]
            if not members:
                continue
            target = (category, group)
            expanded = target not in closed_groups
            marker = "▼" if expanded else "▶"
            self._rows.append(_Row("group", f"{marker}  {label} ({len(members)})", target, 16))
            if expanded:
                self._add_tile_rows(members, 32)

    def _add_tile_rows(self, entries, indent):
        self._rows.extend(_Row("tile", self._tile_label(entry), entry.key, indent) for entry in entries)

    def _set_query(self, query):
        self._query = query[:100]
        self._scroll = 0
        self._search_closed.clear()
        self._search_closed_groups.clear()
        self._refresh_rows()

    def _scroll_by(self, amount):
        maximum = max(0, len(self._rows) * ROW_HEIGHT - self.list_rect.height)
        self._scroll = max(0, min(maximum, self._scroll + amount))

    def _visible_rows(self):
        first = self._scroll // ROW_HEIGHT
        for index in range(first, len(self._rows)):
            y = self.list_rect.top + index * ROW_HEIGHT - self._scroll
            if y >= self.list_rect.bottom:
                break
            yield self._rows[index], pygame.Rect(self.list_rect.left, y, self.list_rect.width, ROW_HEIGHT)

    def handle_event(self, event) -> bool:
        """Return true when the editor should dismiss the library."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return True
            if event.key == pygame.K_BACKSPACE:
                self._set_query(self._query[:-1])
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(self._matches) == 1:
                self.select_tile(self._matches[0].key)
                return True
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                delta = {
                    pygame.K_UP: -ROW_HEIGHT, pygame.K_DOWN: ROW_HEIGHT,
                    pygame.K_PAGEUP: -self.list_rect.height, pygame.K_PAGEDOWN: self.list_rect.height,
                }
                self._scroll_by(delta[event.key])
        elif event.type == pygame.TEXTINPUT:
            self._set_query(self._query + event.text)
        elif event.type == pygame.MOUSEWHEEL:
            if self.list_rect.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                self._scroll_by(-event.y * ROW_HEIGHT * 3)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._click(event.pos, event.button)
        return False

    def _click(self, pos, button):
        if button == 1:
            if self.close_rect.collidepoint(pos):
                return True
            if self.clear_rect.collidepoint(pos):
                self._set_query("")
        if not self.list_rect.collidepoint(pos):
            return False
        index = (pos[1] - self.list_rect.top + self._scroll) // ROW_HEIGHT
        if index >= len(self._rows):
            return False
        row = self._rows[index]
        if row.kind == "tile":
            if button == 1:
                self.select_tile(row.target)
                return True
            if button == 3:
                self._toggle_favorite(row.target)
        elif button == 1 and row.kind in ("category", "group"):
            if row.kind == "category":
                state = self._search_closed if self._query.split() else self._expanded
            else:
                state = self._search_closed_groups if self._query.split() else self._closed_groups
            if row.target in state:
                state.remove(row.target)
            else:
                state.add(row.target)
            self._refresh_rows()
        return False

    def _toggle_favorite(self, key):
        if key in self.favorites:
            self.favorites.remove(key)
        elif len(self.favorites) < self.max_favorites:
            self.favorites.append(key)
        self._refresh_rows()

    def _text(self, screen, text, pos, *, color=TEXT_COLOR, max_width=None):
        surface = self.font.render(text, True, color)
        if max_width is not None and surface.get_width() > max_width:
            surface = surface.subsurface((0, 0, max_width, surface.get_height()))
        screen.blit(surface, pos)

    def draw(self, screen, current_tile):
        pygame.draw.rect(screen, PANEL_COLOR, self.panel, border_radius=6)
        pygame.draw.rect(screen, ACCENT_COLOR, self.panel, width=2, border_radius=6)
        self._text(screen, "Tile-Bibliothek", (self.panel.left + 18, self.panel.top + 18))
        self._draw_button(screen, self.close_rect, "Schließen")
        pygame.draw.rect(screen, LIST_COLOR, self.search_rect, border_radius=3)
        pygame.draw.rect(screen, ACCENT_COLOR, self.search_rect, width=1, border_radius=3)
        query = self._query or "Dateiname oder Thema suchen …"
        self._text(screen, query, (self.search_rect.left + 9, self.search_rect.top + 8),
                   color=TEXT_COLOR if self._query else MUTED_COLOR, max_width=self.search_rect.width - 18)
        self._draw_button(screen, self.clear_rect, "Leeren")
        pygame.draw.rect(screen, LIST_COLOR, self.list_rect)
        previous_clip = screen.get_clip()
        screen.set_clip(self.list_rect.clip(previous_clip))
        for row, rect in self._visible_rows():
            self._draw_row(screen, row, rect, current_tile)
        screen.set_clip(previous_clip)
        footer = f"{len(self._matches)} Kacheln · Mausrad scrollt · Rechtsklick ändert Favoriten · Esc schließt"
        self._text(screen, footer, (self.list_rect.left, self.list_rect.bottom + 6), color=MUTED_COLOR)
        if self._warnings:
            self._text(screen, self._warnings[0], (self.list_rect.left, self.list_rect.bottom + 26),
                       color=ACCENT_COLOR, max_width=self.list_rect.width)

    def _draw_button(self, screen, rect, label):
        pygame.draw.rect(screen, ROW_COLOR, rect, border_radius=3)
        self._text(screen, label, (rect.left + 8, rect.top + 5))

    def _draw_row(self, screen, row, rect, current_tile):
        x = rect.left + 8 + row.indent
        if row.kind in ("category", "group"):
            pygame.draw.rect(screen, ROW_COLOR, rect.inflate(-2, -2))
        if row.kind == "tile":
            thumb_rect = pygame.Rect(x, rect.top + 4, THUMBNAIL_SIZE, THUMBNAIL_SIZE)
            if row.target not in self._thumbnails:
                self._thumbnails[row.target] = self._make_thumbnail(row.target, thumb_rect)
            thumbnail = self._thumbnails[row.target]
            if thumbnail is not None:
                screen.blit(thumbnail, thumbnail.get_rect(center=thumb_rect.center))
            if row.target == current_tile:
                pygame.draw.rect(screen, ACCENT_COLOR, rect.inflate(-2, -2), width=1)
            x += THUMBNAIL_SIZE + 9
        self._text(screen, row.label, (x, rect.top + 8),
                   color=MUTED_COLOR if row.kind == "hint" else TEXT_COLOR,
                   max_width=rect.right - x - 8)

    def _make_thumbnail(self, key, bounds):
        if key in self.frost_assets:
            image = load_frostage_image(key)
            if image is not None:
                width, height = image.get_rect().fit(bounds).size
                return pygame.transform.smoothscale(image, (max(1, width), max(1, height)))
        elif (image := self.tiles.get(key)) is not None:
            return pygame.transform.scale(image, bounds.size)
        return None
