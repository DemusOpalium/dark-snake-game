"""Exercise the sidebar against World Studio's existing level layers and tools."""

import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
if pygame.display.get_surface() is None:
    pygame.display.set_mode((1, 1))

from modules import resources
from modules.editor_buttons import load_editor_button_catalog
from modules.editor_sidebar import PANEL, StudioSidebar
from modules.game import Game
from modules.graphic_objects import GraphicObject
from modules.level_effects import CellEffects, DamageField, SlowField


@pytest.fixture
def studio(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    editor = Game(headless=True).level_editor
    return editor, StudioSidebar(pygame.font.SysFont("Arial", 16))


def _click(sidebar, editor, bounds, position):
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=position, button=1)
    return sidebar.handle_event(event, bounds, editor)


def _tab_center(sidebar, editor, bounds, key):
    tabs, _, _, _ = sidebar._geometry(bounds, editor)
    return next(rect.center for tab, _, rect in tabs if tab == key)


def _action_center(sidebar, editor, bounds, action_id):
    _, area, entries, max_scroll = sidebar._geometry(bounds, editor)
    rect, = [
        target for entry, _, _, rect in entries for control, target in sidebar._entry_targets(entry, rect)
        if control.action_id == action_id
    ]
    sidebar._scroll = max(0, min(max_scroll, rect.centery - area.height // 2))
    pos = rect.move(0, area.top - sidebar._scroll).center
    assert area.collidepoint(pos)
    return pos


def test_sidebar_switches_the_existing_layer_tool_and_keeps_map_data(studio):
    editor, sidebar = studio
    bounds = pygame.Rect(700, 80, 240, 500)
    editor.collisions[(4, 4)] = "WALL"
    assert _click(sidebar, editor, bounds, _tab_center(sidebar, editor, bounds, "layers"))
    assert sidebar.tab == "layers"
    for action in ("layer_visibility_roof", "layer_roof", "layer_visibility_collision"):
        assert _click(sidebar, editor, bounds, _action_center(sidebar, editor, bounds, action))
    assert editor.graphic_layer == "roof"
    assert not editor.show_roofs
    assert not editor.show_collisions
    assert editor.collisions == {(4, 4): "WALL"}
    assert not _click(sidebar, editor, bounds, (bounds.left - 1, bounds.top + 80))


def test_inspector_lists_roof_footprint_and_coextensive_effects(studio):
    editor, sidebar = studio
    editor.inspected_cell = (5, 4)
    editor.map[4][5] = "bone_corner_tl"
    editor.roofs[(4, 3)] = GraphicObject("frostage_roof_005", 5, 3)
    editor.collisions[(5, 4)] = "BARRIER"
    editor.effects[(5, 4)] = CellEffects(DamageField(16, 2.5), SlowField(50))
    sidebar.show("cell")
    entries = {entry.title: entry.detail for entry in sidebar._entries(editor)}
    assert "Zelle 5 / 4" in entries
    assert "5 × 3 · Anker 4 / 3" in entries["Dach"]
    assert entries["Objekt"] == "Leer"
    assert entries["Kollision"] == "BARRIER"
    assert entries["Schaden"] == "16 HP je 2,5 s · Keine Zeitgrenze"
    assert entries["Slow"] == "50 % langsamer"
    assert entries["Boden"] == "bone_corner_tl"


def test_inspector_updates_selected_collision_and_blocks_locked_controls(studio):
    editor, sidebar = studio
    bounds = pygame.Rect(708, 96, 192, 342)
    cell = editor.inspected_cell = (4, 3)
    editor.collisions[cell] = "WALL"
    sidebar.show("cell")
    editor.toggle_layer_lock("collision")
    switch = _action_center(sidebar, editor, bounds, "inspector_collision_barrier")
    assert _click(sidebar, editor, bounds, switch)
    assert editor.collisions[cell] == "WALL" and not editor.undo_stack
    editor.toggle_layer_lock("collision")
    assert _click(sidebar, editor, bounds, switch)
    assert editor.collisions[cell] == "BARRIER"
    editor.undo()
    assert editor.collisions[cell] == "WALL"


def test_layer_controls_restore_visibility_after_solo_and_leave_locks_alone(studio):
    editor, sidebar = studio
    bounds = pygame.Rect(708, 96, 192, 342)
    sidebar.show("layers")

    def click_layer(action_id):
        assert _click(sidebar, editor, bounds, _action_center(sidebar, editor, bounds, action_id))

    click_layer("layer_visibility_ground")
    click_layer("layer_lock_objects")
    click_layer("layer_solo_roof")
    assert editor.solo_layer == "roof" and not editor.layer_visible("objects")
    click_layer("layer_exit_solo")
    assert editor.solo_layer is None and editor.layer_visible("objects")
    assert not editor.layer_visible("ground")
    click_layer("layer_show_all")
    assert editor.layer_visible("ground")
    assert editor.layer_locked("objects") and not editor.undo_stack


def test_sidebar_draw_and_scroll_are_confined_to_its_panel(studio):
    editor, sidebar = studio
    bounds = pygame.Rect(75, 22, 204, 310)
    surface = pygame.Surface((330, 360))
    base = (212, 90, 16)
    surface.fill(base)
    sidebar.show("help")
    sidebar.draw(surface, bounds, editor)
    assert surface.get_at((bounds.right + 1, bounds.centery))[:3] == base
    assert surface.get_at((bounds.centerx, bounds.top + 27))[:3] == PANEL
    _, _, _, max_scroll = sidebar._geometry(bounds, editor)
    assert max_scroll > 0
    over_sidebar = pygame.event.Event(pygame.MOUSEWHEEL, y=-20, pos=bounds.center)
    assert sidebar.handle_event(over_sidebar, bounds, editor) and sidebar._scroll == max_scroll
    sidebar.show("properties")
    assert sidebar._scroll == 0


def test_sidebar_leaves_pointer_cleanup_to_the_editor(studio):
    editor, sidebar = studio
    bounds = pygame.Rect(75, 22, 204, 310)
    release = pygame.event.Event(pygame.MOUSEBUTTONUP, pos=bounds.center, button=1)
    motion = pygame.event.Event(pygame.MOUSEMOTION, pos=bounds.center)
    assert not sidebar.handle_event(release, bounds, editor)
    assert not sidebar.handle_event(motion, bounds, editor)


def test_drawn_layer_art_invokes_the_displayed_tools(studio, monkeypatch):
    editor, sidebar = studio
    surface = pygame.Surface((330, 490))
    bounds = pygame.Rect(108, 0, 204, 490)
    sidebar.show("layers")
    art = {}
    render = sidebar.button_art.draw

    def observe(screen, action_id, label, rect, **state):
        art[action_id] = (rect.copy(), state)
        render(screen, action_id, label, rect, **state)

    monkeypatch.setattr(sidebar.button_art, "draw", observe)
    sidebar.draw(surface, bounds, editor)
    tab_ids = {"sidebar_properties", "sidebar_layers", "sidebar_cell", "sidebar_help", "sidebar_learn"}
    assert tab_ids <= set(art) and tab_ids <= set(load_editor_button_catalog())
    for tab in ("properties", "help", "cell", "learn", "layers"):
        assert _click(sidebar, editor, bounds, art[f"sidebar_{tab}"][0].center)
        assert sidebar.tab == tab
    for layer in ("roof", "objects", "ground", "collision", "effects"):
        action = f"layer_{layer}"
        target = _action_center(sidebar, editor, bounds, action)
        sidebar.draw(surface, bounds, editor)
        assert art[action][0].center == target and action in load_editor_button_catalog()
        assert _click(sidebar, editor, bounds, target)
        assert editor.active_layer == layer
        sidebar.draw(surface, bounds, editor)
        assert art[action][1]["active"]
