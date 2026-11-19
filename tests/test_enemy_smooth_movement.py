"""Windows-tested KI preview: smooth visual step pacing, no collision desync."""
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

from config import GRID_SIZE
from modules import enemies
from modules.bolbu_enemy import BolbuEnemy
from modules.enemies import NormalEnemy
from modules.enemy_vision import VisionResult


@pytest.mark.parametrize("enemy_type", [NormalEnemy, BolbuEnemy])
def test_ai_glide_follows_most_of_actual_movement_interval_and_hitbox(enemy_type, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(enemies.time, "time", lambda: clock[0])
    enemy = enemy_type()
    enemy.x, enemy.y = 4, 4
    enemy._render_start = enemy._render_target = (4, 4)
    enemy.last_move = clock[0]
    enemy.sprint_chance = 0
    enemy.set_ai_preview(True)
    # For deterministic chase both types use a temporary CHASE profile.
    from modules.enemy_behavior import BehaviorProfile
    enemy.behavior_profile = BehaviorProfile("CHASE", chase_speed=1)
    enemy.facing = (1, 0)
    enemy.eyes.result = VisionResult("VISIBLE", 1, (9, 4), clock[0])
    enemy.update()
    interval = 1.0 / enemy.AI_MOVEMENT_SPEED
    clock[0] += interval + .005
    enemy.update()
    assert (enemy.x, enemy.y) == (5, 4)
    assert enemy._glide_duration == pytest.approx(interval * .9)
    assert enemy.get_render_rect().topleft == (4 * GRID_SIZE, 4 * GRID_SIZE)

    clock[0] += enemy._glide_duration / 2
    enemy.update()
    midpoint = pygame.Rect(
        round(4.5 * GRID_SIZE), 4 * GRID_SIZE, enemy.width, enemy.height,
    )
    assert enemy.get_render_rect() == midpoint
    assert enemy.get_hitbox() == midpoint
    enemy.image = pygame.Surface((enemy.width, enemy.height), pygame.SRCALPHA)
    enemy.image.fill((250, 250, 250))
    canvas = pygame.Surface((12 * GRID_SIZE, 12 * GRID_SIZE), pygame.SRCALPHA)
    # Bolbu's own draw additionally paints only projectiles (none in this test).
    enemy.draw(canvas)
    assert canvas.get_bounding_rect() == midpoint
    clock[0] += enemy._glide_duration / 2
    enemy.update()
    assert enemy.get_hitbox().topleft == (5 * GRID_SIZE, 4 * GRID_SIZE)


def test_ai_speed_switch_does_not_snap_sprite_back_to_previous_cell(monkeypatch):
    clock = [40.0]
    monkeypatch.setattr(enemies.time, "time", lambda: clock[0])
    e = NormalEnemy()
    e.x, e.y = 5, 5
    e._render_start = e._render_target = (5, 5)
    e.last_move = clock[0]
    e.set_ai_preview(True)
    e.sprint_chance = 0
    e.eyes.result = VisionResult("VISIBLE", 1, (15, 5), clock[0])
    from modules.enemy_behavior import BehaviorProfile
    e.behavior_profile = BehaviorProfile("CHASE", chase_speed=1)
    first_interval = 1.0 / e.AI_MOVEMENT_SPEED
    clock[0] += first_interval + .01
    e.update()
    assert e.x == 6
    clock[0] += .31  # old half-second glide has not yet finished
    # The next movement interval drops to ~.28s, so a new step is due.
    e.behavior_profile = BehaviorProfile("CHASE", chase_speed=2)
    before = e.get_render_rect().x
    assert 5 * GRID_SIZE < before < 6 * GRID_SIZE

    # The next tween must start at the last drawn position, not old cell 6.
    e.update()
    assert e.x == 7
    assert e.get_render_rect().x == before
    assert e.get_hitbox() == e.get_render_rect()


def test_ai_off_retains_original_short_glide_and_random_base_speed(monkeypatch):
    clock = [10.]
    monkeypatch.setattr(enemies.time, "time", lambda: clock[0])
    e = NormalEnemy()
    e.x, e.y = 3, 3
    e._render_start = e._render_target = (3, 3)
    e.speed = 1
    e.sprint_chance = 0
    e.last_move = clock[0] - 2
    monkeypatch.setattr(enemies.random, "choice", lambda seq: 1)
    assert not e.behavior_enabled
    e.update()
    assert (e.x, e.y) == (4, 4)
    assert e._glide_duration == pytest.approx(e.GLIDE_SECONDS)
    clock[0] += e.GLIDE_SECONDS
    e.update()
    assert e.get_hitbox().topleft == (4 * GRID_SIZE, 4 * GRID_SIZE)
