"""Tile-based editor for independent level drafts."""

import time

import pygame

from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH, WINDOW_HEIGHT, WINDOW_WIDTH
from modules.effect_settings import EFFECT_COLORS, EffectSettings, draw_effect_overlay
from modules.frostage_assets import frostage_assets, load_frostage_image
from modules.graphic_objects import (GraphicObject, can_place_graphic_object, draw_graphic_object,
                                     draw_graphic_objects, object_anchor_at, place_graphic_object)
from modules.graphics import TILE_IMAGES
from modules.level_drafts import (COLLISION_TYPES, LevelDocument, legacy_map_exists, list_drafts,
                                  load_level_document, normalize_draft_name, read_legacy_map,
                                  read_level_file, suggest_draft_name, write_draft)
from modules.level_effects import CellEffects, DamageField, SlowField
from modules.level_playtest import COLLISION_COLORS, LevelPlaytest, draw_collision_overlay
from modules.resources import find_asset
from modules.roof_editor_settings import RoofSettingsEditor
from modules.roof_render import draw_roof_objects
from modules.roof_settings import RoofVisibility, is_roof_asset

TOOLBAR_W = 200
BTN_H = 28
ZOOM = 0.72
FAV_ROW_H = 50
SCROLL_TOP = 312
TILE_ROW_H = WINDOW_HEIGHT - SCROLL_TOP - 12
MAP_TOP = 200
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

PLACEMENT_TOOLS = (
    ("graphics", "Nur Grafik", 96, "Grafik"),
    ("combined", "Grafik + Kollision", 142, "beide Ebenen"),
    ("collision", "Nur Kollision", 114, "Kollision"),
)
EFFECT_TOOLS = (("damage", "Schaden"), ("slow", "Slow"))
GRAPHIC_LAYERS = (("ground", "Boden", 70), ("objects", "Objekte", 74), ("roof", "Dach / Foreground", 151))
ERASE_LABELS = {mode: description for mode, _, _, description in PLACEMENT_TOOLS}
ERASE_LABELS.update({"damage": "Schaden", "slow": "Slow"})


def _empty_map():
    return [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]


def _copy_map(level_map):
    return [row.copy() for row in level_map]


class LevelEditor:
    def __init__(self, game):
        self.game = game
        self.active = False
        self.tiles = dict(sorted(TILE_IMAGES.items()))
        self.frost_assets = frostage_assets()
        self._tile_keys = tuple(self.tiles)
        self._scaled_tiles = {}
        self._frost_favorite_thumbnails = {}
        self.current_tile = next(iter(self.tiles), None)
        self._object_brush = None
        self._moving_objects = False
        self._transferring_roof = False
        self._move_anchor = None
        self._move_offset = (0, 0)
        self._hover_cell = None
        self.map = _empty_map()
        self.collisions = {}
        self.effects = {}
        self.objects = {}
        self.roofs = {}
        self.roof_visibility = RoofVisibility()
        self._saved_layers = self._snapshot()
        self.graphic_layer = "ground"
        self.placement_mode = "graphics"
        self.collision_type = "WALL"
        self.show_collisions = True
        self.show_effects = True
        self.show_roofs = True
        self.damage_brush = DamageField()
        self.slow_brush = SlowField()
        self.effect_settings = None
        self.roof_settings_editor = None
        self.playtest = None
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
        return self._layers() != self._saved_layers

    @property
    def dialog_open(self):
        return self._dialog is not None

    def _make_buttons(self):
        preview = (("Vorschau beenden", self.stop_sim) if self.preview_active
                   else ("Vorschau starten", self.start_sim))
        test_controls = (("Test beenden", self.stop_playtest),) if self.playtest is not None else (
            ("Test 1P", lambda: self.start_playtest(1)), ("Test 2P", lambda: self.start_playtest(2)))
        rows = [
            (("Neu", self.new_map), ("Öffnen", self.load_map)),
            (("Speichern", self.save_map),),
            (preview,),
            (("Rand", self.set_border), ("Mittelfeld", self.fill_middle)),
            (("Undo", self.undo), ("Redo", self.redo)),
            (("Für Classic wählen", self.select_for_classic),),
            (("Classic-Standard", self.select_classic_default),),
            test_controls,
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
            ("Objekt verschieben", pygame.Rect(WINDOW_WIDTH - 304, 71, 140, BTN_H), self._toggle_object_move),
            ("Objektgröße", pygame.Rect(WINDOW_WIDTH - 154, 71, 140, BTN_H), self._open_object_size),
        ))
        x = TOOLBAR_W
        for layer, label, width in GRAPHIC_LAYERS:
            buttons.append((label, pygame.Rect(x, 71, width, BTN_H),
                            lambda layer=layer: self._set_graphic_layer(layer)))
            x += width + 4
        x = TOOLBAR_W
        for label, width, action in (
            ("Dachwerte", 91, self.open_roof_settings),
            ("Auf Dachebene", 117, self._toggle_roof_transfer),
            ("Dach-Demo", 95, self.load_roof_demo),
            ("Dachansicht", 95, self._toggle_roof_overlay),
        ):
            buttons.append((label, pygame.Rect(x, 103, width, BTN_H), action))
            x += width + 4
        x = TOOLBAR_W
        collision_toolbar_y = MAP_TOP - 2 * (BTN_H + 4)
        for mode, label, width, _ in PLACEMENT_TOOLS:
            buttons.append((label, pygame.Rect(x, collision_toolbar_y, width, BTN_H),
                            lambda mode=mode: self._set_placement_mode(mode)))
            x += width + 4
        for kind in COLLISION_TYPES:
            buttons.append((kind, pygame.Rect(x, collision_toolbar_y, 75, BTN_H),
                            lambda kind=kind: self._set_collision_type(kind)))
            x += 79
        buttons.append(("Kollision ein/aus", pygame.Rect(x, collision_toolbar_y, 138, BTN_H),
                        self._toggle_collision_overlay))
        effect_toolbar_y = MAP_TOP - BTN_H - 4
        for index, (mode, label) in enumerate(EFFECT_TOOLS):
            buttons.append((label, pygame.Rect(TOOLBAR_W + index * 100, effect_toolbar_y, 96, BTN_H),
                            lambda mode=mode: self._set_placement_mode(mode)))
        buttons.extend((
            ("Effektwerte", pygame.Rect(TOOLBAR_W + 200, effect_toolbar_y, 106, BTN_H), self.open_effect_settings),
            ("Effekte ein/aus", pygame.Rect(TOOLBAR_W + 310, effect_toolbar_y, 126, BTN_H),
             self._toggle_effect_overlay),
        ))
        return buttons

    def _set_placement_mode(self, mode):
        if mode == "combined" and self.graphic_layer == "roof":
            self.info = "Dachebene und Kollision werden getrennt bearbeitet."
            return
        self._stroke_button = None
        self._stop_object_move()
        self.placement_mode = mode

    def _set_graphic_layer(self, layer):
        self._set_placement_mode("graphics")
        self.graphic_layer = layer
        if layer == "roof":
            self.show_roofs = True

    def _set_collision_type(self, kind):
        self._stroke_button = None
        self.collision_type = kind

    def _toggle_collision_overlay(self):
        self.show_collisions = not self.show_collisions
        self.info = "Kollisionsansicht ein" if self.show_collisions else "Kollisionsansicht aus"

    def _toggle_effect_overlay(self):
        self.show_effects = not self.show_effects
        self.info = "Effektmarkierungen ein" if self.show_effects else "Effektmarkierungen aus"

    def _toggle_roof_overlay(self):
        self.show_roofs = not self.show_roofs
        self.info = "Dächer in der Bearbeitung sichtbar" if self.show_roofs else "Dächer in der Bearbeitung ausgeblendet"

    def open_effect_settings(self):
        self._stroke_button = None
        self.effect_settings = EffectSettings(self.damage_brush, self.slow_brush,
                                              pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
        self._dialog = {"kind": "effects"}
        pygame.key.start_text_input()

    def open_roof_settings(self):
        self._stroke_button = None
        self._stop_object_move()
        self.roof_settings_editor = RoofSettingsEditor(
            self.roof_visibility, pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
        )
        self._dialog = {"kind": "roof_settings"}
        pygame.key.start_text_input()

    def toggle(self):
        if self.active:
            self.request_close()
        else:
            self.active = True
            if not self.name:
                self.name = self._suggest_name()
            self.info = "Editor geöffnet"

    def request_close(self, on_close=None):
        if self.playtest is not None:
            self.stop_playtest()
        if self.dialog_open:
            if self._dialog["kind"] == "discard":
                return False
            self._dismiss_dialog()

        def close():
            if self.dirty:
                saved_map, collision, effects, objects, roofs, visibility = self._saved_layers
                self._restore_layers((_copy_map(saved_map), collision.copy(), effects.copy(), objects.copy(),
                                      roofs.copy(), visibility))
                self.undo_stack.clear()
                self.redo_stack.clear()
            self.stop_sim()
            self._stop_object_move()
            self._hover_cell = None
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
            saved_name = write_draft(name, self.map, collision=self.collisions,
                                     effects=self.effects, objects=self.objects, roofs=self.roofs,
                                     roof_visibility=self.roof_visibility, replace=replace)
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
        self._saved_layers = self._snapshot()
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
        return self._load_document(name, lambda: load_level_document(name), saved_name=name)

    def load_legacy_map(self):
        return self._load_document("custom_level.json", lambda: LevelDocument(read_legacy_map()), legacy=True)

    def load_roof_demo(self):
        return self._load_document(
            "FrostAge-Dachbogen", lambda: read_level_file(find_asset("levels", "frostage_roof_demo.json")),
            notice="Dach-Demo geladen · Test 1P/2P starten und mit W bzw. ↑ durch den Bogen fahren.",
        )

    def _load_document(self, name, read, *, saved_name=None, legacy=False, notice=None):
        def load():
            try:
                document = read()
            except (OSError, ValueError) as error:
                self.info = f"Level konnte nicht geladen werden. {error}"
                return False
            self._set_document(name, document.graphics, collisions=document.collision,
                               effects=document.effects, objects=document.objects,
                               roofs=document.roofs, roof_visibility=document.roof_visibility,
                               saved_name=saved_name, legacy=legacy)
            self.info = notice if notice is not None else f"{name} geladen"
            return True

        return self._after_discard_confirmation(load)

    def _set_document(self, name, level_map, *, collisions=None, effects=None, objects=None,
                      roofs=None, roof_visibility=None,
                      saved_name=None, legacy=False):
        self._stroke_button = None
        self._stop_object_move()
        self._hover_cell = None
        self.name = name
        self.map = level_map
        self.collisions = {} if collisions is None else collisions
        self.effects = {} if effects is None else effects
        self.objects = {} if objects is None else objects
        self.roofs = {} if roofs is None else roofs
        self.roof_visibility = RoofVisibility() if roof_visibility is None else roof_visibility
        self.show_roofs = True
        self._saved_layers = self._snapshot()
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
                                            self.font, self._select_tile, max_favorites=MAX_FAV,
                                            frost_assets=self.frost_assets)
        self.tile_library.open()
        self._stroke_button = None
        self._dialog = {"kind": "tiles"}

    def _select_tile(self, key):
        self.current_tile = key
        self._object_brush = None
        self._stop_object_move()
        asset = self.frost_assets.get(key)
        if asset is None:
            self.graphic_layer = "ground"
            self.info = f"{key}.png ausgewählt"
            return
        self._object_brush = GraphicObject(key, *asset.cells)
        self._set_graphic_layer("roof" if asset.category == "roof" else "objects")
        self.info = f"{asset.name} · {asset.cells[0]}×{asset.cells[1]} ausgewählt"

    def _open_object_size(self):
        anchor = self._move_anchor
        layer_objects = self._selected_layer_objects()
        item = layer_objects.get(anchor) if anchor is not None else self._selected_object()
        if item is None:
            self.info = "Zuerst eine FrostAge-Grafik aus der Bibliothek auswählen."
            return

        def validate(value):
            try:
                width, height = map(int, value.lower().replace("×", "x").split("x"))
            except ValueError as error:
                raise ValueError("Bitte eine Rastergröße wie 4x4 eingeben.") from error
            return GraphicObject(item.asset_id, width, height)

        def apply_size(updated):
            if anchor is None:
                self._object_brush = updated
            elif updated != item:
                if not can_place_graphic_object(layer_objects, anchor, updated, moving=anchor):
                    self.info = "Die Größe reicht aus der Karte oder über ein anderes Objekt."
                    return
                self._store_undo()
                place_graphic_object(layer_objects, anchor, updated, moving=anchor)
            self.info = f"Objektgröße {updated.width}×{updated.height}"

        self._name_dialog("Objektgröße im Raster, z. B. 4x4", f"{item.width}x{item.height}",
                          apply_size, validate=validate)

    def _stop_object_move(self):
        self._moving_objects = False
        self._transferring_roof = False
        self._move_anchor = None

    def _toggle_object_move(self):
        if self._moving_objects:
            self._stop_object_move()
            self.info = "Verschieben beendet"
        else:
            self._stroke_button = None
            self._stop_object_move()
            if self.graphic_layer == "ground":
                self._set_graphic_layer("objects")
            elif self.graphic_layer == "roof":
                self.show_roofs = True
            self._moving_objects = True
            self.info = "Objekt der aktiven Ebene anklicken."

    def _selected_layer_objects(self):
        return self.roofs if self.graphic_layer == "roof" else self.objects

    def _toggle_roof_transfer(self):
        if self._transferring_roof:
            self._stop_object_move()
            self.info = "Dachübertragung beendet"
            return
        self._set_graphic_layer("objects")
        self._transferring_roof = True
        self.info = "Ein vorhandenes Dach auf der Objektebene anklicken."

    def _transfer_roof_at(self, cell):
        anchor = object_anchor_at(self.objects, cell)
        if anchor is None or not is_roof_asset(self.objects[anchor].asset_id):
            self.info = "Hier liegt kein FrostAge-Dach auf der Objektebene."
            return
        item = self.objects[anchor]
        if not can_place_graphic_object(self.roofs, anchor, item):
            self.info = "Auf der Dachebene ist dieser Bereich bereits belegt."
            return
        self._store_undo()
        self.roofs[anchor] = self.objects.pop(anchor)
        self._set_graphic_layer("roof")
        self.info = "Dach auf die Vordergrundebene verschoben"

    def _move_object_at(self, cell):
        objects = self._selected_layer_objects()
        if self._move_anchor is None:
            anchor = object_anchor_at(objects, cell)
            if anchor is not None:
                self._move_anchor = anchor
                self._move_offset = cell[0] - anchor[0], cell[1] - anchor[1]
                self.info = "Zielposition anklicken · Esc bricht ab"
            return
        old = self._move_anchor
        target = cell[0] - self._move_offset[0], cell[1] - self._move_offset[1]
        item = objects[old]
        if not can_place_graphic_object(objects, target, item, moving=old):
            self.info = "Ziel liegt außerhalb der Karte oder über einem anderen Objekt."
            return
        if target != old:
            self._store_undo()
            place_graphic_object(objects, target, item, moving=old)
            self.info = "Grafikobjekt verschoben"
        self._move_anchor = None

    def select_for_classic(self):
        if self.dirty or not (self._saved_name or self._legacy):
            self.info = "Bitte zuerst einen Entwurf speichern oder eine gespeicherte Karte öffnen."
            return
        name = self._display_name()
        self.game.choose_classic_background(name, self.map, roof_objects=self.roofs,
                                            roof_visibility=self.roof_visibility)
        self.info = f"{name} für den nächsten Classic-Start gewählt"

    def select_classic_default(self):
        self.game.choose_classic_background(None, None)
        self.info = "Standardhintergrund für den nächsten Classic-Start gewählt"

    def start_sim(self):
        self.preview_active = True
        self._stop_object_move()
        self._preview_background = pygame.transform.scale(self.game.default_background_surface, MAP_RECT.size)
        self._stroke_button = None
        self.buttons = self._make_buttons()
        self.info = "Visuelle Vorschau der Karte"

    def stop_sim(self):
        self.preview_active = False
        self._preview_background = None
        self.buttons = self._make_buttons()
        self.info = "Vorschau beendet"

    def start_playtest(self, player_count):
        try:
            session = LevelPlaytest(self.collisions, player_count, started_at=time.monotonic(), effects=self.effects,
                                    roof_objects=self.roofs, roof_visibility=self.roof_visibility)
        except ValueError as error:
            self.info = str(error)
            return
        self.playtest = session
        self._stop_object_move()
        self._preview_background = pygame.transform.scale(self.game.default_background_surface, MAP_RECT.size)
        self._stroke_button = None
        self.buttons = self._make_buttons()
        self.info = "Leveltest gestartet"

    def stop_playtest(self):
        self.playtest = None
        self._preview_background = None
        self.buttons = self._make_buttons()
        self.info = "Leveltest beendet · Entwurf unverändert"

    def handle_event(self, event, actions=()):
        if not self.active:
            return
        if self.playtest is not None:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_F2):
                self.stop_playtest()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos, event.button)
            else:
                self.playtest.apply_actions(actions)
        elif self.dialog_open:
            self._handle_dialog(event)
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos, event.button)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == self._stroke_button:
            self._stroke_button = None
        elif event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWLEAVE):
            self._stroke_button = None
            self._hover_cell = None
        elif event.type == pygame.MOUSEMOTION:
            self._hover_cell = self._map_cell(event.pos)
            if self._stroke_button:
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
            elif self._moving_objects or self._transferring_roof:
                self._stop_object_move()
                self.info = "Objektwerkzeug beendet"
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
                    if self._button_available(action):
                        action()
                    return
        if self.preview_active or self.playtest is not None or button not in (1, 3):
            return
        if PALETTE_RECT.collidepoint(pos):
            for key, rect in self._visible_tiles():
                if rect.collidepoint(pos):
                    if button == 1:
                        self._select_tile(key)
                    elif key not in self.favorites and len(self.favorites) < MAX_FAV:
                        self.favorites.append(key)
                        self.info = f"{key} zu Favoriten hinzugefügt"
                    return
        elif button == 1 and pos[1] < FAV_ROW_H:
            for index, key in enumerate(self.favorites):
                if self._favorite_rect(index).collidepoint(pos):
                    self._select_tile(key)
                    return
        if (cell := self._map_cell(pos)) is not None:
            self._hover_cell = cell
            if self._transferring_roof:
                if button == 1:
                    self._transfer_roof_at(cell)
                return
            if self._moving_objects:
                if button == 1:
                    self._move_object_at(cell)
                return
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

    @staticmethod
    def _map_cell(position):
        if MAP_RECT.collidepoint(position):
            x, y = position
            return (x - MAP_RECT.x) // CELL_SIZE, (y - MAP_RECT.y) // CELL_SIZE
        return None

    def _selected_object(self):
        if self._object_brush and self._object_brush.asset_id == self.current_tile:
            layer = "roof" if is_roof_asset(self.current_tile) else "objects"
            if self.graphic_layer == layer:
                return self._object_brush
        return None

    def _paint(self, mx, my):
        cell = self._map_cell((mx, my))
        if cell is None:
            return
        gx, gy = cell
        erase = self._stroke_button == 3
        if self.placement_mode in ("damage", "slow"):
            self._paint_effect(cell, erase)
            return
        if self.placement_mode != "collision" and self.graphic_layer != "ground":
            objects = self._selected_layer_objects()
            if erase and (anchor := object_anchor_at(objects, cell)) is not None:
                self._begin_stroke_change()
                del objects[anchor]
                if self.placement_mode == "combined":
                    self.collisions.pop(cell, None)
                self.info = "Ganzes Grafikobjekt entfernt"
                return
            if not erase and (item := self._selected_object()) is not None:
                self._paint_object(objects, cell, item)
                return
        tile = self.current_tile if not erase and self.current_tile in self.tiles else None
        collision = None if erase else self.collision_type
        change_graphics = (self.graphic_layer == "ground" and self.placement_mode != "collision"
                           and (erase or tile is not None)
                           and self.map[gy][gx] != tile)
        change_collision = self.placement_mode != "graphics" and self.collisions.get(cell) != collision
        if not (change_graphics or change_collision):
            return
        self._begin_stroke_change()
        if change_graphics:
            self.map[gy][gx] = tile
        if change_collision:
            if erase:
                del self.collisions[cell]
            else:
                self.collisions[cell] = collision
        if change_collision and change_graphics:
            self.info = "Beide Ebenen gelöscht" if erase else f"Kachel und {collision} gesetzt"
        elif change_collision:
            self.info = "Kollision gelöscht" if erase else f"{collision} gesetzt"
        else:
            self.info = "Kachel entfernt" if erase else f"{tile} gesetzt"

    def _paint_object(self, objects, cell, item):
        if self._stroke_changed and self._stroke_button is not None:
            return
        if not can_place_graphic_object(objects, cell, item):
            self.info = "Grafikobjekt passt hier nicht."
            return
        self._begin_stroke_change()
        place_graphic_object(objects, cell, item)
        if self.placement_mode == "combined":
            self.collisions[cell] = self.collision_type
            self.info = "Grafikobjekt gesetzt · Kollision nur am Ankerfeld"
        else:
            self.info = f"Grafikobjekt {item.width}×{item.height} gesetzt"

    def _paint_effect(self, cell, erase):
        existing = self.effects.get(cell, CellEffects())
        if self.placement_mode == "damage":
            updated = CellEffects(damage=None if erase else self.damage_brush, slow=existing.slow)
            label = "Schaden"
        else:
            updated = CellEffects(damage=existing.damage, slow=None if erase else self.slow_brush)
            label = "Slow"
        if updated == existing:
            return
        self._begin_stroke_change()
        if updated.damage is None and updated.slow is None:
            del self.effects[cell]
        else:
            self.effects[cell] = updated
        self.info = f"{label} entfernt" if erase else f"{label} gesetzt"

    def _begin_stroke_change(self):
        if self._stroke_button is None or not self._stroke_changed:
            self._store_undo()
            self._stroke_changed = True

    def _snapshot(self):
        return (_copy_map(self.map), self.collisions.copy(), self.effects.copy(), self.objects.copy(),
                self.roofs.copy(), self.roof_visibility)

    def _layers(self):
        return self.map, self.collisions, self.effects, self.objects, self.roofs, self.roof_visibility

    def _restore_layers(self, layers):
        self.map, self.collisions, self.effects, self.objects, self.roofs, self.roof_visibility = layers

    def _store_undo(self):
        self.undo_stack.append(self._snapshot())
        self.redo_stack.clear()

    def undo(self):
        self._stroke_button = None
        self._stop_object_move()
        if self.undo_stack:
            self.redo_stack.append(self._layers())
            self._restore_layers(self.undo_stack.pop())
            self.info = "Bearbeitung rückgängig gemacht"

    def redo(self):
        self._stroke_button = None
        self._stop_object_move()
        if self.redo_stack:
            self.undo_stack.append(self._layers())
            self._restore_layers(self.redo_stack.pop())
            self.info = "Bearbeitung wiederholt"

    def fill_middle(self):
        if self.graphic_layer != "ground":
            self.info = "Mittelfeld ist für einzelne Kacheln verfügbar."
            return
        if self.current_tile in self.tiles:
            self._store_undo()
            for row in self.map[1:-1]:
                row[1:-1] = [self.current_tile] * (GRID_WIDTH - 2)
            self.info = "Mittelfeld gefüllt"

    def set_border(self):
        if self.graphic_layer != "ground":
            self.info = "Rand ist für einzelne Kacheln verfügbar."
            return
        if self.current_tile in self.tiles:
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
        if self._dialog["kind"] in ("name", "effects", "roof_settings"):
            pygame.key.stop_text_input()
        elif self._dialog["kind"] == "tiles":
            self.tile_library.close()
        self.effect_settings = None
        self.roof_settings_editor = None
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
        elif kind == "effects":
            result = self.effect_settings.handle_event(event)
            if result is not None:
                self._dismiss_dialog()
                if result is not False:
                    self.damage_brush, self.slow_brush = result
                    self.info = "Effektwerte übernommen"
        elif kind == "roof_settings":
            result = self.roof_settings_editor.handle_event(event)
            if result is not None:
                self._dismiss_dialog()
                if result is not False and result != self.roof_visibility:
                    self._store_undo()
                    self.roof_visibility = result
                    self.info = "Dachwerte übernommen"

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

    def _draw_button(self, screen, label, rect, outline=None):
        pygame.draw.rect(screen, COLOR_BTN, rect)
        if outline is not None:
            pygame.draw.rect(screen, outline, rect, 2)
        self._draw_text(screen, label, (rect.x + 6, rect.y + 5))

    def _button_available(self, action):
        if self.playtest is not None:
            return action in (self.stop_playtest, self._toggle_collision_overlay, self._toggle_effect_overlay)
        return not self.preview_active or action == self.stop_sim

    def _tool_outline(self, label):
        if label == self.collision_type:
            return COLLISION_COLORS[label]
        if label == "Kollision ein/aus" and self.show_collisions:
            return COLOR_SELECT
        if label == "Effekte ein/aus" and self.show_effects:
            return COLOR_SELECT
        if label == "Objekt verschieben" and self._moving_objects:
            return COLOR_SELECT
        if label == "Auf Dachebene" and self._transferring_roof:
            return COLOR_SELECT
        if label == "Dachansicht" and self.show_roofs:
            return COLOR_SELECT
        if any(label == name and self.graphic_layer == layer for layer, name, _ in GRAPHIC_LAYERS):
            return COLOR_SELECT
        if (self.placement_mode, label) in EFFECT_TOOLS:
            return EFFECT_COLORS[self.placement_mode]
        if any(mode == self.placement_mode and label == name for mode, name, _, _ in PLACEMENT_TOOLS):
            return COLOR_SELECT
        return None

    def _draw_effect_legend(self, screen):
        x, y = TOOLBAR_W + 451, MAP_TOP - BTN_H + 3
        self._draw_text(screen, "Schaden", (x, y), EFFECT_COLORS["damage"])
        self._draw_text(screen, "Slow", (x + 70, y), EFFECT_COLORS["slow"])

    def draw(self, screen):
        if not self.active:
            return
        screen.fill(COLOR_BG)
        if self.dialog_open and self._dialog["kind"] == "tiles":
            self.tile_library.draw(screen, self.current_tile)
            return
        if not self.preview_active and self.playtest is None:
            self._draw_tiles(screen)
            classic = getattr(self.game, "classic_level_name", None) or "Standard"
            self._draw_text(screen, f"Nächster Classic-Start · {classic}", (WINDOW_WIDTH - 304, 54),
                            max_width=290)
        for label, rect, action in self.buttons:
            if self._button_available(action):
                self._draw_button(screen, label, rect, self._tool_outline(label))
        if self.show_effects and not self.preview_active:
            self._draw_effect_legend(screen)

        title = self._display_name() or "Neuer Entwurf"
        if self._legacy:
            title += " (Altformat)"
        elif self._saved_name is None:
            title += " (noch nicht gespeichert)"
        if self.dirty:
            title = f"* Ungespeichert · {title}"
        self._draw_text(screen, title, (TOOLBAR_W, 54), COLOR_SELECT if self.dirty else COLOR_TEXT)
        self._draw_map(screen)

        if self.playtest is not None:
            self.playtest.draw(screen, MAP_RECT)
            statuses = " | ".join(
                f"P{index}: {player.health} HP · "
                + (f"Tempo {player.speed_percent} %{f' · {player.blocked}' if player.blocked else ''}"
                   if player.health else "K. o.")
                for index, player in enumerate(self.playtest.players, start=1)
            )
            self._draw_text(screen, statuses, (TOOLBAR_W, WINDOW_HEIGHT - 20), COLOR_SELECT)
            hint = "Leveltest · Esc/F2 zurück"
        elif self.preview_active:
            hint = "Karten-Vorschau · Esc zurück"
        else:
            erase = ERASE_LABELS[self.placement_mode]
            hint = f"Links malen · Rechts löscht {erase} · Mausrad über Kacheln"
            if self.placement_mode == "damage":
                damage = self.damage_brush
                duration = "" if damage.duration is None else f" · Dauer {damage.duration:g} s"
                hint = f"Links {damage.amount} HP je {damage.interval:g} s{duration} · Rechts löscht Schaden"
            elif self.placement_mode == "slow":
                hint = f"Links Slow {self.slow_brush.percent} % · Rechts löscht Slow"
            elif self._moving_objects:
                hint = "Grafikobjekt und Ziel anklicken · Esc bricht ab"
            elif self._transferring_roof:
                hint = "Dach auf Objektebene anklicken · Esc bricht ab"
            elif self.placement_mode != "collision" and (item := self._selected_object()) is not None:
                hint = f"Objekt {item.width}×{item.height} · Links setzt · Rechts entfernt das ganze Objekt"
                if self.placement_mode == "combined":
                    hint += " · Kollision nur im Klickfeld"
            elif self.placement_mode == "graphics" and self.graphic_layer == "roof":
                hint = "Dach aus der Tile-Bibliothek wählen · Rechts entfernt das ganze Dach"
        self._draw_text(screen, hint, (TOOLBAR_W, WINDOW_HEIGHT - 39))
        if self.playtest is None:
            self._draw_text(screen, self.info, (TOOLBAR_W, WINDOW_HEIGHT - 20), COLOR_SELECT)
        if self.dialog_open:
            if self._dialog["kind"] == "world":
                self.world_tree.draw(screen)
            elif self._dialog["kind"] == "effects":
                self.effect_settings.draw(screen, self._draw_text, self._draw_button)
            elif self._dialog["kind"] == "roof_settings":
                self.roof_settings_editor.draw(screen, self._draw_text, self._draw_button)
            else:
                self._draw_dialog(screen)

    def _draw_tiles(self, screen):
        pygame.draw.rect(screen, COLOR_FAV, (TOOLBAR_W, 0, WINDOW_WIDTH - TOOLBAR_W, FAV_ROW_H))
        for index, key in enumerate(self.favorites):
            rect = self._favorite_rect(index)
            image = self.tiles.get(key)
            if image is None and key in self.frost_assets:
                if key not in self._frost_favorite_thumbnails:
                    original = load_frostage_image(key)
                    if original is not None:
                        size = original.get_rect().fit(rect).size
                        self._frost_favorite_thumbnails[key] = pygame.transform.smoothscale(
                            original, tuple(max(1, side) for side in size))
                image = self._frost_favorite_thumbnails.get(key)
            if image is not None:
                screen.blit(image, image.get_rect(center=rect.center))
            if key == self.current_tile:
                pygame.draw.rect(screen, COLOR_SELECT, rect, 2)

        self._draw_text(screen, "Kacheln", (10, SCROLL_TOP - 39))
        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(10, SCROLL_TOP - 20, TOOLBAR_W - 18, 20))
        asset = self.frost_assets.get(self.current_tile)
        selection = asset.name if asset else self.current_tile or "–"
        self._draw_text(screen, selection, (10, SCROLL_TOP - 20), COLOR_SELECT)
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
        if self._preview_background is not None:
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
        draw_graphic_objects(screen, MAP_RECT, self.objects)
        if self.playtest is None and (self.show_roofs or self.preview_active):
            draw_roof_objects(screen, MAP_RECT, self.roofs, self.roof_visibility)
        if not self.preview_active and self.playtest is None:
            for x in range(0, MAP_RECT.width, CELL_SIZE):
                pygame.draw.line(screen, COLOR_GRID, (MAP_RECT.x + x, MAP_RECT.y),
                                 (MAP_RECT.x + x, MAP_RECT.bottom - 1))
            for y in range(0, MAP_RECT.height, CELL_SIZE):
                pygame.draw.line(screen, COLOR_GRID, (MAP_RECT.x, MAP_RECT.y + y),
                                 (MAP_RECT.right - 1, MAP_RECT.y + y))
        pygame.draw.rect(screen, COLOR_FRAME, MAP_RECT, 2)
        if self.show_collisions and not self.preview_active:
            draw_collision_overlay(screen, MAP_RECT, self.collisions)
        if self.show_effects and not self.preview_active:
            draw_effect_overlay(screen, MAP_RECT, CELL_SIZE, self.effects)
        if not self.preview_active and self.playtest is None and not self.dialog_open:
            self._draw_object_preview(screen)

    def _draw_object_preview(self, screen):
        anchor = self._hover_cell
        if anchor is None:
            return
        objects = self._selected_layer_objects()
        moving = self._move_anchor
        if moving is not None:
            anchor = anchor[0] - self._move_offset[0], anchor[1] - self._move_offset[1]
            item = objects[moving]
        elif self._moving_objects or self._transferring_roof or self.placement_mode not in ("graphics", "combined"):
            return
        else:
            item = self._selected_object()
        if item is None:
            return
        rect = pygame.Rect(MAP_RECT.x + anchor[0] * CELL_SIZE, MAP_RECT.y + anchor[1] * CELL_SIZE,
                           item.width * CELL_SIZE, item.height * CELL_SIZE)
        fits = can_place_graphic_object(objects, anchor, item, moving=moving)
        if fits:
            draw_graphic_object(screen, MAP_RECT, anchor, item, preview=True)
        old_clip = screen.get_clip()
        screen.set_clip(MAP_RECT.clip(old_clip))
        pygame.draw.rect(screen, COLOR_SELECT if fits else (244, 104, 127), rect, 2)
        screen.set_clip(old_clip)

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
