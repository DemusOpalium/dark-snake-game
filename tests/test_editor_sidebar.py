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


def _action_center(sidebar, editor, bounds, label):
    _, area, entries, _ = sidebar._geometry(bounds, editor)
    rect, = [rect for entry, _, _, rect in entries if entry.title == label]
    return rect.move(0, area.top - sidebar._scroll).center


def test_sidebar_switches_the_existing_layer_tool_and_keeps_map_data(studio):
    editor, sidebar = studio
    bounds = pygame.Rect(700, 80, 240, 500)
    editor.collisions[(4, 4)] = "WALL"
    assert _click(sidebar, editor, bounds, (bounds.left + 36, bounds.top + 74))
    assert sidebar.tab == "layers"
    assert _click(sidebar, editor, bounds, _action_center(sidebar, editor, bounds, "Dach / Foreground"))
    assert editor.graphic_layer == "roof"
    assert _click(sidebar, editor, bounds, _action_center(sidebar, editor, bounds, "Kollisionsmarkierung · an"))
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
