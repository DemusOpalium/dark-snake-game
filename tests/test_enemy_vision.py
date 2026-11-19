"""Enemy Vision A: deterministic 1P/2P eyesight, occlusion and Classic bridge."""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE
from modules.enemy_vision import (
    VisionProfile, VisionSensor, can_see, has_line_of_sight, supercover_cells,
)
from modules.enemies import NormalEnemy
from modules.bolbu_enemy import BolbuEnemy
from modules.enums import GameState
from modules.game import Game
from modules import game as game_module


def test_cone_only_sees_forward_and_respects_boundaries():
    eye = VisionProfile(radius_cells=5, fov_degrees=90)
    assert can_see((8, 8), (1, 0), (13, 8), eye)
    assert can_see((8, 8), (1, 0), (11, 11), eye)  # on the diagonal edge
    assert not can_see((8, 8), (1, 0), (7, 8), eye)
    assert not can_see((8, 8), (1, 0), (8, 10), eye)
    assert not can_see((8, 8), (1, 0), (14, 8), eye)
    assert can_see((8, 8), (0, -1), (8, 4), eye)
    assert not can_see((8, 8), (0, 0), (10, 8), eye)
    assert can_see((8, 8), (0, 0), (8, 8), eye)


def test_full_circle_perception_and_diagonal_direction():
    omni = VisionProfile(radius_cells=6, fov_degrees=360)
    assert can_see((10, 10), (0, 0), (5, 10), omni)
    assert can_see((10, 10), (1, 0), (10, 15), omni)
    assert not can_see((10, 10), (1, 0), (17, 10), omni)
    diagonal = VisionProfile(radius_cells=5, fov_degrees=45)
    assert can_see((10, 10), (1, 1), (12, 12), diagonal)
    assert not can_see((10, 10), (1, 1), (12, 10), diagonal)


def test_supercover_does_not_allow_diagonal_peeking_through_wall_corners():
    visited = set(supercover_cells((1, 1), (4, 4)))
    assert {(1, 1), (2, 1), (1, 2), (2, 2), (4, 4)} <= visited
    assert has_line_of_sight((1, 1), (4, 4), frozenset())
    assert not has_line_of_sight((1, 1), (4, 4), {(1, 2)})
    assert not has_line_of_sight((1, 1), (4, 4), {(2, 1)})
    assert has_line_of_sight((1, 1), (4, 4), {(2, 0)})
    assert not has_line_of_sight((3, 5), (8, 5), {(5, 5)})
    assert has_line_of_sight((3, 5), (8, 5), {(3, 5)})
    assert has_line_of_sight((8, 5), (3, 5), frozenset())


@pytest.mark.parametrize("kwargs", [
    {"radius_cells": 0}, {"radius_cells": 101},
    {"fov_degrees": 0}, {"fov_degrees": 370},
    {"memory_seconds": -1}, {"memory_seconds": 61},
    {"scan_interval": 0}, {"scan_interval": 2.1},
])
def test_reject_impossible_sensor_profiles(kwargs):
    with pytest.raises(ValueError):
        VisionProfile(**kwargs)


def test_sensor_remembers_last_seen_cell_then_forgets_after_timeout():
    eye = VisionSensor(VisionProfile(
        radius_cells=6, fov_degrees=90, scan_interval=0.1, memory_seconds=1.0))
    observed = eye.observe((2, 2), (1, 0), [(1, (5, 2))], (), now=10)
    assert (observed.kind, observed.target_player,
            observed.last_known_cell) == ("VISIBLE", 1, (5, 2))
    observed = eye.observe((2, 2), (1, 0), [(1, (1, 2))], (), now=10.2)
    assert observed.kind == "SEARCHING"
    assert observed.last_known_cell == (5, 2)
    assert not observed.visible
    assert eye.observe((2, 2), (1, 0), [], (), now=11.21).kind == "UNAWARE"
    assert eye.result.target_player is None


def test_sensor_interval_throttles_rays_not_frames_and_keeps_reading_stable():
    eye = VisionSensor(VisionProfile(
        radius_cells=6, fov_degrees=360, scan_interval=0.2))
    first = eye.observe((1, 1), (1, 0), [(1, (4, 1))], (), now=20)
    assert first.visible
    # Same result until next scheduled sensor tick, even when a wall appears.
    again = eye.observe((1, 1), (1, 0), [(1, (4, 1))],
                        {(2, 1)}, now=20.1)
    assert again is first
    late = eye.observe((1, 1), (1, 0), [(1, (4, 1))],
                       {(2, 1)}, now=20.21)
    assert late.kind == "SEARCHING"
    eye.reset()
    assert eye.result.kind == "UNAWARE"


def test_2p_target_pick_is_nearest_and_tie_breaks_toward_player_1():
    sensor = VisionSensor(VisionProfile(fov_degrees=360))
    found = sensor.observe((5, 5), (1, 0), [(1, (9, 5)), (2, (6, 5))],
                           (), now=0)
    assert found.target_player == 2 and found.last_known_cell == (6, 5)
    sensor.reset()
    tied = sensor.observe((5, 5), (1, 0), [(2, (5, 6)), (1, (6, 5))],
                          (), now=5)
    assert tied.target_player == 1
    assert tied.last_known_cell == (6, 5)


def test_normal_enemy_and_bolbu_have_separate_interchangeable_sight_profiles():
    normal = NormalEnemy()
    bolbu = BolbuEnemy()
    assert normal.eyes.profile.fov_degrees < 360
    assert bolbu.eyes.profile.fov_degrees == 360
    assert normal.eyes.profile != bolbu.eyes.profile
    assert not normal.eyes.result.visible
    assert not bolbu.eyes.result.visible


def test_game_update_gives_classic_opponents_real_eyes_without_damage(monkeypatch):
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(1)
    game.snake = [(10, 5)]
    enemy = NormalEnemy()
    enemy.x, enemy.y = 5, 5
    enemy.facing = (1, 0)
    enemy.sprint_chance = 0
    enemy.last_move = time.time()
    game.enemies = [enemy]
    health, score, lives = game.player_health, game.score, game.lives
    game.last_update_time = time.time()  # No Snake raster turn.
    game.update()
    result = enemy.eyes.result
    assert result.visible
    assert result.target_player == 1
    assert result.last_known_cell == (10, 5)
    assert (game.player_health, game.score, game.lives) == (health, score, lives)

    game.game_state = GameState.PAUSE
    before = enemy.eyes.result
    game.update()
    assert enemy.eyes.result is before


def test_game_2p_sight_can_really_choose_second_snake(monkeypatch):
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(2)
    game.snake1, game.snake2 = [(10, 5)], [(6, 5)]
    enemy = NormalEnemy()
    enemy.x, enemy.y = 5, 5
    enemy.facing = (1, 0)
    enemy.sprint_chance = 0
    enemy.last_move = time.time()
    game.enemies = [enemy]
    game.last_update_time = time.time()
    game.update()
    assert enemy.eyes.result.target_player == 2
    assert enemy.eyes.result.last_known_cell == (6, 5)
    assert enemy.eyes.result.visible


def test_classic_editor_collision_only_occludes_sight_not_movement_rules():
    game = Game(headless=True)
    game.choose_classic_background("Sight Lab", None, collisions={
        (7, 5): "WALL", (8, 6): "BARRIER", (6, 5): "DECORATION",
    })
    game.start_game(1)
    assert game._vision_blockers == {(7, 5), (8, 6)}
    eye = VisionSensor(VisionProfile(radius_cells=6, fov_degrees=360))
    result = eye.observe((5, 5), (1, 0), [(1, (9, 5))],
                         game._vision_blockers, now=12)
    assert not result.visible
    game.choose_classic_background(None, None)
    game.start_game(1)
    assert game._vision_blockers == frozenset()


def test_debug_eye_range_and_last_seen_marker_draw_on_headless_surface():
    game = Game(headless=True)
    enemy = NormalEnemy()
    enemy.x, enemy.y = 5, 5
    enemy.facing = (1, 0)
    enemy.eyes.observe((5, 5), enemy.facing, [(1, (8, 5))], (), now=1)
    assert enemy.eyes.result.visible
    game.screen.fill((0, 0, 0))
    game._draw_enemy_sight_debug(enemy)
    target = (8 * GRID_SIZE + GRID_SIZE // 2, 5 * GRID_SIZE + GRID_SIZE // 2)
    assert game.screen.get_at(target)[:3] != (0, 0, 0)
