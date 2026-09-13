import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

import modules.game as game_module
from config import GRID_SIZE
from modules.game import Game


FLOAT_TOLERANCE = 1e-9


def assert_positions(actual, expected):
    """Compare each pixel axis without masking meaningful movement errors."""
    assert len(actual) == len(expected)
    for (actual_x, actual_y), (expected_x, expected_y) in zip(actual, expected):
        assert actual_x == pytest.approx(expected_x, abs=FLOAT_TOLERANCE)
        assert actual_y == pytest.approx(expected_y, abs=FLOAT_TOLERANCE)


def assert_between_cells(position, start, target, grid_size=GRID_SIZE):
    """The renderer may only occupy the segment between confirmed cells."""
    for value, start_axis, target_axis in zip(position, start, target):
        lower = min(start_axis, target_axis) * grid_size
        upper = max(start_axis, target_axis) * grid_size
        assert lower - FLOAT_TOLERANCE <= value <= upper + FLOAT_TOLERANCE


def interpolation_game(players=1):
    game = Game(headless=True)
    game.start_game(players)
    game.speed = 5
    game.last_update_time = 10
    return game


def test_normal_movement_interpolates_previous_to_current_cell():
    game = interpolation_game()
    game.previous_snake = [(5, 5), (4, 5)]
    game.snake = [(6, 5), (5, 5)]
    positions = game.get_snake_render_positions(now=10.1)
    assert_positions(positions, [(5.5 * GRID_SIZE, 5 * GRID_SIZE),
                                 (4.5 * GRID_SIZE, 5 * GRID_SIZE)])
    assert positions[0][0] - positions[1][0] == pytest.approx(
        GRID_SIZE, abs=FLOAT_TOLERANCE)
    assert_between_cells(positions[0], (5, 5), (6, 5))


def test_direction_change_uses_only_confirmed_corner_positions():
    game = interpolation_game()
    game.previous_snake = [(5, 5), (4, 5)]
    game.snake = [(5, 4), (5, 5)]
    positions = game.get_snake_render_positions(now=10.1)
    assert_positions(positions, [
        (5 * GRID_SIZE, 4.5 * GRID_SIZE),
        (4.5 * GRID_SIZE, 5 * GRID_SIZE),
    ])
    assert_between_cells(positions[0], (5, 5), (5, 4))


def test_two_players_have_independent_interpolation_history():
    game = interpolation_game(2)
    game.previous_snake1, game.snake1 = [(1, 1)], [(2, 1)]
    game.previous_snake2, game.snake2 = [(8, 8)], [(8, 7)]
    p1_positions = game.get_snake_render_positions(1, now=10.1)
    p2_positions = game.get_snake_render_positions(2, now=10.1)
    assert_positions(p1_positions, [(1.5 * GRID_SIZE, GRID_SIZE)])
    assert_positions(p2_positions, [(8 * GRID_SIZE, 7.5 * GRID_SIZE)])
    assert_between_cells(p1_positions[0], (1, 1), (2, 1))
    assert_between_cells(p2_positions[0], (8, 8), (8, 7))


def test_gameplay_collision_stays_on_current_grid_position_during_render_move():
    game = interpolation_game()
    game.previous_snake, game.snake = [(4, 5)], [(5, 5)]
    game.boss = SimpleNamespace(
        get_rect=lambda: pygame.Rect(5 * GRID_SIZE, 5 * GRID_SIZE,
                                     GRID_SIZE, GRID_SIZE))
    assert game.get_snake_render_positions(now=10.05)[0][0] < 5 * GRID_SIZE
    assert game.check_boss_collision(game.snake[0])


def test_start_and_restart_reset_visual_history():
    game = interpolation_game()
    assert game.previous_snake == game.snake
    game.previous_snake = [(0, 0)]
    game.start_game(1)
    assert game.previous_snake == game.snake
    assert_positions(game.get_snake_render_positions(now=game.last_update_time), [
        (game.snake[0][0] * GRID_SIZE, game.snake[0][1] * GRID_SIZE)])


def test_render_interpolation_scales_with_view_grid_size(monkeypatch):
    game = interpolation_game()
    game.previous_snake, game.snake = [(1, 1)], [(2, 1)]
    for grid_size in (20, 30, 40):  # VIEW_SCALE 1.0, 1.5 und 2.0
        monkeypatch.setattr(game_module, "GRID_SIZE", grid_size)
        positions = game.get_snake_render_positions(now=10.1)
        assert_positions(positions, [(1.5 * grid_size, grid_size)])
        assert_between_cells(positions[0], (1, 1), (2, 1), grid_size)
