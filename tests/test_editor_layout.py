"""World Studio view coordinates are independent of the level grid."""

import sys
from pathlib import Path

import pygame
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

from config import GRID_HEIGHT, GRID_WIDTH
from modules.editor_layout import MIN_STUDIO_SIZE, MapCamera, StudioLayout


@pytest.mark.parametrize("size", [MIN_STUDIO_SIZE, (1350, 930), (1920, 1080)])
def test_studio_regions_do_not_overlap_and_panels_can_collapse(size):
    layout = StudioLayout(size)
    regions = (layout.header, layout.library, layout.viewport, layout.inspector, layout.status)
    for index, region in enumerate(regions):
        assert layout.bounds.contains(region)
        assert region.width > 0 and region.height > 0
        assert not any(region.colliderect(other) for other in regions[index + 1:])

    compact = StudioLayout(size, show_library=False, show_inspector=False)
    assert compact.library.width == compact.inspector.width == 0
    assert compact.viewport.left < layout.viewport.left < layout.viewport.right < compact.viewport.right
    assert compact.viewport.height == layout.viewport.height


def test_fit_mapping_uses_integer_grid_cells_and_excludes_gutters_and_edges():
    viewport = pygame.Rect(245, 96, 801, 620)
    camera = MapCamera(viewport)
    board = camera.board_rect
    assert viewport.contains(board)
    assert board.width == camera.cell_size * GRID_WIDTH
    assert board.height == camera.cell_size * GRID_HEIGHT
    assert camera.cell_at(board.topleft) == (0, 0)
    assert camera.cell_at((board.right - 1, board.bottom - 1)) == (GRID_WIDTH - 1, GRID_HEIGHT - 1)
    assert camera.cell_at((board.right, board.bottom - 1)) is None
    assert camera.cell_at(viewport.topleft) is None


def test_zoom_preserves_pointer_cell_and_pan_can_reach_level_edges():
    viewport = pygame.Rect(245, 96, 800, 620)
    camera = MapCamera(viewport)
    focus = (viewport.centerx + 82, viewport.centery - 32)
    cell = camera.cell_at(focus)
    assert camera.zoom_at(focus, 1)
    assert camera.cell_at(focus) == cell
    assert not camera.zoom_at((viewport.right, viewport.centery), 1)
    assert camera.pan(10000, 10000)
    assert camera.cell_at(viewport.topleft) == (0, 0)
    assert not camera.pan(10000, 10000)
    assert camera.pan(-10000, -10000)
    assert camera.cell_at((viewport.right - 1, viewport.bottom - 1)) == (GRID_WIDTH - 1, GRID_HEIGHT - 1)
    assert camera.board_rect.collidepoint(viewport.left - 1, viewport.centery)
    assert camera.cell_at((viewport.left - 1, viewport.centery)) is None


def test_resize_refits_overview_and_preserves_center_cell_when_zoomed():
    original = StudioLayout((1350, 930))
    larger = StudioLayout((1920, 1080))
    camera = MapCamera(original.viewport)
    fit = camera.cell_size
    camera.set_viewport(larger.viewport)
    assert camera.cell_size > fit
    assert larger.viewport.contains(camera.board_rect)

    assert camera.zoom_at(larger.viewport.center, 4)
    assert camera.pan(132, -107)
    focus = camera.cell_at(larger.viewport.center)
    zoomed = camera.cell_size
    camera.set_viewport(original.viewport)
    assert camera.cell_size == zoomed
    assert camera.cell_at(original.viewport.center) == focus
    camera.reset()
    assert camera.cell_size == fit
    assert original.viewport.contains(camera.board_rect)
