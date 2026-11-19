"""Enemy Vision D: faster detection and pursuit only behind the KI-Test toggle."""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules.enemies import NormalEnemy
from modules.bolbu_enemy import BolbuEnemy
from modules.enemy_vision import VisionResult, VisionSensor, can_see


def test_fast_classic_hunter_profile_is_fixed_and_bolbu_stays_different():
    profile = NormalEnemy.AI_SIGHT_PROFILE
    assert profile.radius_cells == 8
    assert profile.alert_radius_cells == 16
    assert profile.fov_degrees == 150
    assert profile.reaction_seconds == pytest.approx(.05)
    assert profile.scan_interval == pytest.approx(.05)
    assert profile.memory_seconds == 4
    assert NormalEnemy.AI_MOVEMENT_SPEED == pytest.approx(1.8)
    assert (NormalEnemy.AI_MOVEMENT_SPEED
            * NormalEnemy.BEHAVIOR_PROFILE.chase_speed) == pytest.approx(3.6)
    # Bolbu deliberately remains a slow 360-degree guard during this trial.
    assert BolbuEnemy.AI_MOVEMENT_SPEED < NormalEnemy.AI_MOVEMENT_SPEED
    assert BolbuEnemy.AI_SIGHT_PROFILE.fov_degrees == 360
    assert BolbuEnemy.AI_SIGHT_PROFILE.reaction_seconds > profile.reaction_seconds


def test_50ms_observation_recognizes_a_head_before_it_crosses_eight_cells():
    eyes = VisionSensor(NormalEnemy.AI_SIGHT_PROFILE)
    origin = (5, 5)
    target = [(1, (12, 5))]  # 7 cells, outside previous 5-cell range.
    assert eyes.observe(origin, (1, 0), target, (), now=0).kind == "UNAWARE"
    assert eyes.observe(origin, (1, 0), target, (), now=.03).kind == "UNAWARE"
    reading = eyes.observe(origin, (1, 0), target, (), now=.06)
    assert reading.visible
    assert reading.last_known_cell == (12, 5)
    assert reading.target_player == 1


def test_150_degree_cone_sees_more_than_old_classic_but_not_behind():
    profile = NormalEnemy.AI_SIGHT_PROFILE
    assert can_see((10, 10), (1, 0), (12, 14), profile)
    assert not can_see((10, 10), (1, 0), (8, 10), profile)
    assert not can_see((10, 10), (1, 0), (10, 15), profile)
    assert can_see((10, 10), (1, 0), (17, 10), profile)
    assert not can_see((10, 10), (1, 0), (19, 10), profile)


def test_alert_sight_persists_at_sixteen_cells_and_still_obeys_walls():
    eyes = VisionSensor(NormalEnemy.AI_SIGHT_PROFILE)
    assert not eyes.observe((5, 5), (1, 0), [(1, (10, 5))], (),
                            now=0).visible
    assert eyes.observe((5, 5), (1, 0), [(1, (10, 5))], (),
                        now=.06).visible
    # 15 cells away: beyond detection radius, inside alert radius.
    assert eyes.observe((5, 5), (1, 0), [(1, (20, 5))], (),
                        now=.12).visible
    # No vision through solid walls, even at the expanded range.
    lost = eyes.observe((5, 5), (1, 0), [(1, (20, 5))],
                        {(12, 5)}, now=.18)
    assert lost.kind == "SEARCHING"
    assert lost.last_known_cell == (20, 5)


def test_ki_on_has_fixed_fast_pursuit_even_if_classic_random_speed_was_slow(monkeypatch):
    from modules import enemies

    now = [100.]
    monkeypatch.setattr(enemies.time, "time", lambda: now[0])
    enemy = NormalEnemy()
    enemy.speed = .5  # Classic's slowest random base value.
    enemy.x, enemy.y = 5, 5
    enemy._render_start = enemy._render_target = (5, 5)
    enemy.last_move = now[0]
    enemy.sprint_chance = 0
    enemy.set_ai_preview(True)
    enemy.eyes.result = VisionResult("VISIBLE", 1, (12, 5), now[0])
    enemy.update()
    assert enemy.behavior_state == "CHASE"
    assert (enemy.x, enemy.y) == (5, 5)

    # 3.6 grid steps/s means one step after ~278ms.
    now[0] += .29
    enemy.update()
    assert (enemy.x, enemy.y) == (6, 5)
    assert enemy.speed == .5  # Do NOT alter legacy properties.
    assert enemy._render_target == (6, 5)
    assert enemy.get_hitbox() == enemy.get_render_rect()

    # Disabling KI-Test immediately restores normal Classic speed.
    enemy.set_ai_preview(False)
    assert enemy.eyes.profile == NormalEnemy.SIGHT_PROFILE
    assert enemy.behavior_state == "PATROL"
    enemy.last_move = now[0]
    monkeypatch.setattr(enemies.random, "random", lambda: 1.0)
    monkeypatch.setattr(enemies.random, "choice", lambda options: 0)
    now[0] += .31
    enemy.update()
    assert (enemy.x, enemy.y) == (6, 5)
    # Slow Classic: 0.5 steps/sec, so not enough time to move.


def test_bolbu_inherits_tunable_speed_without_touching_projectile_rules():
    from modules.bolbu_enemy import BolbuEnemy
    guard = BolbuEnemy()
    assert guard.AI_MOVEMENT_SPEED == pytest.approx(1.1)
    assert guard.BEHAVIOR_PROFILE.visible_action == "GUARD"
    assert guard.SHOOT_COOLDOWN > 0
    guard.set_ai_preview(True)
    assert guard.eyes.profile == BolbuEnemy.AI_SIGHT_PROFILE
    guard.set_ai_preview(False)
    assert guard.eyes.profile == BolbuEnemy.SIGHT_PROFILE
