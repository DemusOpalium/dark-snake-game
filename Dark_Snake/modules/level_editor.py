"""Tile-based editor for independent level drafts."""

from collections.abc import Callable
from dataclasses import dataclass, replace
import time

import pygame

from config import GRID_HEIGHT, GRID_WIDTH
from modules.border_builder_ui import BorderBuilderUI
from modules.editor_buttons import BUTTON_HEIGHT, MAX_ART_WIDTH, EditorButtons
from modules.editor_layout import MapCamera, StudioLayout
from modules.editor_layers import LAYER_COLORS, LAYER_LABELS, LayerView
from modules.editor_sidebar import StudioSidebar
from modules.effect_settings import EffectSettings, draw_effect_overlay
from modules.frostage_assets import frostage_assets
from modules.graphic_objects import (GraphicObject, can_place_graphic_object, draw_graphic_object,
                                     draw_graphic_objects, object_anchor_at, place_graphic_object)
from modules.graphics import TILE_IMAGES
from modules.level_drafts import (COLLISION_TYPES, LevelDocument, legacy_map_exists, list_drafts,
                                  load_level_document, normalize_draft_name, read_legacy_map,
                                  read_level_file, suggest_draft_name, write_draft)
from modules.level_effects import CellEffects, DamageField, SlowField
from modules.level_playtest import LevelPlaytest, draw_collision_overlay
from modules.resources import find_asset
from modules.roof_editor_settings import RoofSettingsEditor
from modules.roof_render import draw_roof_objects
from modules.roof_settings import RoofVisibility, is_roof_asset
from modules.studio_locale import StudioLocale
from modules.tile_library import TileLibrary

BTN_H = 30
MAX_FAV = 8
OPEN_ROWS = 8
OPEN_ROW_H = 27

COLOR_BG = (16, 21, 32)
COLOR_BTN = (29, 43, 62)
COLOR_FAV = (36, 52, 72)
COLOR_TEXT = (232, 240, 250)
COLOR_MUTED = (162, 180, 200)
COLOR_SELECT = (118, 214, 246)
COLOR_FRAME = (61, 87, 111)
COLOR_GRID = (47, 62, 79)
NAVIGATION = (
    ("nav_file", "Datei"), ("nav_build", "Bauen"), ("nav_layers", "Ebenen"),
    ("nav_effects", "Effekte"), ("nav_view", "Ansicht"), ("nav_test", "Testen"),
    ("nav_learn", "Lernen"), ("nav_help", "Hilfe"),
)

PLACEMENT_TOOLS = (
    ("graphics", "Nur Grafik", 96, "Grafik"),
    ("combined", "Grafik + Kollision", 142, "beide Ebenen"),
    ("collision", "Nur Kollision", 114, "Kollision"),
)
EFFECT_TOOLS = (("damage", "Schaden"), ("slow", "Slow"))
GRAPHIC_LAYERS = (("ground", "Boden", 70), ("objects", "Objekte", 74), ("roof", "Dach / Foreground", 151))
DOCUMENT_LAYERS = ("ground", "collision", "effects", "objects", "roof", "roof")
DELETE_COLOR = (248, 111, 122)

@dataclass(frozen=True, slots=True)
class EditorControl:
    id: str
    label: str
    rect: pygame.Rect
    action: Callable


@dataclass(frozen=True, slots=True)
class Deletion:
    layer: str
    cell: tuple[int, int]
    effect: str | None = None


def _empty_map():
    return [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]


def _copy_map(level_map):
    return [row.copy() for row in level_map]


class LevelEditor:
    def __init__(self, game):
        self.game = game
        self.tr = StudioLocale(game.settings.get("studio_language", "en"))
        self.active = False
        self.tiles = dict(sorted(TILE_IMAGES.items()))
        self.frost_assets = frostage_assets()
        self._scaled_tiles = {}
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
        self.layer_view = LayerView()
        self.eraser_active = False
        self.damage_brush = DamageField()
        self.slow_brush = SlowField()
        self.effect_settings = None
        self.roof_settings_editor = None
        self.border_builder = None
        self.playtest = None
        self.name = ""
        self._saved_name = None
        self._legacy = False
        self.undo_stack = []
        self.redo_stack = []
        self.favorites = []
        self._stroke_button = None
        self._stroke_changed = False
        self._pan_button = None
        self._space_held = False
        self.preview_active = False
        self._preview_background = None
        self._dialog_shade = None
        self._dialog = None
        self.tile_library = None
        self.world_tree = None
        self.font = pygame.font.SysFont("Segoe UI", 16)
        self.title_font = pygame.font.SysFont("Segoe UI", 19, bold=True)
        self.button_art = EditorButtons(self.font)
        self.layout = StudioLayout(game.screen.get_size())
        self.camera = MapCamera(self.layout.viewport)
        self.sidebar = StudioSidebar(self.font, self.button_art, translate=self.tr)
        self.section = "nav_build"
        self.show_library = self.show_inspector = True
        self.inspect_mode = False
        self.inspected_cell = None
        self.info = ""
        self._button_pointer = None
        self.resize(game.screen.get_size())

    @property
    def dirty(self):
        return self._layers() != self._saved_layers

    @property
    def dialog_open(self):
        return self._dialog is not None

    @property
    def library_search_focused(self):
        return self.tile_library is not None and self.tile_library.search_focused

    @property
    def active_layer(self):
        if self.placement_mode == "collision":
            return "collision"
        if self.placement_mode in ("damage", "slow"):
            return "effects"
        return self.graphic_layer

    @property
    def solo_layer(self):
        return self.layer_view.solo

    @property
    def show_collisions(self):
        return self._overlay_visible("collision")

    @property
    def show_effects(self):
        return self._overlay_visible("effects")

    @property
    def show_roofs(self):
        return self.layer_visible("roof")

    def layer_visible(self, layer):
        return self.layer_view.visible(layer)

    def _overlay_visible(self, layer):
        if self.playtest is not None:
            return layer not in self.layer_view.hidden
        return self.layer_visible(layer)

    def layer_locked(self, layer):
        return layer in self.layer_view.locked

    def layer_editable(self, layer):
        return self.layer_visible(layer) and not self.layer_locked(layer)

    def _toggle_language(self):
        self.tr.language = "de" if self.tr.language == "en" else "en"
        self.game.settings["studio_language"] = self.tr.language
        saved = self.game.save_settings()
        if self.tile_library is not None:
            self.tile_library.refresh_language()
        self._layout_controls()
        self.info = self.tr("Sprache · Deutsch" if saved else "Spracheinstellung konnte nicht gespeichert werden.")

    def _require_editable(self, *layers):
        for layer in layers:
            name = self.tr(LAYER_LABELS[layer])
            if self.layer_locked(layer):
                self.info = self.tr("{name} ist gesperrt.", name=name)
                return False
            if not self.layer_visible(layer):
                self.info = self.tr("{name} ist ausgeblendet.", name=name)
                return False
        return True

    def toggle_layer_visibility(self, layer):
        if self.solo_layer is not None:
            self.info = self.tr("Zuerst den Solo-Modus beenden, um einzelne Ebenen ein- oder auszublenden.")
            return
        self._stroke_button = None
        self.layer_view.hidden.symmetric_difference_update((layer,))
        message = "{name} ausgeblendet." if layer in self.layer_view.hidden else "{name} sichtbar."
        self.info = self.tr(message, name=self.tr(LAYER_LABELS[layer]))

    def toggle_layer_lock(self, layer):
        self._stroke_button = None
        self.layer_view.locked.symmetric_difference_update((layer,))
        message = "{name} gesperrt." if self.layer_locked(layer) else "{name} entsperrt."
        self.info = self.tr(message, name=self.tr(LAYER_LABELS[layer]))

    def toggle_layer_solo(self, layer):
        self._stroke_button = None
        current = self.solo_layer
        self.layer_view.solo = None if layer == current else layer
        self.info = (self.tr("Solo-Modus beendet.") if self.solo_layer is None
                     else f"Solo · {self.tr(LAYER_LABELS[layer])}")

    def show_all_layers(self):
        self._stroke_button = None
        self.layer_view.show_all()
        self.info = self.tr("Alle Ebenen sichtbar.")

    def toggle_eraser(self):
        self._stroke_button = None
        self._stop_object_move()
        self.inspect_mode = False
        self.eraser_active = not self.eraser_active
        self.info = (self.tr("Radierer an · {name}", name=self.tr(LAYER_LABELS[self.active_layer]))
                     if self.eraser_active else self.tr("Radierer aus."))

    def resize(self, size):
        self._layout_controls(size)
        self._reset_pointer()

    def _layout_controls(self, size=None):
        size = self.layout.bounds.size if size is None else size
        self.buttons, header_height = self._make_buttons(size[0])
        self.layout = StudioLayout(size, show_library=self.show_library, show_inspector=self.show_inspector,
                                   header_height=header_height)
        self.camera.set_viewport(self.layout.viewport)
        if self.tile_library is not None and self.show_library:
            self.tile_library.set_bounds(self.layout.library)
        for panel in (self.world_tree, self.effect_settings, self.roof_settings_editor):
            if panel is not None:
                panel.set_bounds(self.layout.bounds)
        if self.border_builder is not None:
            self.border_builder.set_bounds(self._border_bounds())

    def _set_section(self, section):
        self.section = section
        panel = {"nav_layers": "layers", "nav_effects": "properties",
                 "nav_learn": "learn", "nav_help": "help"}.get(section)
        if panel:
            self.sidebar.show(panel)
            if not self.show_inspector:
                self._toggle_sidebar("inspector")
                return
        self._layout_controls()

    def _toggle_sidebar(self, name):
        if name == "library":
            self.show_library = not self.show_library
            if not self.show_library and self.tile_library is not None:
                self.tile_library.blur_search()
        else:
            self.show_inspector = not self.show_inspector
        self.resize(self.layout.bounds.size)

    def toggle_inspect_mode(self):
        self.inspect_mode = not self.inspect_mode
        self._stroke_button = None
        if self.inspect_mode:
            self.eraser_active = False
            self._stop_object_move()
            self.sidebar.show("cell")
            if not self.show_inspector:
                self._toggle_sidebar("inspector")
        self.info = self.tr("Zelle anklicken, um ihre Ebenen zu lesen." if self.inspect_mode
                            else "Zellen-Auswahl beendet.")

    def _fit_map(self):
        self.camera.reset()
        self._reset_pointer()

    def _reset_pointer(self):
        self._stroke_button = self._pan_button = self._hover_cell = None
        self._space_held = False
        self._button_pointer = None

    def _make_buttons(self, window_width):
        buttons = []
        if self.border_builder is not None:
            return buttons, 54
        tool_width = 160 if window_width < 1440 else MAX_ART_WIDTH
        nav = tuple((key, label, lambda key=key: self._set_section(key)) for key, label in NAVIGATION)
        nav = (*nav, ("nav_language", "DE / EN", self._toggle_language))
        nav_width = max(110, min(140, (window_width - 178 - 6 * (len(nav) - 1)) // len(nav)))

        def rows(controls, x, y, *, navigation=False):
            height = 0
            for action_id, label, action in controls:
                label = self.tr(label)
                width, button_height = self.button_art.preferred_size(action_id, label)
                if navigation:
                    width, button_height = min(width, nav_width), 36
                else:
                    width = min(width, tool_width)
                width = min(width, max(1, window_width - 24))
                if x + width > window_width - 12 and x > 12:
                    x, y, height = 12, y + height + 5, 0
                buttons.append(EditorControl(action_id, label, pygame.Rect(x, y, width, button_height), action))
                height = max(height, button_height)
                x += width + 6
            return y + height

        tool_top = rows(nav, 166, 7, navigation=True) + 8
        if self.playtest is not None or self.preview_active:
            buttons[:] = [control for control in buttons if control.id == "nav_language"]
        if self.playtest is not None:
            controls = (("test_stop", "Test beenden", self.stop_playtest),
                        ("view_collision", "Kollision ein/aus", self._toggle_collision_overlay),
                        ("view_effects", "Effekte ein/aus", self._toggle_effect_overlay),
                        ("view_fit_map", "Karte einpassen", self._fit_map))
        elif self.preview_active:
            controls = (("preview_stop", "Vorschau beenden", self.stop_sim),
                        ("view_fit_map", "Karte einpassen", self._fit_map))
        else:
            controls = self._section_tools()
        tool_bottom = rows(controls, 12, tool_top)
        # Keep the map in place when switching tools, including on compact windows.
        per_row = max(1, (window_width - 18) // (tool_width + 6))
        tool_rows = (8 + per_row - 1) // per_row
        return buttons, max(tool_bottom, tool_top + tool_rows * (BUTTON_HEIGHT + 5) - 5) + 8

    def _section_tools(self):
        if self.section == "nav_file":
            return (("file_new", "Neu", self.new_map), ("file_open", "Öffnen", self.load_map),
                    ("file_save", "Speichern", self.save_map), ("file_worlds", "Welten", self.open_world_tree),
                    ("file_undo", "Undo", self.undo), ("file_redo", "Redo", self.redo),
                    ("file_use_classic", "Für Classic wählen", self.select_for_classic),
                    ("file_classic_default", "Classic-Standard", self.select_classic_default))
        if self.section == "nav_build":
            return (("build_border", "Rand", self.set_border), ("build_middle", "Mittelfeld", self.fill_middle),
                    ("build_move_objects", "Objekt verschieben", self._toggle_object_move),
                    ("build_object_size", "Objektgröße", self._open_object_size),
                    ("build_transfer_roof", "Auf Dachebene", self._toggle_roof_transfer),
                    ("build_tile_library", "Tile-Bibliothek", self.open_tile_library),
                    ("build_eraser", "Radierer", self.toggle_eraser))
        if self.section == "nav_layers":
            return (
                *((f"layer_{layer}", label, lambda layer=layer: self._set_graphic_layer(layer))
                  for layer, label, _ in GRAPHIC_LAYERS),
                *((("layer_collision" if mode == "collision" else f"tool_{mode}"), label,
                   lambda mode=mode: self._set_placement_mode(mode))
                  for mode, label, _, _ in PLACEMENT_TOOLS),
                *((f"collision_{kind.lower()}", kind, lambda kind=kind: self._set_collision_type(kind))
                  for kind in COLLISION_TYPES),
            )
        if self.section == "nav_effects":
            return (*((f"effect_{mode}", label, lambda mode=mode: self._set_placement_mode(mode))
                      for mode, label in EFFECT_TOOLS),
                    ("effect_values", "Effektwerte", self.open_effect_settings),
                    ("roof_settings", "Dachwerte", self.open_roof_settings))
        if self.section == "nav_view":
            return (("view_fit_map", "Karte einpassen", self._fit_map),
                    ("view_library", "Bibliothek ein/aus", lambda: self._toggle_sidebar("library")),
                    ("view_panel", "Panel ein/aus", lambda: self._toggle_sidebar("inspector")),
                    ("view_cell", "Zelle untersuchen", self.toggle_inspect_mode),
                    ("view_collision", "Kollision ein/aus", self._toggle_collision_overlay),
                    ("view_effects", "Effekte ein/aus", self._toggle_effect_overlay),
                    ("view_roof", "Dachansicht", self._toggle_roof_overlay))
        if self.section == "nav_test":
            return (("test_preview", "Vorschau starten", self.start_sim),
                    ("test_player_1", "Test 1P", lambda: self.start_playtest(1)),
                    ("test_player_2", "Test 2P", lambda: self.start_playtest(2)),
                    ("test_roof_demo", "Dach-Demo", self.load_roof_demo))
        return ()

    def _set_placement_mode(self, mode):
        if mode == "combined" and self.graphic_layer == "roof":
            self.info = self.tr("Dachebene und Kollision werden getrennt bearbeitet.")
            return
        self._stroke_button = None
        self.inspect_mode = False
        self.eraser_active = False
        self._stop_object_move()
        self.placement_mode = mode

    def _set_graphic_layer(self, layer):
        self._set_placement_mode("graphics")
        self.graphic_layer = layer

    def _set_collision_type(self, kind):
        self._stroke_button = None
        self.collision_type = kind

    def _toggle_collision_overlay(self):
        self.toggle_layer_visibility("collision")

    def _toggle_effect_overlay(self):
        self.toggle_layer_visibility("effects")

    def _toggle_roof_overlay(self):
        self.toggle_layer_visibility("roof")

    def open_effect_settings(self):
        self._blur_library()
        self._stroke_button = None
        self.effect_settings = EffectSettings(self.damage_brush, self.slow_brush, self.layout.bounds,
                                              translate=self.tr)
        self._dialog = {"kind": "effects"}
        pygame.key.start_text_input()

    def edit_inspected_effect(self, kind):
        cell = self.inspected_cell
        existing = self.effects.get(cell)
        if existing is None or getattr(existing, kind) is None or not self._require_editable("effects"):
            return
        self._blur_library()
        self._stroke_button = None
        self.effect_settings = EffectSettings(existing.damage or self.damage_brush, existing.slow or self.slow_brush,
                                              self.layout.bounds, kind=kind, translate=self.tr)
        self._dialog = {"kind": "effects", "cell": cell, "effect": kind}
        pygame.key.start_text_input()

    def edit_inspected_collision(self, kind):
        cell = self.inspected_cell
        if (cell in self.collisions and self.collisions[cell] != kind and kind in COLLISION_TYPES
                and self._require_editable("collision")):
            self._stroke_button = None
            self._store_undo()
            self.collisions[cell] = kind
            self.info = self.tr("Kollision auf {kind} geändert.", kind=kind)

    def select_inspected_object(self, layer):
        if self.inspected_cell is None or not self._require_editable(layer):
            return
        objects = self.roofs if layer == "roof" else self.objects
        anchor = object_anchor_at(objects, self.inspected_cell)
        if anchor is None:
            return
        self._set_graphic_layer(layer)
        self._moving_objects = True
        self._move_anchor = anchor
        self._move_offset = (0, 0)
        self.info = self.tr("Ziel anklicken oder Objektgröße öffnen.")

    def open_roof_settings(self):
        if not self._require_editable("roof"):
            return
        self._blur_library()
        self._stroke_button = None
        self._stop_object_move()
        self.roof_settings_editor = RoofSettingsEditor(
            self.roof_visibility, self.layout.bounds, translate=self.tr,
        )
        self._dialog = {"kind": "roof_settings"}
        pygame.key.start_text_input()

    def toggle(self):
        if self.active:
            self.request_close()
        else:
            self.active = True
            self.game._set_editor_window(True)
            self._ensure_library()
            if not self.name:
                self.name = self._suggest_name()
            self.info = self.tr("Editor geöffnet")

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
            self._reset_pointer()
            self._blur_library()
            self.active = False
            self.game._set_editor_window(False)
            if on_close is not None:
                on_close()
            return True

        return self._after_discard_confirmation(close)

    def _after_discard_confirmation(self, action):
        if self.dirty:
            self._blur_library()
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
            raise FileExistsError(self.tr("Ein Entwurf mit dem Namen {name} existiert bereits.", name=name))
        return name

    def new_map(self, name=None):
        if name is None:
            self._name_dialog("Neuer Entwurf", self._suggest_name(), self._new_named_map)
            return False
        try:
            return self._new_named_map(self._available_name(name))
        except (OSError, ValueError) as error:
            self.info = self.tr("Neuer Entwurf nicht möglich. {error}", error=self.tr(str(error)))
            return False

    def _new_named_map(self, name):
        def create():
            self._set_document(name, _empty_map())
            self.info = self.tr("Neuer Entwurf {name}", name=name)
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
        except FileExistsError:
            self.info = self.tr("Ein Entwurf mit dem Namen {name} existiert bereits.", name=name)
            if not replace:
                self._name_dialog("Unter einem neuen Namen speichern", self._suggest_name(),
                                  self._save_named_map)
            return False
        except (OSError, ValueError) as error:
            self.info = self.tr("Level konnte nicht gespeichert werden. {error}", error=self.tr(str(error)))
            return False
        self.name = self._saved_name = saved_name
        self._saved_layers = self._snapshot()
        self._legacy = False
        self.info = self.tr("{file}.json gespeichert", file=saved_name)
        return True

    def load_map(self, name=None):
        if name is None:
            try:
                names = list_drafts()
                if legacy_map_exists():
                    names.append(None)
            except OSError as error:
                self.info = self.tr("Entwürfe konnten nicht gelesen werden. {error}", error=self.tr(str(error)))
                return False
            if not names:
                self.info = self.tr("Keine gespeicherten Entwürfe vorhanden.")
                return False
            self._blur_library()
            self._stroke_button = None
            self._dialog = {"kind": "open", "names": names, "selected": 0}
            return False
        try:
            name = normalize_draft_name(name)
        except ValueError as error:
            self.info = self.tr("Level konnte nicht geladen werden. {error}", error=self.tr(str(error)))
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
                self.info = self.tr("Level konnte nicht geladen werden. {error}", error=self.tr(str(error)))
                return False
            self._set_document(name, document.graphics, collisions=document.collision,
                               effects=document.effects, objects=document.objects,
                               roofs=document.roofs, roof_visibility=document.roof_visibility,
                               saved_name=saved_name, legacy=legacy)
            self.info = self.tr(notice) if notice is not None else self.tr("{name} geladen", name=name)
            return True

        return self._after_discard_confirmation(load)

    def _set_document(self, name, level_map, *, collisions=None, effects=None, objects=None,
                      roofs=None, roof_visibility=None,
                      saved_name=None, legacy=False):
        self._stroke_button = None
        self._stop_object_move()
        self.inspected_cell = None
        self._hover_cell = None
        self.name = name
        self.map = level_map
        self.collisions = {} if collisions is None else collisions
        self.effects = {} if effects is None else effects
        self.objects = {} if objects is None else objects
        self.roofs = {} if roofs is None else roofs
        self.roof_visibility = RoofVisibility() if roof_visibility is None else roof_visibility
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
            self.world_tree = WorldTree(self.layout.bounds, self.font,
                                        self._open_world_draft, self._world_name_dialog, self._dismiss_dialog,
                                        translate=self.tr)
        try:
            self.world_tree.open(self._saved_name)
        except (OSError, ValueError) as error:
            self.info = self.tr("Weltbibliothek konnte nicht geladen werden. {error}", error=self.tr(str(error)))
            return
        self._stroke_button = None
        self._blur_library()
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

    def _ensure_library(self):
        if self.tile_library is None:
            self.tile_library = TileLibrary(
                self.tiles, self.favorites, self.layout.library, self.font, self._select_tile,
                max_favorites=MAX_FAV, frost_assets=self.frost_assets, embedded=True,
                translate=self.tr,
            )
            self.tile_library.open()

    def _blur_library(self):
        if self.tile_library is not None:
            self.tile_library.blur_search()

    def open_tile_library(self):
        if not self.show_library:
            self._toggle_sidebar("library")
        self._ensure_library()
        self.tile_library.focus_search()
        self._stroke_button = None

    def _select_tile(self, key):
        if self.border_builder is not None:
            if key in self.tiles:
                self.border_builder.select_tile(key)
            else:
                self.border_builder.reject_tile()
            return
        self.current_tile = key
        self.inspect_mode = False
        self.eraser_active = False
        self._object_brush = None
        self._stop_object_move()
        asset = self.frost_assets.get(key)
        if asset is None:
            self.graphic_layer = "ground"
            self.info = self.tr("{key}.png ausgewählt", key=key)
            return
        self._object_brush = GraphicObject(key, *asset.cells)
        self._set_graphic_layer("roof" if asset.category == "roof" else "objects")
        self.info = self.tr("{name} · {width}×{height} ausgewählt", name=asset.name,
                            width=asset.cells[0], height=asset.cells[1])

    def _open_object_size(self):
        anchor = self._move_anchor
        layer_objects = self._selected_layer_objects()
        item = layer_objects.get(anchor) if anchor is not None else self._selected_object()
        if item is None:
            self.info = self.tr("Zuerst eine FrostAge-Grafik aus der Bibliothek auswählen.")
            return
        layer = self.graphic_layer
        if anchor is not None and not self._require_editable(layer):
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
                if not self._require_editable(layer):
                    return
                if not can_place_graphic_object(layer_objects, anchor, updated, moving=anchor):
                    self.info = self.tr("Die Größe reicht aus der Karte oder über ein anderes Objekt.")
                    return
                self._store_undo()
                place_graphic_object(layer_objects, anchor, updated, moving=anchor)
            self.info = self.tr("Objektgröße {width}×{height}", width=updated.width, height=updated.height)

        self._name_dialog("Objektgröße im Raster, z. B. 4x4", f"{item.width}x{item.height}",
                          apply_size, validate=validate)

    def _stop_object_move(self):
        self._moving_objects = False
        self._transferring_roof = False
        self._move_anchor = None

    def _toggle_object_move(self):
        if self._moving_objects:
            self._stop_object_move()
            self.info = self.tr("Verschieben beendet")
        else:
            self._stroke_button = None
            self._stop_object_move()
            if self.graphic_layer == "ground":
                self._set_graphic_layer("objects")
            else:
                self._set_graphic_layer(self.graphic_layer)
            self._moving_objects = True
            if not self._require_editable(self.graphic_layer):
                return
            self.info = self.tr("Objekt der aktiven Ebene anklicken.")

    def _selected_layer_objects(self):
        return self.roofs if self.graphic_layer == "roof" else self.objects

    def _toggle_roof_transfer(self):
        if self._transferring_roof:
            self._stop_object_move()
            self.info = self.tr("Dachübertragung beendet")
            return
        self._set_graphic_layer("objects")
        self._transferring_roof = True
        if not self._require_editable("objects", "roof"):
            return
        self.info = self.tr("Ein vorhandenes Dach auf der Objektebene anklicken.")

    def _transfer_roof_at(self, cell):
        if not self._require_editable("objects", "roof"):
            return
        anchor = object_anchor_at(self.objects, cell)
        if anchor is None or not is_roof_asset(self.objects[anchor].asset_id):
            self.info = self.tr("Hier liegt kein FrostAge-Dach auf der Objektebene.")
            return
        item = self.objects[anchor]
        if not can_place_graphic_object(self.roofs, anchor, item):
            self.info = self.tr("Auf der Dachebene ist dieser Bereich bereits belegt.")
            return
        self._store_undo()
        self.roofs[anchor] = self.objects.pop(anchor)
        self._set_graphic_layer("roof")
        self.info = self.tr("Dach auf die Vordergrundebene verschoben")

    def _move_object_at(self, cell):
        if not self._require_editable(self.graphic_layer):
            return
        objects = self._selected_layer_objects()
        if self._move_anchor is None:
            anchor = object_anchor_at(objects, cell)
            if anchor is not None:
                self._move_anchor = anchor
                self._move_offset = cell[0] - anchor[0], cell[1] - anchor[1]
                self.info = self.tr("Zielposition anklicken · Esc bricht ab")
            return
        old = self._move_anchor
        target = cell[0] - self._move_offset[0], cell[1] - self._move_offset[1]
        item = objects[old]
        if not can_place_graphic_object(objects, target, item, moving=old):
            self.info = self.tr("Ziel liegt außerhalb der Karte oder über einem anderen Objekt.")
            return
        if target != old:
            self._store_undo()
            place_graphic_object(objects, target, item, moving=old)
            self.info = self.tr("Grafikobjekt verschoben")
        self._move_anchor = None

    def select_for_classic(self):
        if self.dirty or not (self._saved_name or self._legacy):
            self.info = self.tr("Bitte zuerst einen Entwurf speichern oder eine gespeicherte Karte öffnen.")
            return
        name = self._display_name()
        self.game.choose_classic_background(name, self.map, roof_objects=self.roofs,
                                            roof_visibility=self.roof_visibility)
        self.info = self.tr("{name} für den nächsten Classic-Start gewählt", name=name)

    def select_classic_default(self):
        self.game.choose_classic_background(None, None)
        self.info = self.tr("Standardhintergrund für den nächsten Classic-Start gewählt")

    def start_sim(self):
        self.preview_active = True
        self._stop_object_move()
        self._reset_pointer()
        self._blur_library()
        self._stroke_button = None
        self._layout_controls()
        self.info = self.tr("Visuelle Vorschau der Karte")

    def stop_sim(self):
        self.preview_active = False
        self._preview_background = None
        self._layout_controls()
        self.info = self.tr("Vorschau beendet")

    def start_playtest(self, player_count):
        try:
            session = LevelPlaytest(self.collisions, player_count, started_at=time.monotonic(), effects=self.effects,
                                    roof_objects=self.roofs, roof_visibility=self.roof_visibility)
        except ValueError as error:
            self.info = self.tr(str(error))
            return
        self.playtest = session
        self._stop_object_move()
        self._reset_pointer()
        self._blur_library()
        self._layout_controls()
        self.info = self.tr("Leveltest gestartet")

    def stop_playtest(self):
        self.playtest = None
        self._preview_background = None
        self._layout_controls()
        self.info = self.tr("Leveltest beendet · Entwurf unverändert")

    def handle_event(self, event, actions=()):
        if not self.active:
            return
        if event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWLEAVE):
            self._reset_pointer()
            if event.type == pygame.WINDOWFOCUSLOST:
                self._blur_library()
            return
        if self.dialog_open:
            self._handle_dialog(event)
            return
        if self._handle_map_navigation(event):
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button == self._stroke_button:
            self._stroke_button = None
            return
        if event.type == pygame.MOUSEMOTION:
            self._hover_cell = self._map_cell(event.pos)
            self._button_pointer = event.pos
        if self.playtest is not None:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_F2):
                self.stop_playtest()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos, event.button)
            else:
                self.playtest.apply_actions(actions)
        elif not self.preview_active and self._handle_sidebar_event(event):
            return
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos, event.button)
        elif event.type == pygame.MOUSEMOTION:
            if self._stroke_button:
                self._paint(*event.pos)

    def _handle_map_navigation(self, event):
        viewport = self.layout.viewport
        if event.type == pygame.MOUSEWHEEL:
            position = getattr(event, "pos", pygame.mouse.get_pos())
            if viewport.collidepoint(position):
                self._stroke_button = None
                self.camera.zoom_at(position, event.y)
                self._hover_cell = self._map_cell(position)
                return True
        if (self.playtest is None and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE
                and not self.library_search_focused):
            self._space_held = True
            return True
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            self._space_held = False
            if self._pan_button == 1:
                self._pan_button = None
            return True
        if (event.type == pygame.MOUSEBUTTONDOWN and (event.button == 2 or event.button == 1 and self._space_held)
                and viewport.collidepoint(event.pos)):
            self._blur_library()
            self._stroke_button = self._hover_cell = None
            self._pan_button = event.button
            return True
        if self._pan_button is not None:
            if event.type == pygame.MOUSEMOTION:
                self.camera.pan(*event.rel)
                return True
            if event.type == pygame.MOUSEBUTTONUP and event.button == self._pan_button:
                self._pan_button = None
                return True
        return False

    def _handle_sidebar_event(self, event):
        library = self.tile_library
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._stroke_button = None
            if not self.layout.library.collidepoint(event.pos):
                self._blur_library()
        if self.show_library and library is not None:
            if (event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL)
                    and self.layout.library.collidepoint(getattr(event, "pos", pygame.mouse.get_pos()))):
                library.handle_event(event)
                return True
            if self.library_search_focused and event.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
                if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    self._blur_library()
                else:
                    library.handle_event(event)
                return True
        return self.show_inspector and self.sidebar.handle_event(event, self.layout.inspector, self)

    def _handle_key(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.preview_active:
                self.stop_sim()
            elif self._moving_objects or self._transferring_roof:
                self._stop_object_move()
                self.info = self.tr("Objektwerkzeug beendet")
            elif self.inspect_mode:
                self.toggle_inspect_mode()
            elif self.eraser_active:
                self.toggle_eraser()
            else:
                self.request_close()
        elif not self.preview_active and getattr(event, "mod", 0) & pygame.KMOD_CTRL:
            shortcuts = {pygame.K_n: self.new_map, pygame.K_o: self.load_map,
                         pygame.K_s: self.save_map, pygame.K_z: self.undo, pygame.K_y: self.redo}
            action = shortcuts.get(event.key)
            if action:
                action()

    def _handle_click(self, pos, button):
        self._button_pointer = pos
        if button == 1:
            for control in self.buttons:
                if control.rect.collidepoint(pos):
                    if self._button_available(control.id):
                        control.action()
                    return
        if self.preview_active or self.playtest is not None or button not in (1, 3):
            return
        if (cell := self._map_cell(pos)) is not None:
            self._hover_cell = cell
            if button == 3:
                if not self.inspect_mode and not self._transferring_roof:
                    self._request_delete(self.active_layer, cell, self.placement_mode)
                return
            if button == 1:
                self.inspected_cell = cell
            if self.inspect_mode:
                return
            if self._transferring_roof:
                self._transfer_roof_at(cell)
                return
            if self._moving_objects:
                self._move_object_at(cell)
                return
            self._stroke_button = button
            self._stroke_changed = False
            self._paint(*pos)

    def _map_cell(self, position):
        return self.camera.cell_at(position)

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
        layer = self.active_layer
        if self.eraser_active:
            if self._require_editable(layer):
                deletion = self._deletion_at(layer, cell, self.placement_mode)
                if deletion is not None:
                    self._delete(deletion)
            return
        layers = (layer, "collision") if self.placement_mode == "combined" else (layer,)
        if not self._require_editable(*layers):
            return
        gx, gy = cell
        if layer == "effects":
            value = self.damage_brush if self.placement_mode == "damage" else self.slow_brush
            self._update_cell_effect(cell, self.placement_mode, value)
            return
        if layer in ("objects", "roof") and (item := self._selected_object()) is not None:
            self._paint_object(self._selected_layer_objects(), cell, item)
            return
        tile = self.current_tile if self.current_tile in self.tiles else None
        collision = self.collision_type
        change_graphics = layer == "ground" and tile is not None and self.map[gy][gx] != tile
        change_collision = "collision" in layers and self.collisions.get(cell) != collision
        if not (change_graphics or change_collision):
            return
        self._begin_stroke_change()
        if change_graphics:
            self.map[gy][gx] = tile
        if change_collision:
            self.collisions[cell] = collision
        if change_collision and change_graphics:
            self.info = self.tr("Kachel und {kind} gesetzt", kind=collision)
        elif change_collision:
            self.info = self.tr("{kind} gesetzt", kind=collision)
        else:
            self.info = self.tr("{tile} gesetzt", tile=tile)

    def _paint_object(self, objects, cell, item):
        if self._stroke_changed and self._stroke_button is not None:
            return
        if not can_place_graphic_object(objects, cell, item):
            self.info = self.tr("Grafikobjekt passt hier nicht.")
            return
        self._begin_stroke_change()
        place_graphic_object(objects, cell, item)
        if self.placement_mode == "combined":
            self.collisions[cell] = self.collision_type
            self.info = self.tr("Grafikobjekt gesetzt · Kollision nur am Ankerfeld")
        else:
            self.info = self.tr("Grafikobjekt {width}×{height} gesetzt", width=item.width, height=item.height)

    def _update_cell_effect(self, cell, kind, value):
        existing = self.effects.get(cell, CellEffects())
        updated = replace(existing, **{kind: value})
        if updated == existing:
            return
        self._begin_stroke_change()
        if updated.damage is None and updated.slow is None:
            del self.effects[cell]
        else:
            self.effects[cell] = updated
        label = "Schaden" if kind == "damage" else "Slow"
        self.info = self.tr("{label} entfernt" if value is None else "{label} gesetzt", label=self.tr(label))

    def _deletion_at(self, layer, cell, effect):
        x, y = cell
        if layer == "ground" and self.map[y][x] is not None:
            return Deletion(layer, cell)
        if layer == "collision" and cell in self.collisions:
            return Deletion(layer, cell)
        if (layer == "effects" and effect in ("damage", "slow") and cell in self.effects
                and getattr(self.effects[cell], effect) is not None):
            return Deletion(layer, cell, effect)
        if layer in ("objects", "roof"):
            objects = self.roofs if layer == "roof" else self.objects
            anchor = object_anchor_at(objects, cell)
            if anchor is not None:
                return Deletion(layer, anchor)
        return None

    def delete_inspected(self, layer, effect=None):
        if self.inspected_cell is not None:
            self._request_delete(layer, self.inspected_cell, effect)

    def _request_delete(self, layer, cell, effect):
        if not self._require_editable(layer):
            return
        deletion = self._deletion_at(layer, cell, effect)
        if deletion is not None:
            self._stroke_button = None
            self._blur_library()
            self._dialog = {"kind": "delete", "target": deletion}

    def _delete(self, target):
        if target.effect is not None:
            self._update_cell_effect(target.cell, target.effect, None)
            return
        self._begin_stroke_change()
        x, y = target.cell
        if target.layer == "ground":
            self.map[y][x] = None
        else:
            layer = {"objects": self.objects, "roof": self.roofs, "collision": self.collisions}[target.layer]
            del layer[target.cell]
            if self._move_anchor == target.cell and self.graphic_layer == target.layer:
                self._stop_object_move()
        self.info = self.tr("{name} · Element entfernt.", name=self.tr(LAYER_LABELS[target.layer]))

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
        self._apply_history(self.undo_stack, self.redo_stack, "Bearbeitung rückgängig gemacht")

    def redo(self):
        self._apply_history(self.redo_stack, self.undo_stack, "Bearbeitung wiederholt")

    def _apply_history(self, source, destination, message):
        self._stroke_button = None
        self._stop_object_move()
        if not source:
            return
        current = self._layers()
        changed = dict.fromkeys(layer for layer, before, after in zip(DOCUMENT_LAYERS, source[-1], current)
                                if before != after)
        if self._require_editable(*changed):
            destination.append(current)
            self._restore_layers(source.pop())
            self.info = self.tr(message)

    def fill_middle(self):
        if self.graphic_layer != "ground":
            self.info = self.tr("Mittelfeld ist für einzelne Kacheln verfügbar.")
            return
        if not self._require_editable("ground"):
            return
        if self.current_tile in self.tiles:
            self._store_undo()
            for row in self.map[1:-1]:
                row[1:-1] = [self.current_tile] * (GRID_WIDTH - 2)
            self.info = self.tr("Mittelfeld gefüllt")

    def set_border(self):
        if not self._require_editable("ground"):
            return
        self._reset_pointer()
        self._blur_library()
        self._stop_object_move()
        if not self.show_library:
            self._toggle_sidebar("library")
        self._ensure_library()
        tile = self.current_tile if self.current_tile in self.tiles else None
        self.border_builder = BorderBuilderUI(tile, self._border_bounds(), self.button_art, translate=self.tr)
        self._dialog = {"kind": "border"}
        self._layout_controls()

    def _border_bounds(self):
        return self.layout.viewport.union(self.layout.inspector) if self.show_inspector else self.layout.viewport

    def _handle_border_builder(self, event):
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL):
            position = getattr(event, "pos", pygame.mouse.get_pos())
            if self.layout.library.collidepoint(position):
                self.tile_library.handle_event(event)
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._blur_library()
        if self.library_search_focused and event.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self._blur_library()
            else:
                self.tile_library.handle_event(event)
            return
        result = self.border_builder.handle_event(event, self.map)
        if result == "apply":
            self._apply_border()
        elif result == "cancel":
            self._dismiss_dialog()
            self.info = self.tr("Rand-Builder abgebrochen")

    def _apply_border(self):
        if not self._require_editable("ground"):
            return
        changed = [cell for cell in self.border_builder.plan.preview(self.map) if cell.changed]
        if changed:
            self._store_undo()
            for cell in changed:
                self.map[cell.y][cell.x] = cell.tile
            self.info = self.tr("Rand gestaltet · {count} Bodenfelder geändert", count=len(changed))
        self._dismiss_dialog()

    def _name_dialog(self, title, text, submit, *, validate=None, cancel=None):
        self._blur_library()
        self._stroke_button = None
        self._dialog = {"kind": "name", "title": title, "text": text, "select_all": True, "submit": submit,
                        "validate": validate or self._available_name, "cancel": cancel}
        pygame.key.start_text_input()

    def _dismiss_dialog(self):
        if self.border_builder is not None:
            self._blur_library()
            self.border_builder = None
            self._layout_controls()
        if self._dialog["kind"] in ("name", "effects", "roof_settings"):
            pygame.key.stop_text_input()
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
        panel = pygame.Rect(0, 0, min(540, self.layout.bounds.width - 40), height)
        panel.center = self.layout.bounds.center
        if self._dialog["kind"] == "delete":
            target = self._deletion_rect(self._dialog["target"])
            if target is not None:
                visible_target = target.clip(self.layout.viewport)
                if panel.colliderect(visible_target):
                    bounds = self.layout.bounds.inflate(-40, -40)
                    if visible_target.top - bounds.top >= bounds.bottom - visible_target.bottom:
                        panel.bottom = visible_target.top - 8
                    else:
                        panel.top = visible_target.bottom + 8
                    panel.clamp_ip(bounds)
        return panel

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
        if kind == "border":
            self._handle_border_builder(event)
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cancel_dialog()
            return
        if kind == "name":
            self._handle_name(event)
        elif kind == "delete":
            self._handle_delete_dialog(event)
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
                    if "effect" not in dialog:
                        self.damage_brush, self.slow_brush = result
                        self.info = self.tr("Effektwerte übernommen")
                    elif self._require_editable("effects"):
                        effect = dialog["effect"]
                        self._update_cell_effect(dialog["cell"], effect, result[0 if effect == "damage" else 1])
        elif kind == "roof_settings":
            result = self.roof_settings_editor.handle_event(event)
            if result is not None:
                self._dismiss_dialog()
                if result is not False and result != self.roof_visibility and self._require_editable("roof"):
                    self._store_undo()
                    self.roof_visibility = result
                    self.info = self.tr("Dachwerte übernommen")

    def _handle_delete_dialog(self, event):
        target = self._dialog["target"]
        cancel, confirm = self._discard_buttons(self._dialog_panel())
        apply = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if cancel.collidepoint(event.pos):
                self._dismiss_dialog()
                return
            apply = confirm.collidepoint(event.pos)
        if apply:
            self._dismiss_dialog()
            if (self._require_editable(target.layer)
                    and self._deletion_at(target.layer, target.cell, target.effect) == target):
                self._delete(target)

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
        pygame.draw.rect(screen, COLOR_FAV if outline else COLOR_BTN, rect, border_radius=5)
        pygame.draw.rect(screen, outline or COLOR_FRAME, rect, 2 if outline else 1, border_radius=5)
        self._draw_text(screen, label, (rect.x + 8, rect.centery - self.font.get_height() // 2),
                        max_width=rect.width - 15)

    def _button_available(self, action_id):
        if action_id == "file_undo":
            return bool(self.undo_stack)
        if action_id == "file_redo":
            return bool(self.redo_stack)
        if action_id == "tool_combined":
            return self.graphic_layer != "roof"
        return True

    def _control_state(self, action_id):
        toggles = {
            "view_cell": self.inspect_mode, "view_library": self.show_library,
            "view_panel": self.show_inspector, "view_collision": self.show_collisions,
            "view_effects": self.show_effects, "view_roof": self.show_roofs,
            "build_move_objects": self._moving_objects, "build_transfer_roof": self._transferring_roof,
            "build_eraser": self.eraser_active,
        }
        mode = self.placement_mode
        layer = f"layer_{self.graphic_layer}" if mode in ("graphics", "combined") else None
        selected = {
            "graphics": "tool_graphics", "combined": "tool_combined", "collision": "layer_collision",
            "damage": "effect_damage", "slow": "effect_slow",
        }[mode]
        return {
            "active": action_id == self.section or toggles.get(action_id, False),
            "selected": action_id in (layer, selected, f"collision_{self.collision_type.lower()}"),
            "enabled": self._button_available(action_id),
        }

    def _hovered_control(self):
        if self._button_pointer is not None and not self.dialog_open:
            return next((control for control in self.buttons if control.rect.collidepoint(self._button_pointer)), None)
        return None

    def draw(self, screen):
        if not self.active:
            return
        screen.fill(COLOR_BG)
        pygame.draw.rect(screen, COLOR_BTN, self.layout.header)
        screen.blit(self.title_font.render("WORLD STUDIO", True, COLOR_TEXT), (12, 11))
        hovered = self._hovered_control()
        for control in self.buttons:
            self.button_art.draw(screen, control.id, control.label, control.rect,
                                 hovered=control is hovered, **self._control_state(control.id))
        if self.show_library:
            self.tile_library.draw(screen, self.current_tile)
        if self.show_inspector:
            self.sidebar.draw(screen, self.layout.inspector, self)
        self._draw_map(screen)
        self._draw_status(screen, hovered)
        if self.dialog_open:
            if self._dialog["kind"] == "border":
                self.border_builder.draw(screen, self.map, self.tiles, self._draw_text, self._draw_button)
                return
            if self._dialog_shade is None or self._dialog_shade.get_size() != screen.get_size():
                self._dialog_shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                self._dialog_shade.fill((6, 11, 18, 135))
            screen.blit(self._dialog_shade, (0, 0))
            if self._dialog["kind"] == "delete":
                self._draw_deletion_outline(screen, self._dialog["target"])
            if self._dialog["kind"] == "world":
                self.world_tree.draw(screen)
            elif self._dialog["kind"] == "effects":
                self.effect_settings.draw(screen, self._draw_text, self._draw_button)
            elif self._dialog["kind"] == "roof_settings":
                self.roof_settings_editor.draw(screen, self._draw_text, self._draw_button)
            else:
                self._draw_dialog(screen)

    def _draw_status(self, screen, hovered):
        status = self.layout.status
        pygame.draw.rect(screen, COLOR_BTN, status)
        pygame.draw.line(screen, COLOR_FRAME, status.topleft, (status.right, status.top))
        title = self._display_name() or self.tr("Neuer Entwurf")
        saved = self.tr("Ungespeichert" if self.dirty or self._saved_name is None else "Gespeichert")
        if self._legacy:
            saved += f" · {self.tr('Altformat')}"
        if self.playtest is not None:
            summary = " | ".join(
                self.tr("P{player} · {hp} HP · Tempo {speed} %", player=index,
                        hp=player.health, speed=player.speed_percent)
                + (f" · {player.blocked}" if player.blocked else "")
                for index, player in enumerate(self.playtest.players, start=1)
            )
            hint = "Leveltest · Esc oder F2 zurück"
        elif self.preview_active:
            summary, hint = title, "Kartenvorschau · Esc zurück"
        else:
            layer = self.tr(LAYER_LABELS[self.active_layer])
            if self.layer_locked(self.active_layer):
                layer += f" · {self.tr('gesperrt')}"
            if not self.layer_visible(self.active_layer):
                layer += f" · {self.tr('ausgeblendet')}"
            tools = {"graphics": "Grafik", "combined": "Grafik + Kollision", "collision": self.collision_type,
                     "damage": "Schaden", "slow": "Slow"}
            tool = tools[self.placement_mode]
            if self.eraser_active:
                tool = "Radierer"
            elif self.inspect_mode:
                tool = "Zellen-Auswahl"
            elif self._moving_objects:
                tool = "Verschieben"
            elif self._transferring_roof:
                tool = "Auf Dachebene"
            cell = self._hover_cell if self._hover_cell is not None else self.inspected_cell
            coordinates = f"X {cell[0]} / Y {cell[1]}" if cell is not None else "X – / Y –"
            asset = self.frost_assets.get(self.current_tile)
            selection = asset.name if asset else self.current_tile or "–"
            summary = f"{saved} · {title}    |    {layer} / {self.tr(tool)}    |    {coordinates}    |    {selection}"
            if self.eraser_active:
                hint = "Radierer aktiv · Links löscht auf der aktiven Ebene · Esc beendet"
            elif self.inspect_mode:
                hint = "Linksklick liest die Zelle · Esc beendet die Auswahl"
            elif self._moving_objects:
                hint = "Grafikobjekt und Ziel anklicken · Esc bricht ab"
            elif self._transferring_roof:
                hint = "Dach auf der Objektebene anklicken · Esc bricht ab"
            else:
                hint = "Links platziert · Rechts fragt vor dem Löschen · Mausrad zoomt"
        summary_color = (COLOR_TEXT if self.playtest is not None or self.preview_active
                         else LAYER_COLORS[self.active_layer])
        self._draw_text(screen, summary, (12, status.top + 4), summary_color, max_width=status.width - 24)
        message = self.info if not self.preview_active and self.playtest is None and self.info else self.tr(hint)
        if hovered is not None:
            if hovered.id == "nav_language":
                message = self.tr("Aktiv: Deutsch · Zu English wechseln")
            else:
                message = self.tr(self.button_art.hint(hovered.id, hovered.label))
            if not self._button_available(hovered.id):
                message = self.tr("{hint} · Derzeit nicht verfügbar", hint=message)
        self._draw_text(screen, message, (12, status.top + 25), COLOR_MUTED, max_width=status.width - 24)

    def _draw_map(self, screen):
        viewport, board, size = self.layout.viewport, self.camera.board_rect, self.camera.cell_size
        pygame.draw.rect(screen, (10, 14, 23), viewport)
        old_clip = screen.get_clip()
        screen.set_clip(old_clip.clip(viewport))
        if self.preview_active or self.playtest is not None:
            if self._preview_background is None or self._preview_background.get_size() != board.size:
                self._preview_background = pygame.transform.scale(self.game.default_background_surface, board.size)
            screen.blit(self._preview_background, board)
        else:
            pygame.draw.rect(screen, (25, 36, 52), board)
        authored_view = self.preview_active or self.playtest is not None
        if authored_view or self.layer_visible("ground"):
            for y, row in enumerate(self.map):
                for x, key in enumerate(row):
                    if key in self.tiles:
                        position = (board.x + x * size, board.y + y * size)
                        if not viewport.colliderect(pygame.Rect(position, (size, size))):
                            continue
                        screen.blit(self._tile_for_view(key, size), position)
        if authored_view or self.layer_visible("objects"):
            draw_graphic_objects(screen, board, self.objects)
        if self.playtest is None and (self.show_roofs or self.preview_active):
            draw_roof_objects(screen, board, self.roofs, self.roof_visibility)
        if not self.preview_active and self.playtest is None:
            for x in range(board.left, board.right, size):
                pygame.draw.line(screen, COLOR_GRID, (x, board.top), (x, board.bottom - 1))
            for y in range(board.top, board.bottom, size):
                pygame.draw.line(screen, COLOR_GRID, (board.left, y), (board.right - 1, y))
        pygame.draw.rect(screen, COLOR_FRAME, board, 2)
        if self.show_collisions and not self.preview_active:
            draw_collision_overlay(screen, board, self.collisions)
        if self.show_effects and not self.preview_active:
            draw_effect_overlay(screen, board, size, self.effects)
        if self.playtest is not None:
            self.playtest.draw(screen, board)
        elif self.inspect_mode and self.inspected_cell is not None:
            x, y = self.inspected_cell
            pygame.draw.rect(screen, COLOR_SELECT, (board.x + x * size, board.y + y * size, size, size), 2)
        elif not self.preview_active and not self.dialog_open and self.layer_editable(self.active_layer):
            if self.eraser_active and self._hover_cell is not None:
                target = self._deletion_at(self.active_layer, self._hover_cell, self.placement_mode)
                if target is not None:
                    self._draw_deletion_outline(screen, target)
            elif not self.eraser_active and (self.placement_mode != "combined" or self.layer_editable("collision")):
                self._draw_object_preview(screen)
        screen.set_clip(old_clip)
        pygame.draw.rect(screen, COLOR_FRAME, viewport, 1)

    def _tile_for_view(self, key, size):
        cached = self._scaled_tiles.get(key)
        if cached is None or cached.get_width() != size:
            cached = self._scaled_tiles[key] = pygame.transform.scale(self.tiles[key], (size, size))
        return cached

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
        board, size = self.camera.board_rect, self.camera.cell_size
        rect = pygame.Rect(board.x + anchor[0] * size, board.y + anchor[1] * size,
                           item.width * size, item.height * size)
        fits = can_place_graphic_object(objects, anchor, item, moving=moving)
        if fits:
            draw_graphic_object(screen, board, anchor, item, preview=True)
        pygame.draw.rect(screen, COLOR_SELECT if fits else DELETE_COLOR, rect, 2)

    def _deletion_rect(self, target):
        width = height = 1
        if target.layer in ("objects", "roof"):
            items = self.roofs if target.layer == "roof" else self.objects
            item = items.get(target.cell)
            if item is None:
                return
            width, height = item.width, item.height
        board, size = self.camera.board_rect, self.camera.cell_size
        x, y = target.cell
        return pygame.Rect(board.x + x * size, board.y + y * size, width * size, height * size)

    def _draw_deletion_outline(self, screen, target):
        rect = self._deletion_rect(target)
        if rect is None:
            return
        old_clip = screen.get_clip()
        screen.set_clip(old_clip.clip(self.layout.viewport))
        pygame.draw.rect(screen, DELETE_COLOR, rect, 2)
        screen.set_clip(old_clip)

    def _draw_dialog(self, screen):
        dialog = self._dialog
        panel = self._dialog_panel()
        pygame.draw.rect(screen, COLOR_BG, panel)
        pygame.draw.rect(screen, COLOR_SELECT, panel, 2)
        x, y = panel.x + 20, panel.y + 16
        if dialog["kind"] == "name":
            self._draw_text(screen, self.tr(dialog["title"]), (x, y))
            field = pygame.Rect(x, y + 29, panel.width - 40, BTN_H)
            pygame.draw.rect(screen, COLOR_FAV if dialog["select_all"] else COLOR_BTN, field)
            old_clip = screen.get_clip()
            screen.set_clip(field)
            self._draw_text(screen, dialog["text"], (field.x + 6, field.y + 5))
            screen.set_clip(old_clip)
            self._draw_text(screen, self.tr(dialog.get("error", "Name des Entwurfs")), (x, y + 66),
                            max_width=panel.width - 40)
            cancel, accept = self._discard_buttons(panel)
            self._draw_button(screen, self.tr("Abbrechen"), cancel)
            self._draw_button(screen, self.tr("Übernehmen"), accept)
        elif dialog["kind"] == "discard":
            self._draw_text(screen, self.tr("Ungespeicherte Änderungen verwerfen?"), (x, y))
            self._draw_text(screen, self.tr("Zum Speichern zuerst weiterbearbeiten."), (x, y + 33))
            keep, discard = self._discard_buttons(panel)
            self._draw_button(screen, self.tr("Weiter bearbeiten"), keep)
            self._draw_button(screen, self.tr("Verwerfen [V]"), discard)
        elif dialog["kind"] == "delete":
            target = dialog["target"]
            label = {"damage": "Schaden", "slow": "Slow"}.get(target.effect, LAYER_LABELS[target.layer])
            self._draw_text(screen, self.tr("Dieses Element löschen?"), (x, y), DELETE_COLOR)
            self._draw_text(screen, f"{self.tr(label)} · X {target.cell[0]} / Y {target.cell[1]}", (x, y + 32))
            if target.layer in ("objects", "roof"):
                self._draw_text(screen, self.tr("Das gesamte Grafikobjekt wird entfernt."), (x, y + 55))
            cancel, confirm = self._discard_buttons(panel)
            self._draw_button(screen, self.tr("Abbrechen"), cancel)
            self._draw_button(screen, self.tr("Löschen [Enter]"), confirm, DELETE_COLOR)
        else:
            self._draw_text(screen, self.tr("Entwurf öffnen"), (x, y))
            first = self._open_first()
            for index, name in enumerate(dialog["names"][first:first + OPEN_ROWS], start=first):
                rect = pygame.Rect(x, panel.y + 47 + (index - first) * OPEN_ROW_H,
                                   panel.width - 40, OPEN_ROW_H - 1)
                pygame.draw.rect(screen, COLOR_FAV if index == dialog["selected"] else COLOR_BTN, rect)
                label = f"{name}.json" if name is not None else self.tr("custom_level.json (Altformat)")
                self._draw_text(screen, label, (rect.x + 6, rect.y + 4), max_width=rect.width - 12)
            self._draw_text(screen, self.tr("↑ ↓ auswählen · Enter öffnen"), (x, panel.bottom - 31))
            self._draw_button(screen, self.tr("Abbrechen"), self._open_cancel_button(panel))
