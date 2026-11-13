import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

from config import GRID_HEIGHT, GRID_WIDTH
from modules import frostage_assets
from modules.graphic_objects import (
    GraphicObject,
    can_place_graphic_object,
    draw_graphic_object,
    draw_graphic_objects,
    object_anchor_at,
    place_graphic_object,
)


@pytest.fixture
def canvas():
    pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    cell_size = 24
    board = pygame.Rect(13, 19, GRID_WIDTH * cell_size, GRID_HEIGHT * cell_size)
    surface = pygame.Surface((board.right + 11, board.bottom + 7))
    surface.fill((19, 27, 33))
    return surface, board, cell_size


def test_object_selection_and_placement_use_the_whole_grid_footprint():
    objects = {}
    item = GraphicObject("frostage_test_4x4", 4, 4)
    edge = (GRID_WIDTH - 4, GRID_HEIGHT - 4)

    assert place_graphic_object(objects, edge, item)
    assert object_anchor_at(objects, (GRID_WIDTH - 1, GRID_HEIGHT - 1)) == edge
    assert object_anchor_at(objects, (edge[0] - 1, edge[1])) is None
    assert not place_graphic_object(objects, (edge[0] + 1, edge[1]), item)
    assert not place_graphic_object(objects, (-1, 0), item)
    assert not place_graphic_object(objects, (edge[0] - 2, edge[1] - 1), item)
    assert objects == {edge: item}

    adjacent = (edge[0] - 4, edge[1])
    assert place_graphic_object(objects, adjacent, item)
    assert object_anchor_at(objects, (edge[0] - 1, edge[1] + 3)) == adjacent


def test_moving_object_can_overlap_its_old_footprint_and_rejects_other_objects():
    moving = GraphicObject("frostage_test_landscape", 4, 2)
    blocker = GraphicObject("frostage_test_portrait", 1, 3)
    objects = {(3, 3): moving, (9, 3): blocker}
    original = objects.copy()

    assert not place_graphic_object(objects, (6, 3), moving, moving=(3, 3))
    assert not place_graphic_object(objects, (0, 0), moving, moving=(99, 99))
    assert not place_graphic_object(objects, (GRID_WIDTH - 1, 3), moving, moving=(3, 3))
    assert objects == original

    assert can_place_graphic_object(objects, (4, 3), moving, moving=(3, 3))
    assert place_graphic_object(objects, (4, 3), moving, moving=(3, 3))
    assert objects == {(4, 3): moving, (9, 3): blocker}
    assert object_anchor_at(objects, (3, 3)) is None
    assert object_anchor_at(objects, (7, 4)) == (4, 3)


@pytest.mark.parametrize(("filename", "cells", "pixels"), [
    ("FrostAge 10x1 (1).png", (1, 10), (297, 1119)),
    ("FrostAge 1x10 (1).png", (10, 1), (1895, 248)),
    ("FrostAge 4x4 (1).png", (4, 4), (971, 802)),
])
def test_frostage_art_keeps_its_native_proportions_inside_the_footprint(canvas, filename, cells, pixels):
    screen, board, size = canvas
    asset, = (asset for asset in frostage_assets.frostage_assets().values() if asset.name == filename)
    assert asset.cells == cells
    assert (asset.width, asset.height) == pixels

    anchor = (2, 3)
    item = GraphicObject(asset.id, *asset.cells)
    draw_graphic_objects(screen, board, {anchor: item})

    footprint = pygame.Rect(board.x + anchor[0] * size, board.y + anchor[1] * size,
                            cells[0] * size, cells[1] * size)
    background = pygame.Color(19, 27, 33)
    changed = [(x, y) for y in range(footprint.top, footprint.bottom)
               for x in range(footprint.left, footprint.right) if screen.get_at((x, y)) != background]
    assert changed
    x_coords, y_coords = zip(*changed)
    image_width = max(x_coords) - min(x_coords) + 1
    image_height = max(y_coords) - min(y_coords) + 1
    assert image_width / image_height == pytest.approx(pixels[0] / pixels[1], rel=0.03)
    assert (min(x_coords) + max(x_coords) + 1) / 2 == pytest.approx(footprint.centerx, abs=1)
    assert (min(y_coords) + max(y_coords) + 1) / 2 == pytest.approx(footprint.centery, abs=1)
    assert image_width < footprint.width or image_height < footprint.height
    assert screen.get_at((footprint.left - 1, footprint.centery)) == background
    assert screen.get_at((footprint.centerx, footprint.top - 1)) == background


def test_drawing_composites_source_alpha_and_preview_does_not_modify_normal_draw(canvas, monkeypatch):
    screen, board, size = canvas
    source = pygame.Surface((size, size), pygame.SRCALPHA)
    source.fill((230, 106, 50, 0))
    pygame.draw.rect(source, (230, 106, 50, 128), (8, 0, 8, size))
    pygame.draw.rect(source, (230, 106, 50, 255), (16, 0, 8, size))
    asset_id = "frostage_test_alpha"
    monkeypatch.setattr(frostage_assets, "load_frostage_image",
                        lambda key: source if key == asset_id else None)

    item = GraphicObject(asset_id, 1, 1)
    anchor = (2, 3)
    x, y = board.x + 2 * size, board.y + 3 * size
    transparent = (x + 3, y + 10)
    translucent = (x + 12, y + 10)
    solid = (x + 21, y + 10)

    draw_graphic_object(screen, board, anchor, item, preview=True)
    preview_red = screen.get_at(translucent).r

    screen.fill((19, 27, 33))
    draw_graphic_object(screen, board, anchor, item)
    assert screen.get_at(transparent) == (19, 27, 33, 255)
    assert screen.get_at(translucent)[:3] == pytest.approx((125, 67, 42), abs=1)
    assert screen.get_at(solid) == (230, 106, 50, 255)
    assert 19 < preview_red < screen.get_at(translucent).r
    assert source.get_at((12, 10)).a == 128


def test_missing_art_keeps_its_footprint_without_drawing(canvas):
    screen, board, _ = canvas
    item = GraphicObject("frostage_test_missing_asset", 2, 2)
    objects = {}
    assert place_graphic_object(objects, (5, 4), item)
    before = pygame.image.tobytes(screen, "RGB")
    draw_graphic_objects(screen, board, objects)
    assert pygame.image.tobytes(screen, "RGB") == before
    assert object_anchor_at(objects, (6, 5)) == (5, 4)
