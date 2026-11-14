"""Searchable tile library for World Studio and its modal callers."""

from dataclasses import dataclass

import pygame

from modules.frostage_assets import load_frostage_image
from modules.tile_catalog import GROUPS, THEMES, TileEntry, load_tile_catalog


ROW_HEIGHT = 35
THUMBNAIL_SIZE = 26
PANEL_COLOR = (24, 33, 48)
LIST_COLOR = (16, 21, 32)
ROW_COLOR = (36, 52, 72)
TEXT_COLOR = (232, 240, 250)
MUTED_COLOR = (162, 180, 200)
ACCENT_COLOR = (118, 214, 246)
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
                 frost_assets=None, embedded=False):
        self.tiles = tiles
        self.frost_assets = frost_assets or {}
        self._themes = {key: label for key, (label, _) in THEMES.items()}
        self._themes.update({f"frostage_{key}": f"FrostAge · {label}"
                             for key, label in FROST_CATEGORIES.items()})
        self.favorites = favorites
        self.font = font
        self.select_tile = select_tile
        self.max_favorites = max_favorites
        self.embedded = embedded
        self.search_focused = False
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
        self._row_labels: dict[tuple[str, int], str] = {}
        self.set_bounds(bounds)

    def set_bounds(self, bounds):
        """Move or resize the view without reloading the catalogue."""
        old_list_width = self.list_rect.width if hasattr(self, "list_rect") else None
        if self.embedded:
            self.panel = bounds.copy()
            self.close_rect = pygame.Rect(0, 0, 0, 0)
            self.search_rect = pygame.Rect(bounds.x + 10, bounds.y + 40, bounds.width - 56, 34)
            self.clear_rect = pygame.Rect(self.search_rect.right + 4, self.search_rect.y, 32, 34)
            self.list_rect = pygame.Rect(bounds.x + 10, bounds.y + 83, bounds.width - 20,
                                         max(0, bounds.height - 126))
        else:
            self.panel = pygame.Rect(0, 0, min(790, bounds.width - 64), min(735, bounds.height - 64))
            self.panel.center = bounds.center
            self.close_rect = pygame.Rect(self.panel.right - 113, self.panel.top + 13, 95, 28)
            self.search_rect = pygame.Rect(self.panel.left + 18, self.panel.top + 54,
                                           self.panel.width - 117, 34)
            self.clear_rect = pygame.Rect(self.search_rect.right + 7, self.search_rect.top, 74, 34)
            self.list_rect = pygame.Rect(self.panel.left + 18, self.panel.top + 99,
                                         self.panel.width - 36, self.panel.height - 153)
        if self.list_rect.width != old_list_width:
            self._row_labels.clear()
        self._scroll_by(0)

    def open(self):
        self._entries, self._warnings = load_tile_catalog(self.tiles)
        self._entries += tuple(
            TileEntry(asset.id, f"frostage_{asset.category}",
                      "single" if asset.cells == (1, 1) else "multi")
            for asset in self.frost_assets.values()
            if asset.category in FROST_CATEGORIES
        )
        self._refresh_rows()
        if not self.embedded:
            self.focus_search()

    def close(self):
        self.blur_search()

    def focus_search(self):
        if not self.search_focused:
            self.search_focused = True
            pygame.key.start_text_input()

    def blur_search(self):
        if self.search_focused:
            self.search_focused = False
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
            marker = "−" if expanded else "+"
            self._rows.append(_Row("category", f"{marker}  {label} ({len(entries)})", category))
            if not expanded:
                continue
            if category == FAVORITES:
                if not entries:
                    hint = "Noch keine Favoriten" if self.embedded else "Rechtsklick auf eine Kachel fügt sie hinzu."
                    self._rows.append(_Row("hint", hint, "", 16))
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
            marker = "−" if expanded else "+"
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
        """Return true for a tile selection or dismissal of a modal library."""
        if event.type == pygame.KEYDOWN:
            if self.embedded and not self.search_focused:
                return False
            if event.key == pygame.K_ESCAPE:
                if self.embedded:
                    self.blur_search()
                    return False
                return True
            if event.key == pygame.K_BACKSPACE:
                self._set_query(self._query[:-1])
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and len(self._matches) == 1:
                self.select_tile(self._matches[0].key)
                if self.embedded:
                    self.blur_search()
                return True
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                delta = {
                    pygame.K_UP: -ROW_HEIGHT, pygame.K_DOWN: ROW_HEIGHT,
                    pygame.K_PAGEUP: -self.list_rect.height, pygame.K_PAGEDOWN: self.list_rect.height,
                }
                self._scroll_by(delta[event.key])
        elif event.type == pygame.TEXTINPUT and (not self.embedded or self.search_focused):
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
            if self.search_rect.collidepoint(pos):
                self.focus_search()
                return False
            if self.clear_rect.collidepoint(pos):
                self._set_query("")
                self.focus_search()
                return False
            if self.embedded:
                self.blur_search()
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
        if max_width is not None and max_width <= 0:
            return
        surface = self.font.render(text, True, color)
        if max_width is not None and surface.get_width() > max_width:
            surface = surface.subsurface((0, 0, max_width, surface.get_height()))
        screen.blit(surface, pos)

    def draw(self, screen, current_tile):
        pygame.draw.rect(screen, PANEL_COLOR, self.panel, border_radius=6)
        pygame.draw.rect(screen, ROW_COLOR if self.embedded else ACCENT_COLOR, self.panel,
                         width=1 if self.embedded else 2, border_radius=6)
        if self.embedded:
            self._text(screen, "Baukasten", (self.panel.left + 10, self.panel.top + 11))
        else:
            self._text(screen, "Tile-Bibliothek", (self.panel.left + 18, self.panel.top + 18))
            self._draw_button(screen, self.close_rect, "Schließen")
        pygame.draw.rect(screen, LIST_COLOR, self.search_rect, border_radius=3)
        pygame.draw.rect(screen, ACCENT_COLOR if self.search_focused else MUTED_COLOR,
                         self.search_rect, width=1, border_radius=3)
        placeholder = "Kacheln suchen …" if self.embedded else "Dateiname oder Thema suchen …"
        query = self._query or placeholder
        self._text(screen, query, (self.search_rect.left + 9, self.search_rect.top + 8),
                   color=TEXT_COLOR if self._query else MUTED_COLOR, max_width=self.search_rect.width - 18)
        self._draw_button(screen, self.clear_rect, "×" if self.embedded else "Leeren")
        pygame.draw.rect(screen, LIST_COLOR, self.list_rect)
        previous_clip = screen.get_clip()
        screen.set_clip(self.list_rect.clip(previous_clip))
        for row, rect in self._visible_rows():
            self._draw_row(screen, row, rect, current_tile)
        screen.set_clip(previous_clip)
        if self.embedded:
            self._draw_scrollbar(screen)
            count = self._warnings[0] if self._warnings else f"{len(self._matches)} Kacheln"
            self._text(screen, count, (self.list_rect.left, self.list_rect.bottom + 4),
                       color=ACCENT_COLOR if self._warnings else MUTED_COLOR, max_width=self.list_rect.width)
            self._text(screen, "Rechtsklick: Favoriten", (self.list_rect.left, self.list_rect.bottom + 23),
                       color=MUTED_COLOR, max_width=self.list_rect.width)
            return
        footer = f"{len(self._matches)} Kacheln · Mausrad scrollt · Rechtsklick ändert Favoriten · Esc schließt"
        self._text(screen, footer, (self.list_rect.left, self.list_rect.bottom + 6), color=MUTED_COLOR,
                   max_width=self.list_rect.width)
        if self._warnings:
            self._text(screen, self._warnings[0], (self.list_rect.left, self.list_rect.bottom + 26),
                       color=ACCENT_COLOR, max_width=self.list_rect.width)

    def _draw_scrollbar(self, screen):
        total_height = len(self._rows) * ROW_HEIGHT
        if self.list_rect.height <= 0 or total_height <= self.list_rect.height:
            return
        height = max(12, self.list_rect.height * self.list_rect.height // total_height)
        offset = self._scroll * (self.list_rect.height - height) // (total_height - self.list_rect.height)
        pygame.draw.rect(screen, MUTED_COLOR,
                         (self.list_rect.right + 3, self.list_rect.top + offset, 3, height), border_radius=2)

    def _draw_button(self, screen, rect, label):
        pygame.draw.rect(screen, ROW_COLOR, rect, border_radius=3)
        self._text(screen, label, (rect.left + 8, rect.top + 5))

    def _draw_row(self, screen, row, rect, current_tile):
        x = rect.left + 8 + row.indent
        if row.kind in ("category", "group"):
            pygame.draw.rect(screen, ROW_COLOR, rect.inflate(-2, -2))
        label = row.label
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
            if self.embedded:
                asset = self.frost_assets.get(row.target)
                label = asset.name if asset else row.target
                label = self._fit_tile_label(label.removesuffix(".png"), rect.right - x - 8)
        self._text(screen, label, (x, rect.top + 8),
                   color=MUTED_COLOR if row.kind == "hint" else TEXT_COLOR,
                   max_width=rect.right - x - 8)

    def _fit_tile_label(self, label, width):
        # Numbered tile variants share long prefixes. Keep the distinguishing
        # suffix visible in a narrow panel while search retains the full name.
        key = label, width
        if key not in self._row_labels:
            if self.font.size(label)[0] > width:
                left = right = len(label) // 2
                while left > 0 or right < len(label):
                    if left > len(label) - right:
                        left -= 1
                    else:
                        right += 1
                    shortened = f"{label[:left]}…{label[right:]}"
                    if self.font.size(shortened)[0] <= width:
                        label = shortened
                        break
            self._row_labels[key] = label
        return self._row_labels[key]

    def _make_thumbnail(self, key, bounds):
        if key in self.frost_assets:
            image = load_frostage_image(key)
            if image is not None:
                width, height = image.get_rect().fit(bounds).size
                return pygame.transform.smoothscale(image, (max(1, width), max(1, height)))
        elif (image := self.tiles.get(key)) is not None:
            return pygame.transform.scale(image, bounds.size)
        return None
