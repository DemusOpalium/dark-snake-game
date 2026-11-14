"""Choose independent border graphics and preview one paint operation."""

from dataclasses import dataclass

import pygame

from config import GRID_HEIGHT, GRID_WIDTH
from modules.border_builder import CORNERS, SIDES, BorderPlan


PANEL = (24, 33, 48)
STROKE = (61, 87, 111)
TEXT = (232, 240, 250)
MUTED = (162, 180, 200)
ACCENT = (118, 214, 246)
OVERWRITE = (252, 183, 105)
UNCHANGED = (154, 170, 187)
CORNER = (220, 168, 248)
LABELS = {
    "left": "Links",
    "right": "Rechts",
    "top": "Oben",
    "bottom": "Unten",
    "top_left": "Oben links",
    "top_right": "Oben rechts",
    "bottom_left": "Unten links",
    "bottom_right": "Unten rechts",
}


@dataclass(frozen=True)
class _Slot:
    label_pos: tuple[int, int]
    toggle: pygame.Rect
    choose: pygame.Rect


class BorderBuilderUI:
    """Hold uncommitted brush choices and show their effect on the current floor."""

    def __init__(self, tile, bounds, button_art=None):
        self.plan = BorderPlan()
        self.button_art = button_art
        self._last_tile = tile
        self._side_tiles = {}
        self._corner_tiles = {}
        self._target = None
        self._hover_cell = None
        self._hover_slot = None
        self._pointer = None
        self._show_corners = True
        self._thumbnail_size = None
        self._thumbnails = {}
        self._swatches = {}
        self._message = ""
        self.set_bounds(bounds)

    @property
    def target_pending(self):
        return self._target is not None

    def set_bounds(self, bounds):
        self.panel = pygame.Rect(0, 0, min(bounds.width, 1000), min(bounds.height, 520))
        self.panel.center = bounds.center
        x, y = self.panel.topleft
        right_width = self.panel.width * 44 // 100
        control_width = self.panel.width - right_width - 45
        control_x, preview_x = x + 14, self.panel.right - right_width - 14
        self.all_button = pygame.Rect(control_x, y + 59, min(186, control_width), 38)
        self.side_rows = self._slots(SIDES, control_x, y + 100, control_width, sides=True)
        self.corners_button = pygame.Rect(control_x, y + 228, min(186, control_width), 36)
        self.corner_rows = self._slots(CORNERS, control_x, y + 267, control_width)
        self.cancel_button = pygame.Rect(x + 14, self.panel.bottom - 46, 116, 30)
        self.apply_button = pygame.Rect(self.panel.right - 133, self.panel.bottom - 46, 119, 30)
        self._preview_frame = pygame.Rect(preview_x, y + 65, right_width, self.panel.height - 251)
        size = max(1, min((right_width - 12) // GRID_WIDTH, (self._preview_frame.height - 12) // GRID_HEIGHT))
        self.preview_rect = pygame.Rect(0, 0, GRID_WIDTH * size, GRID_HEIGHT * size)
        self.preview_rect.center = self._preview_frame.center
        self._hover_cell = None
        self._hover_slot = None
        self._pointer = None

    @staticmethod
    def _slots(keys, x, y, width, *, sides=False):
        slot_width = (width - 8) // 2
        slots = {}
        for index, key in enumerate(keys):
            row, column = divmod(index, 2)
            left = x + column * (slot_width + 8)
            if sides:
                top = y + row * 64
                slots[key] = _Slot((left, top), pygame.Rect(left, top, slot_width - 25, 34),
                                   pygame.Rect(left, top + 35, slot_width, 26))
            else:
                top = y + row * 51
                slots[key] = _Slot((left, top), pygame.Rect(left, top + 18, 42, 27),
                                   pygame.Rect(left + 47, top + 18, slot_width - 47, 27))
        return slots

    def _visible_rows(self):
        return (self.side_rows, self.corner_rows) if self._show_corners else (self.side_rows,)

    def _choose(self, key):
        self._target = key
        self._message = f"{LABELS.get(key, 'Gesamter Rand')} · Bodenkachel links wählen."

    def _choices(self, key):
        return (self.plan.sides, self._side_tiles) if key in SIDES else (self.plan.corners, self._corner_tiles)

    def _toggle(self, key):
        choices, saved = self._choices(key)
        if key in choices:
            del choices[key]
        elif tile := saved.get(key, self._last_tile):
            choices[key] = tile
        else:
            self._choose(key)
            return
        self._target = None
        self._message = ""

    def _toggle_all(self):
        if all(key in self.plan.sides for key in SIDES):
            self.plan.sides.clear()
        elif self._last_tile is None:
            self._choose("all")
            return
        else:
            for key in SIDES:
                self.plan.sides.setdefault(key, self._side_tiles.get(key, self._last_tile))
        self._target = None
        self._message = ""

    def select_tile(self, tile):
        """Receive a Classic floor graphic from the existing library."""
        if not self.target_pending:
            self._message = "Wähle zuerst rechts eine Randseite oder Ecke."
            return False
        keys = SIDES if self._target == "all" else (self._target,)
        for key in keys:
            choices, saved = self._choices(key)
            choices[key] = saved[key] = tile
        self._last_tile = tile
        self._target = None
        self._message = ""
        return True

    def reject_tile(self):
        self._message = "Bitte links eine Kachel für die Bodenebene wählen."

    def _has_changes(self, level_map):
        return not self.target_pending and any(cell.changed for cell in self.plan.preview(level_map))

    def handle_event(self, event, level_map):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "cancel"
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER) and self._has_changes(level_map):
                return "apply"
        if event.type == pygame.MOUSEMOTION:
            self._pointer = event.pos
            self._hover_slot = next(
                (key for rows in self._visible_rows()
                 for key, slot in rows.items() if slot.choose.collidepoint(event.pos)),
                None,
            )
            if self.preview_rect.collidepoint(event.pos):
                cell_size = self.preview_rect.width // GRID_WIDTH
                self._hover_cell = ((event.pos[0] - self.preview_rect.x) // cell_size,
                                    (event.pos[1] - self.preview_rect.y) // cell_size)
            else:
                self._hover_cell = None
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None
        if self.cancel_button.collidepoint(event.pos):
            return "cancel"
        if self.apply_button.collidepoint(event.pos):
            return "apply" if self._has_changes(level_map) else None
        if self.all_button.collidepoint(event.pos):
            self._toggle_all()
            return None
        if self.corners_button.collidepoint(event.pos):
            self._show_corners = not self._show_corners
            if not self._show_corners and self._target in CORNERS:
                self._target = None
                self._message = ""
            return None
        for rows in self._visible_rows():
            for key, slot in rows.items():
                if slot.toggle.collidepoint(event.pos):
                    self._toggle(key)
                    return None
                if slot.choose.collidepoint(event.pos):
                    self._choose(key)
                    return None
        return None

    def draw(self, screen, level_map, tile_images, text, button):
        pygame.draw.rect(screen, PANEL, self.panel, border_radius=6)
        pygame.draw.rect(screen, STROKE, self.panel, width=1, border_radius=6)
        x, y = self.panel.topleft
        left = x + 14
        text(screen, "Rand-Builder", (left, y + 10), TEXT)
        text(screen, "Seiten einzeln wählen und die Änderung vor dem Anwenden prüfen.", (left, y + 34), MUTED,
             max_width=self.panel.width - 28)
        all_on = all(key in self.plan.sides for key in SIDES)
        self._draw_art(screen, "border_all", "Gesamter Rand", self.all_button, button, active=all_on)
        self._draw_slots(screen, self.side_rows, self.plan.sides, tile_images, text, button)
        self._draw_art(screen, "border_corner", "Ecken", self.corners_button, button,
                       selected=self._show_corners)
        text(screen, "Einblenden" if not self._show_corners else "Ausblenden",
             (self.corners_button.right + 7, self.corners_button.y + 10), MUTED,
             max_width=self._preview_frame.left - self.corners_button.right - 15)
        if self._show_corners:
            self._draw_slots(screen, self.corner_rows, self.plan.corners, tile_images, text, button)
        text(screen, "Automatische Ecken · Oben/Unten zuerst", (left, y + 366), MUTED,
             max_width=self._preview_frame.left - left - 8)

        preview = {(cell.x, cell.y): cell for cell in self.plan.preview(level_map)}
        self._draw_preview(screen, level_map, tile_images, preview, text)
        button(screen, "Abbrechen", self.cancel_button)
        if not self.target_pending and any(cell.changed for cell in preview.values()):
            button(screen, "Anwenden", self.apply_button, ACCENT)
        else:
            pygame.draw.rect(screen, STROKE, self.apply_button, width=1, border_radius=5)
            text(screen, "Anwenden", (self.apply_button.x + 8, self.apply_button.y + 5), MUTED)

        usable = self.apply_button.left - self.cancel_button.right - 20
        text(screen, self._message or self._slot_detail() or self._art_hint()
             or "Nur Boden-Grafik · Strg+Z macht rückgängig.",
             (self.cancel_button.right + 9, self.cancel_button.y + 6), ACCENT if self._message else MUTED,
             max_width=usable)

    def _draw_art(self, screen, action_id, label, rect, button, *, active=False, selected=False):
        hovered = self._pointer is not None and rect.collidepoint(self._pointer)
        if self.button_art is not None:
            self.button_art.draw(screen, action_id, label, rect, active=active, selected=selected,
                                 hovered=hovered)
        else:
            button(screen, label, rect, ACCENT if active or selected or hovered else None)

    def _art_hint(self):
        if self._pointer is None:
            return None
        if self.all_button.collidepoint(self._pointer):
            return "Alle vier Randseiten gemeinsam ein- oder ausschalten."
        if self.corners_button.collidepoint(self._pointer):
            return "Optionale Eckgrafiken ein- oder ausblenden."
        for key, slot in self.side_rows.items():
            if slot.toggle.collidepoint(self._pointer):
                return f"{LABELS[key]} · Diese Randseite ein- oder ausschalten."
        return None

    def _slot_detail(self):
        key = self._hover_slot
        if key is None:
            return None
        if key in CORNERS:
            choice = self.plan.corner_choice(key)
            tile = choice[0] if choice else self.plan.corners.get(key)
        else:
            tile = self.plan.sides.get(key)
        return f"{LABELS[key]} · {tile}" if tile else None

    def _draw_slots(self, screen, rows, choices, tile_images, text, button):
        for key, slot in rows.items():
            tile = choices.get(key)
            if key in SIDES:
                self._draw_art(screen, f"border_{key}", LABELS[key], slot.toggle, button, active=bool(tile))
                text(screen, "An" if tile else "Aus", (slot.toggle.right + 3, slot.toggle.y + 9),
                     ACCENT if tile else MUTED)
            else:
                text(screen, LABELS[key], slot.label_pos, TEXT)
                button(screen, "An" if tile else "Aus", slot.toggle, ACCENT if tile else None)
            pygame.draw.rect(screen, (29, 43, 62), slot.choose, border_radius=5)
            highlighted = key in (self._target, self._hover_slot)
            pygame.draw.rect(screen, ACCENT if highlighted else STROKE, slot.choose,
                             width=2 if key == self._target else 1, border_radius=5)
            label = tile or ("Auto" if key in CORNERS else "Grafik wählen")
            swatch_tile = tile
            if key in CORNERS and (choice := self.plan.corner_choice(key)) is not None and tile is None:
                swatch_tile, source = choice
                label = "Von " + LABELS[source]
            elif key in CORNERS and tile:
                if self.plan.corner_choice(key) is None:
                    label = "Wartet"
            if key == self._target:
                label = "Links wählen"
            label_x, label_y = slot.choose.x + 5, slot.choose.y + 4
            if swatch_tile in tile_images and key != self._target:
                if swatch_tile not in self._swatches:
                    self._swatches[swatch_tile] = pygame.transform.scale(tile_images[swatch_tile], (19, 19))
                screen.blit(self._swatches[swatch_tile], (label_x, label_y))
                label_x += 24
            text(screen, label, (label_x, label_y), TEXT if tile else MUTED,
                 max_width=slot.choose.right - label_x - 4)

    def _draw_preview(self, screen, level_map, tile_images, preview, text):
        rect = self.preview_rect
        size = rect.width // GRID_WIDTH
        pygame.draw.rect(screen, (16, 21, 32), self._preview_frame, border_radius=5)
        pygame.draw.rect(screen, STROKE, self._preview_frame, width=1, border_radius=5)
        pygame.draw.rect(screen, (36, 52, 72), rect)
        if size != self._thumbnail_size:
            self._thumbnail_size = size
            self._thumbnails.clear()
        for y, row in enumerate(level_map):
            for x, existing in enumerate(row):
                entry = preview.get((x, y))
                tile = entry.tile if entry else existing
                cell = pygame.Rect(rect.x + x * size, rect.y + y * size, size, size)
                if tile in tile_images:
                    if tile not in self._thumbnails:
                        self._thumbnails[tile] = pygame.transform.scale(tile_images[tile], (size, size))
                    screen.blit(self._thumbnails[tile], cell)
                if entry:
                    color = OVERWRITE if entry.overwrites else ACCENT if entry.changed else UNCHANGED
                    pygame.draw.rect(screen, color, cell, width=1)
                    if x in (0, GRID_WIDTH - 1) and y in (0, GRID_HEIGHT - 1):
                        screen.set_at(cell.center, CORNER)
                if self._hover_cell == (x, y):
                    pygame.draw.rect(screen, TEXT, cell, width=1)
        x, y = self._preview_frame.left, self._preview_frame.bottom + 7
        width = self._preview_frame.width
        text(screen, f"{len(preview)} Zielzellen · {sum(cell.changed for cell in preview.values())} geändert",
             (x, y), TEXT, max_width=width)
        overwritten = sum(cell.overwrites for cell in preview.values())
        text(screen, f"{overwritten} vorhandene Kacheln ersetzt", (x, y + 20), OVERWRITE, max_width=width)
        text(screen, "Blau neu · Orange ersetzt · Violett Ecke", (x, y + 40), MUTED, max_width=width)
        if self._hover_cell is not None:
            self._draw_cell_details(screen, level_map, preview, text, x, y + 62, width)

    def _draw_cell_details(self, screen, level_map, preview, text, left, top, width):
        x, y = self._hover_cell
        entry = preview.get((x, y))
        existing = level_map[y][x]
        if entry is None:
            text(screen, f"X {x} / Y {y} · bleibt unverändert", (left, top), MUTED, max_width=width)
            return
        text(screen, f"X {x} / Y {y} · {LABELS[entry.source]}", (left, top), TEXT, max_width=width)
        text(screen, "Vorher " + (existing or "leer"), (left, top + 18), MUTED, max_width=width)
        text(screen, "Danach " + entry.tile, (left, top + 36), ACCENT, max_width=width)
