"""Tile-based editor for independent level drafts."""

import pygame

from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH
from modules.graphics import TILE_IMAGES
from modules.level_drafts import (legacy_map_exists, list_drafts, normalize_draft_name,
                                  read_draft, read_legacy_map, suggest_draft_name, write_draft)

TOOLBAR_W = 200
BTN_H = 28
ZOOM = 0.72
FAV_ROW_H = 50
SCROLL_TOP = 312
TILE_ROW_H = WINDOW_HEIGHT - SCROLL_TOP - 12
MAP_TOP = 104
CELL_SIZE = max(1, min(int(GRID_SIZE * ZOOM), (WINDOW_WIDTH - TOOLBAR_W - 12) // GRID_WIDTH,
                       (WINDOW_HEIGHT - MAP_TOP - 42) // GRID_HEIGHT))
MAP_RECT = pygame.Rect(TOOLBAR_W, MAP_TOP, GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE)
PALETTE_RECT = pygame.Rect(0, SCROLL_TOP, TOOLBAR_W, TILE_ROW_H)
PALETTE_COLUMNS = min(5, max(1, (TOOLBAR_W - 20) // (GRID_SIZE + 6)))
MAX_FAV = 8
OPEN_ROWS = 8
OPEN_ROW_H = 27

COLOR_BG = (25, 25, 25)
COLOR_BTN = (50, 50, 50)
COLOR_FAV = (70, 70, 70)
COLOR_TEXT = (255, 255, 255)
COLOR_SELECT = (255, 255, 0)
COLOR_FRAME = (120, 0, 120)
COLOR_GRID = (54, 54, 65)


def _empty_map():
    return [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]


def _copy_map(level_map):
    return [row.copy() for row in level_map]


class LevelEditor:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.tiles = dict(sorted(TILE_IMAGES.items()))
        self._tile_keys = tuple(self.tiles)
        self._scaled_tiles = {}
        self.current_tile = next(iter(self.tiles), None)
        self.map = _empty_map()
        self._saved_map = _copy_map(self.map)
        self.name = ""
        self._saved_name = None
        self._legacy = False
        self.undo_stack = []
        self.redo_stack = []
        self.favorites = []
        self.tile_scroll_offset = 0
        self._stroke_button = None
        self._stroke_changed = False
        self.preview_active = False
        self._preview_background = None
        self._dialog = None
        self.tile_library = None
        self.world_tree = None
        self.font = pygame.font.SysFont("Arial", 16)
        self.info = ""
        self.buttons = self._make_buttons()

    @property
    def dirty(self):
        return self.map != self._saved_map

    @property
    def dialog_open(self):
        return self._dialog is not None

    def _make_buttons(self):
        preview = (("Vorschau beenden", self.stop_sim) if self.preview_active
                   else ("Vorschau starten", self.start_sim))
        rows = [
            (("Neu", self.new_map), ("Öffnen", self.load_map)),
            (("Speichern", self.save_map),),
            (preview,),
            (("Rand", self.set_border), ("Mittelfeld", self.fill_middle)),
            (("Undo", self.undo), ("Redo", self.redo)),
            (("Für Classic wählen", self.select_for_classic),),
            (("Classic-Standard", self.select_classic_default),),
        ]
        buttons = []
        for row, controls in enumerate(rows):
            width = (TOOLBAR_W - 20 - 4 * (len(controls) - 1)) // len(controls)
            for column, (label, action) in enumerate(controls):
                rect = pygame.Rect(10 + column * (width + 4), 10 + row * (BTN_H + 4), width, BTN_H)
                buttons.append((label, rect, action))
        buttons.extend((
            ("Welten", pygame.Rect(WINDOW_WIDTH - 304, 10, 140, BTN_H), self.open_world_tree),
            ("Tile-Bibliothek", pygame.Rect(WINDOW_WIDTH - 154, 10, 140, BTN_H), self.open_tile_library),
        ))
        return buttons

    def toggle(self):
        if self.active:
            self.request_close()
        else:
            self.active = True
            if not self.name:
                self.name = self._suggest_name()
            self.info = "Editor geöffnet"

    def request_close(self, on_close=None):
        if self.dialog_open:
            if self._dialog["kind"] == "discard":
                return False
            self._dismiss_dialog()

        def close():
            if self.dirty:
                self.map = _copy_map(self._saved_map)
                self.undo_stack.clear()
                self.redo_stack.clear()
            self.stop_sim()
            self._stroke_button = None
            self.active = False
            if on_close is not None:
                on_close()
            return True

        return self._after_discard_confirmation(close)

    def _after_discard_confirmation(self, action):
        if self.dirty:
            self._stroke_button = None
            self._dialog = {"kind": "discard", "action": action}
            return False
        return action()

    def _suggest_name(self):
        try:
            return suggest_draft_name()
        except OSError:
            return "Level_001"

    def _available_name(self, name):
        name = normalize_draft_name(name)
        if any(existing.casefold() == name.casefold() for existing in list_drafts()):
            raise FileExistsError(f"Ein Entwurf mit dem Namen {name} existiert bereits.")
        return name

    def new_map(self, name=None):
        if name is None:
            self._name_dialog("Neuer Entwurf", self._suggest_name(), self._new_named_map)
            return False
        try:
            return self._new_named_map(self._available_name(name))
        except (OSError, ValueError) as error:
            self.info = f"Neuer Entwurf nicht möglich. {error}"
            return False

    def _new_named_map(self, name):
        def create():
            self._set_document(name, _empty_map())
            self.info = f"Neuer Entwurf {name}"
            return True

        return self._after_discard_confirmation(create)

    def save_map(self):
        if self._legacy:
            self._name_dialog("Altformat als Entwurf speichern", self._suggest_name(), self._save_named_map)
            return False
        name = self._saved_name or self.name or self._suggest_name()
        return self._save_named_map(name, replace=self._saved_name is not None)

    def _save_named_map(self, name, *, replace=False):
        try:
            saved_name = write_draft(name, self.map, replace=replace)
        except FileExistsError as error:
            self.info = str(error)
            if not replace:
                self._name_dialog("Unter einem neuen Namen speichern", self._suggest_name(),
                                  self._save_named_map)
            return False
        except (OSError, ValueError) as error:
            self.info = f"Level konnte nicht gespeichert werden. {error}"
            return False
        self.name = self._saved_name = saved_name
        self._saved_map = _copy_map(self.map)
        self._legacy = False
        self.info = f"{saved_name}.json gespeichert"
        return True

    def load_map(self, name=None):
        if name is None:
            try:
                names = list_drafts()
                if legacy_map_exists():
                    names.append(None)
            except OSError as error:
                self.info = f"Entwürfe konnten nicht gelesen werden. {error}"
                return False
            if not names:
                self.info = "Keine gespeicherten Entwürfe vorhanden."
                return False
            self._stroke_button = None
            self._dialog = {"kind": "open", "names": names, "selected": 0}
            return False
        try:
            name = normalize_draft_name(name)
        except ValueError as error:
            self.info = f"Level konnte nicht geladen werden. {error}"
            return False
        return self._load_document(name, lambda: read_draft(name), saved_name=name)

    def load_legacy_map(self):
        return self._load_document("custom_level.json", read_legacy_map, legacy=True)

    def _load_document(self, name, read, *, saved_name=None, legacy=False):
        def load():
            try:
                level_map = read()
            except (OSError, ValueError) as error:
                self.info = f"Level konnte nicht geladen werden. {error}"
                return False
            self._set_document(name, level_map, saved_name=saved_name, legacy=legacy)
            self.info = f"{name} geladen"
            return True

        return self._after_discard_confirmation(load)

    def _set_document(self, name, level_map, *, saved_name=None, legacy=False):
        self._stroke_button = None
        self.name = name
        self.map = level_map
        self._saved_map = _copy_map(level_map)
        self._saved_name = saved_name
        self._legacy = legacy
        self.undo_stack.clear()
        self.redo_stack.clear()

    def read_map(self):
        """Read the legacy single-file map without changing the editor."""
        return read_legacy_map()

    def _display_name(self):
        if self.world_tree and self.world_tree.library and self._saved_name:
            level = self.world_tree.library.level_for_draft(self._saved_name)
            if level:
                return level.name
        return self.name

    def open_world_tree(self):
        from modules.world_tree import WorldTree

        if self.world_tree is None:
            self.world_tree = WorldTree(pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), self.font,
                                        self._open_world_draft, self._world_name_dialog, self._dismiss_dialog)
        try:
            self.world_tree.open(self._saved_name)
        except (OSError, ValueError) as error:
            self.info = f"Weltbibliothek konnte nicht geladen werden. {error}"
            return
        self._stroke_button = None
        self._show_world_tree()

    def _show_world_tree(self):
        self._dialog = {"kind": "world"}

    def _open_world_draft(self, name):
        self._dismiss_dialog()
        self.load_map(name)

    def _world_name_dialog(self, title, name, submit):
        def accept(value):
            self._show_world_tree()
            submit(value)

        self._name_dialog(title, name, accept, validate=str.strip, cancel=self._show_world_tree)

    def open_tile_library(self):
        from modules.tile_library import TileLibrary

        if self.tile_library is None:
            self.tile_library = TileLibrary(self.tiles, self.favorites,
                                            pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
                                            self.font, self._select_tile, max_favorites=MAX_FAV)
        self.tile_library.open()
        self._stroke_button = None
        self._dialog = {"kind": "tiles"}

    def _select_tile(self, key):
        self.current_tile = key
        self.info = f"{key}.png ausgewählt"

    def select_for_classic(self):
        if self.dirty or not (self._saved_name or self._legacy):
            self.info = "Bitte zuerst einen Entwurf speichern oder eine gespeicherte Karte öffnen."
            return
        name = self._display_name()
        self.game.choose_classic_background(name, self.map)
        self.info = f"{name} für den nächsten Classic-Start gewählt"

    def select_classic_default(self):
        self.game.choose_classic_background(None, None)
        self.info = "Standardhintergrund für den nächsten Classic-Start gewählt"

    def start_sim(self):
        self.preview_active = True
        self._preview_background = pygame.transform.scale(self.game.default_background_surface, MAP_RECT.size)
        self._stroke_button = None
        self.buttons = self._make_buttons()
        self.info = "Visuelle Vorschau der Karte"

    def stop_sim(self):
        self.preview_active = False
        self._preview_background = None
        self.buttons = self._make_buttons()
        self.info = "Vorschau beendet"

    def handle_event(self, event):
        if not self.active:
            return
        if self.dialog_open:
            self._handle_dialog(event)
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos, event.button)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == self._stroke_button:
            self._stroke_button = None
        elif event.type == pygame.WINDOWFOCUSLOST:
            self._stroke_button = None
        elif event.type == pygame.MOUSEMOTION and self._stroke_button:
            self._paint(*event.pos)
        elif event.type == pygame.MOUSEWHEEL and not self.preview_active:
            if PALETTE_RECT.collidepoint(getattr(event, "pos", pygame.mouse.get_pos())):
                rows = (len(self._tile_keys) + PALETTE_COLUMNS - 1) // PALETTE_COLUMNS
                height = 20 + rows * (GRID_SIZE + 4) - 4
                minimum = min(0, PALETTE_RECT.height - height)
                self.tile_scroll_offset = max(minimum, min(0, self.tile_scroll_offset + event.y * 20))

    def _handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.preview_active:
                self.stop_sim()
            else:
                self.request_close()
        elif not self.preview_active and getattr(event, "mod", 0) & pygame.KMOD_CTRL:
            shortcuts = {pygame.K_n: self.new_map, pygame.K_o: self.load_map,
                         pygame.K_s: self.save_map, pygame.K_z: self.undo, pygame.K_y: self.redo}
            action = shortcuts.get(event.key)
            if action:
                action()

    def _handle_click(self, pos, button):
        if button == 1:
            for _, rect, action in self.buttons:
                if rect.collidepoint(pos):
                    if not self.preview_active or action == self.stop_sim:
                        action()
                    return
        if self.preview_active or button not in (1, 3):
            return
        if PALETTE_RECT.collidepoint(pos):
            for key, rect in self._visible_tiles():
                if rect.collidepoint(pos):
                    if button == 1:
                        self.current_tile = key
                    elif key not in self.favorites and len(self.favorites) < MAX_FAV:
                        self.favorites.append(key)
                        self.info = f"{key} zu Favoriten hinzugefügt"
                    return
        elif button == 1 and pos[1] < FAV_ROW_H:
            for index, key in enumerate(self.favorites):
                if self._favorite_rect(index).collidepoint(pos):
                    self.current_tile = key
                    return
        if MAP_RECT.collidepoint(pos):
            self._stroke_button = button
            self._stroke_changed = False
            self._paint(*pos)

    def _visible_tiles(self):
        for i, key in enumerate(self._tile_keys):
            row, column = divmod(i, PALETTE_COLUMNS)
            rect = pygame.Rect(10 + column * (GRID_SIZE + 6),
                               SCROLL_TOP + 10 + row * (GRID_SIZE + 4) + self.tile_scroll_offset,
                               GRID_SIZE, GRID_SIZE)
            if rect.colliderect(PALETTE_RECT):
                yield key, rect
            elif rect.top >= PALETTE_RECT.bottom:
                break

    def _favorite_rect(self, index):
        return pygame.Rect(TOOLBAR_W + 10 + index * (GRID_SIZE + 6), 10, GRID_SIZE, GRID_SIZE)

    def _paint(self, mx, my):
        if not MAP_RECT.collidepoint(mx, my):
            return
        gx = (mx - MAP_RECT.x) // CELL_SIZE
        gy = (my - MAP_RECT.y) // CELL_SIZE
        tile = None if self._stroke_button == 3 else self.current_tile
        if self.map[gy][gx] == tile or (tile is None and self._stroke_button != 3):
            return
        if self._stroke_button is None or not self._stroke_changed:
            self._store_undo()
            self._stroke_changed = True
        self.map[gy][gx] = tile
        self.info = "Kachel entfernt" if tile is None else f"{tile} gesetzt"

    def _store_undo(self):
        self.undo_stack.append(_copy_map(self.map))
        self.redo_stack.clear()

    def undo(self):
        self._stroke_button = None
        if self.undo_stack:
            self.redo_stack.append(self.map)
            self.map = self.undo_stack.pop()
            self.info = "Bearbeitung rückgängig gemacht"

    def redo(self):
        self._stroke_button = None
        if self.redo_stack:
            self.undo_stack.append(self.map)
            self.map = self.redo_stack.pop()
            self.info = "Bearbeitung wiederholt"

    def fill_middle(self):
        if self.current_tile is not None:
            self._store_undo()
            for row in self.map[1:-1]:
                row[1:-1] = [self.current_tile] * (GRID_WIDTH - 2)
            self.info = "Mittelfeld gefüllt"

    def set_border(self):
        if self.current_tile is not None:
            self._store_undo()
            for row in self.map:
                row[0] = row[-1] = self.current_tile
            self.map[0][:] = self.map[-1][:] = [self.current_tile] * GRID_WIDTH
            self.info = "Rand gesetzt"

    def _name_dialog(self, title, text, submit, *, validate=None, cancel=None):
        self._stroke_button = None
        self._dialog = {"kind": "name", "title": title, "text": text, "select_all": True, "submit": submit,
                        "validate": validate or self._available_name, "cancel": cancel}
        pygame.key.start_text_input()

    def _dismiss_dialog(self):
        if self._dialog["kind"] == "name":
            pygame.key.stop_text_input()
        elif self._dialog["kind"] == "tiles":
            self.tile_library.close()
        self._dialog = None

    def _cancel_dialog(self):
        cancel = self._dialog.get("cancel")
        self._dismiss_dialog()
        if cancel is not None:
            cancel()

    def _dialog_panel(self):
        height = 310 if self._dialog["kind"] == "open" else 174
        width = min(540, WINDOW_WIDTH - 40)
        return pygame.Rect((WINDOW_WIDTH - width) // 2, (WINDOW_HEIGHT - height) // 2, width, height)

    def _discard_buttons(self, panel):
        width = (panel.width - 52) // 2
        return (pygame.Rect(panel.x + 20, panel.bottom - 48, width, BTN_H),
                pygame.Rect(panel.right - 20 - width, panel.bottom - 48, width, BTN_H))

    def _open_cancel_button(self, panel):
        return pygame.Rect(panel.right - 116, panel.bottom - 37, 96, BTN_H)

    def _open_first(self):
        dialog = self._dialog
        return max(0, min(dialog["selected"] - OPEN_ROWS // 2, len(dialog["names"]) - OPEN_ROWS))

    def _open_selected(self, index):
        name = self._dialog["names"][index]
        self._dismiss_dialog()
        if name is None:
            self.load_legacy_map()
        else:
            self.load_map(name)

    def _handle_dialog(self, event):
        dialog = self._dialog
        kind = dialog["kind"]
        if kind == "tiles":
            if self.tile_library.handle_event(event):
                self._dismiss_dialog()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cancel_dialog()
            return
        if kind == "name":
            self._handle_name(event)
        elif kind == "discard":
            self._handle_discard(event)
        elif kind == "open":
            self._handle_open(event)
        elif kind == "world":
            self.world_tree.handle_event(event)

    def _handle_name(self, event):
        dialog = self._dialog
        if event.type == pygame.TEXTINPUT:
            previous = "" if dialog["select_all"] else dialog["text"]
            dialog["text"] = (previous + event.text)[:100]
            dialog["select_all"] = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            dialog["text"] = "" if dialog["select_all"] else dialog["text"][:-1]
            dialog["select_all"] = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_a and getattr(event, "mod", 0) & pygame.KMOD_CTRL:
            dialog["select_all"] = True
        elif (event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
              or event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
              and self._discard_buttons(self._dialog_panel())[1].collidepoint(event.pos)):
            try:
                name = dialog["validate"](dialog["text"])
            except (OSError, ValueError) as error:
                dialog["error"] = str(error)
                return
            self._dismiss_dialog()
            dialog["submit"](name)
        elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
              and self._discard_buttons(self._dialog_panel())[0].collidepoint(event.pos)):
            self._cancel_dialog()

    def _handle_discard(self, event):
        action = self._dialog["action"]
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_v:
                self._dismiss_dialog()
                action()
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._dismiss_dialog()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            keep, discard = self._discard_buttons(self._dialog_panel())
            if discard.collidepoint(event.pos):
                self._dismiss_dialog()
                action()
            elif keep.collidepoint(event.pos):
                self._dismiss_dialog()

    def _handle_open(self, event):
        dialog = self._dialog
        count = len(dialog["names"])
        move = 0
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._open_selected(dialog["selected"])
                return
            move = {pygame.K_UP: -1, pygame.K_DOWN: 1, pygame.K_PAGEUP: -OPEN_ROWS,
                    pygame.K_PAGEDOWN: OPEN_ROWS}.get(event.key, 0)
        elif event.type == pygame.MOUSEWHEEL:
            move = -event.y
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            panel = self._dialog_panel()
            if self._open_cancel_button(panel).collidepoint(event.pos):
                self._dismiss_dialog()
                return
            rows = pygame.Rect(panel.x + 20, panel.y + 47, panel.width - 40, OPEN_ROWS * OPEN_ROW_H)
            if rows.collidepoint(event.pos):
                index = self._open_first() + (event.pos[1] - rows.y) // OPEN_ROW_H
                if index < count:
                    self._open_selected(index)
                    return
        dialog["selected"] = max(0, min(count - 1, dialog["selected"] + move))

    def _draw_text(self, screen, value, pos, color=COLOR_TEXT, *, max_width=None):
        text = self.font.render(value, True, color)
        if max_width is not None and text.get_width() > max_width:
            text = text.subsurface((0, 0, max_width, text.get_height()))
        screen.blit(text, pos)

    def _draw_button(self, screen, label, rect):
        pygame.draw.rect(screen, COLOR_BTN, rect)
        self._draw_text(screen, label, (rect.x + 6, rect.y + 5))

    def draw(self, screen):
        if not self.active:
            return
        screen.fill(COLOR_BG)
        if self.dialog_open and self._dialog["kind"] == "tiles":
            self.tile_library.draw(screen, self.current_tile)
            return
        if not self.preview_active:
            self._draw_tiles(screen)
            classic = getattr(self.game, "classic_level_name", None) or "Standard"
            self._draw_text(screen, f"Nächster Classic-Start · {classic}", (TOOLBAR_W, 78))
        for label, rect, _ in self.buttons:
            if not self.preview_active or label == "Vorschau beenden":
                self._draw_button(screen, label, rect)

        title = self._display_name() or "Neuer Entwurf"
        if self._legacy:
            title += " (Altformat)"
        elif self._saved_name is None:
            title += " (noch nicht gespeichert)"
        if self.dirty:
            title = f"* Ungespeichert · {title}"
        self._draw_text(screen, title, (TOOLBAR_W, 54), COLOR_SELECT if self.dirty else COLOR_TEXT)
        self._draw_map(screen)

        hint = ("Karten-Vorschau · Esc zurück"
                if self.preview_active else "Links malen · Rechts löschen · Mausrad über Kacheln")
        self._draw_text(screen, hint, (TOOLBAR_W, WINDOW_HEIGHT - 39))
        self._draw_text(screen, self.info, (TOOLBAR_W, WINDOW_HEIGHT - 20), COLOR_SELECT)
        if self.dialog_open:
            if self._dialog["kind"] == "world":
                self.world_tree.draw(screen)
            else:
                self._draw_dialog(screen)

    def _draw_tiles(self, screen):
        pygame.draw.rect(screen, COLOR_FAV, (TOOLBAR_W, 0, WINDOW_WIDTH - TOOLBAR_W, FAV_ROW_H))
        for index, key in enumerate(self.favorites):
            rect = self._favorite_rect(index)
            screen.blit(self.tiles[key], rect)
            if key == self.current_tile:
                pygame.draw.rect(screen, COLOR_SELECT, rect, 2)

        self._draw_text(screen, "Kacheln", (10, SCROLL_TOP - 39))
        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(10, SCROLL_TOP - 20, TOOLBAR_W - 18, 20))
        self._draw_text(screen, self.current_tile or "–", (10, SCROLL_TOP - 20), COLOR_SELECT)
        screen.set_clip(old_clip)
        pygame.draw.rect(screen, COLOR_BTN, PALETTE_RECT)
        pygame.draw.rect(screen, COLOR_FRAME, PALETTE_RECT, 2)
        screen.set_clip(PALETTE_RECT)
        for key, rect in self._visible_tiles():
            screen.blit(self.tiles[key], rect)
            if key == self.current_tile:
                pygame.draw.rect(screen, COLOR_SELECT, rect, 2)
        screen.set_clip(old_clip)

    def _draw_map(self, screen):
        if self.preview_active:
            screen.blit(self._preview_background, MAP_RECT)
        else:
            pygame.draw.rect(screen, (35, 35, 44), MAP_RECT)
        for y, row in enumerate(self.map):
            for x, key in enumerate(row):
                if key in self.tiles:
                    if key not in self._scaled_tiles:
                        self._scaled_tiles[key] = pygame.transform.scale(self.tiles[key], (CELL_SIZE, CELL_SIZE))
                    screen.blit(self._scaled_tiles[key], (MAP_RECT.x + x * CELL_SIZE,
                                                          MAP_RECT.y + y * CELL_SIZE))
        if not self.preview_active:
            for x in range(0, MAP_RECT.width, CELL_SIZE):
                pygame.draw.line(screen, COLOR_GRID, (MAP_RECT.x + x, MAP_RECT.y),
                                 (MAP_RECT.x + x, MAP_RECT.bottom - 1))
            for y in range(0, MAP_RECT.height, CELL_SIZE):
                pygame.draw.line(screen, COLOR_GRID, (MAP_RECT.x, MAP_RECT.y + y),
                                 (MAP_RECT.right - 1, MAP_RECT.y + y))
        pygame.draw.rect(screen, COLOR_FRAME, MAP_RECT, 2)

    def _draw_dialog(self, screen):
        dialog = self._dialog
        panel = self._dialog_panel()
        pygame.draw.rect(screen, COLOR_BG, panel)
        pygame.draw.rect(screen, COLOR_SELECT, panel, 2)
        x, y = panel.x + 20, panel.y + 16
        if dialog["kind"] == "name":
            self._draw_text(screen, dialog["title"], (x, y))
            field = pygame.Rect(x, y + 29, panel.width - 40, BTN_H)
            pygame.draw.rect(screen, COLOR_FAV if dialog["select_all"] else COLOR_BTN, field)
            old_clip = screen.get_clip()
            screen.set_clip(field)
            self._draw_text(screen, dialog["text"], (field.x + 6, field.y + 5))
            screen.set_clip(old_clip)
            self._draw_text(screen, dialog.get("error", "Name des Entwurfs"), (x, y + 66),
                            max_width=panel.width - 40)
            cancel, accept = self._discard_buttons(panel)
            self._draw_button(screen, "Abbrechen", cancel)
            self._draw_button(screen, "Übernehmen", accept)
        elif dialog["kind"] == "discard":
            self._draw_text(screen, "Ungespeicherte Änderungen verwerfen?", (x, y))
            self._draw_text(screen, "Zum Speichern zuerst weiterbearbeiten.", (x, y + 33))
            keep, discard = self._discard_buttons(panel)
            self._draw_button(screen, "Weiter bearbeiten", keep)
            self._draw_button(screen, "Verwerfen [V]", discard)
        else:
            self._draw_text(screen, "Entwurf öffnen", (x, y))
            first = self._open_first()
            for index, name in enumerate(dialog["names"][first:first + OPEN_ROWS], start=first):
                rect = pygame.Rect(x, panel.y + 47 + (index - first) * OPEN_ROW_H,
                                   panel.width - 40, OPEN_ROW_H - 1)
                pygame.draw.rect(screen, COLOR_FAV if index == dialog["selected"] else COLOR_BTN, rect)
                label = f"{name}.json" if name is not None else "custom_level.json (Altformat)"
                self._draw_text(screen, label, (rect.x + 6, rect.y + 4), max_width=rect.width - 12)
            self._draw_text(screen, "↑ ↓ auswählen · Enter öffnen", (x, panel.bottom - 31))
            self._draw_button(screen, "Abbrechen", self._open_cancel_button(panel))
