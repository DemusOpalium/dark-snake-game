"""Pixel regressions for the foreground pass shared by the game and playtest."""

import os
import sys
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

from config import GRID_HEIGHT, GRID_WIDTH
from modules import roof_render
from modules.graphic_objects import GraphicObject
from modules.roof_settings import RoofVisibility


CELL = 20
ROOF_COLOR = (226, 100, 36, 255)
WORLD_COLOR = (22, 100, 184)
ROOF_RECT = pygame.Rect(40, 40, 140, 120)
P1 = (90, 90)
P2 = (126, 90)


@pytest.fixture
def roof(monkeypatch):
    image = pygame.Surface(ROOF_RECT.size, pygame.SRCALPHA)
    image.fill(ROOF_COLOR)
    monkeypatch.setattr(roof_render, "graphic_object_art", lambda *args: (image, ROOF_RECT))
    return image


def render(*heads, settings=RoofVisibility(), transparent_world=False):
    board = pygame.Rect(0, 0, GRID_WIDTH * CELL, GRID_HEIGHT * CELL)
    screen = pygame.Surface(board.size, pygame.SRCALPHA if transparent_world else 0)
    if not transparent_world:
        screen.fill(WORLD_COLOR)
    objects = {(2, 2): GraphicObject("frostage_roof_001", 7, 6)}
    roof_render.draw_roof_objects(screen, board, objects, settings, head_centers=heads)
    return screen


def test_foreground_covers_world_without_window_and_does_not_extend_past_art(roof):
    screen = render()
    assert screen.get_at(P1)[:3] == ROOF_COLOR[:3]
    assert screen.get_at((39, 90))[:3] == WORLD_COLOR


def test_window_fades_radially_without_changing_pixels_outside_it(roof):
    screen = render(P1)
    x, y = P1
    center = screen.get_at((x, y)).r
    inner = screen.get_at((x + 16, y)).r
    edge = screen.get_at((x + 30, y)).r
    outside = screen.get_at((x + 40, y)).r
    assert WORLD_COLOR[0] < center == inner < edge < outside == ROOF_COLOR[0]
    assert screen.get_at((x, y + 30)).r == edge
    assert screen.get_at((x + 30, y + 30)).r == ROOF_COLOR[0]
    assert roof.get_at((x - ROOF_RECT.x, y - ROOF_RECT.y)) == ROOF_COLOR


@pytest.mark.parametrize(
    "settings",
    [replace(RoofVisibility(), enabled=False), replace(RoofVisibility(), transparency=0)],
)
def test_disabled_or_zero_strength_window_keeps_roof_opaque(roof, settings):
    assert render(P1, settings=settings).get_at(P1)[:3] == ROOF_COLOR[:3]


def test_hard_transition_and_full_strength_at_custom_radius(roof):
    settings = replace(RoofVisibility(), radius=1.5, transparency=100, softness=0)
    screen = render(P1, settings=settings)
    assert screen.get_at((P1[0] + 29, P1[1]))[:3] == WORLD_COLOR
    assert screen.get_at((P1[0] + 30, P1[1]))[:3] == ROOF_COLOR[:3]


def test_two_heads_make_independent_windows_with_no_stacking(roof):
    both = render(P1, P2)
    first = render(P1)
    second = render(P2)
    for position in (P1, P2, (104, 90), (112, 104), (168, 90)):
        assert both.get_at(position).r == min(first.get_at(position).r, second.get_at(position).r)
    assert both.get_at(P1).r < second.get_at(P1).r
    assert both.get_at(P2).r < first.get_at(P2).r


def test_head_outside_drawn_art_does_not_open_a_window(roof, monkeypatch):
    # Head and its radius reach the roof footprint, but the head is in fit padding.
    def unexpected_mask(*args):
        pytest.fail("A mask should only be built for a head inside roof art.")

    monkeypatch.setattr(roof_render, "_window_mask", unexpected_mask)
    screen = render((80, 39))
    assert screen.get_at((80, 40))[:3] == ROOF_COLOR[:3]


def test_window_preserves_source_alpha_and_can_open_from_a_transparent_gap(roof):
    x, y = P1[0] - ROOF_RECT.x, P1[1] - ROOF_RECT.y
    roof.set_at((x, y), (0, 0, 0, 0))
    roof.set_at((x + 1, y), (*ROOF_COLOR[:3], 120))
    original = render(transparent_world=True)
    masked = render(P1, transparent_world=True)
    neighbor = (P1[0] + 1, P1[1])
    assert original.get_at(P1).a == masked.get_at(P1).a == 0
    assert original.get_at(neighbor).a == 120
    assert masked.get_at(neighbor).a == pytest.approx(30, abs=1)
