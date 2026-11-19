"""Swipe D.1 integration: real projectile ticks, pickup caps and boss reaction."""
import os
import sys
import time
from math import hypot
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import FPS, GRID_SIZE
from modules import game as game_module
from modules.boss_defense import IncomingShot, MedusaDefense
from modules.game import Game, Boss, FlameProjectile
from modules.projectile_config import (
    PLAYER_FIREBALL_SPEED_PX_PER_TICK, PLAYER_GRID_SPEED_MULTIPLIER,
    player_grid_speed_cells_per_tick,
)


def test_player_fireball_is_25_percent_slower_with_fractional_pixel_precision():
    assert PLAYER_FIREBALL_SPEED_PX_PER_TICK == pytest.approx(6 * .75)
    flame = FlameProjectile(300, 200, (1, 0))
    x = flame.rect.x
    for _ in range(20):
        assert flame.update()
    assert flame.rect.x - x == 90
    assert flame.speed == 4.5
    assert flame.get_hitbox().contains(flame.get_render_rect())


def test_auto_pickup_halved_but_never_faster_than_player_fireball():
    game = Game(headless=True)
    game.start_game(1)
    game.extra_auto_shots = 5
    game.settings["projectile_speed_factor"] = .5
    game.auto_shoot_for_head(game.snake[0], game.snake_direction)
    assert len(game.projectiles) == 1
    assert game.projectiles[0]["projectile_type"] == "player_projectile"
    # Old stacked spread is deliberately disabled by combat balance.
    cap = PLAYER_FIREBALL_SPEED_PX_PER_TICK / GRID_SIZE
    for shot in game.projectiles:
        vx, vy = shot["dir"]
        assert hypot(vx, vy) == pytest.approx(cap)
        assert hypot(vx * GRID_SIZE, vy * GRID_SIZE) <= PLAYER_FIREBALL_SPEED_PX_PER_TICK + 1e-6
    game.projectiles.clear()
    game.settings["projectile_speed_factor"] = .1
    game.auto_shoot_for_head(game.snake[0], game.snake_direction)
    assert all(hypot(*shot["dir"]) == pytest.approx(.1 * PLAYER_GRID_SPEED_MULTIPLIER)
               for shot in game.projectiles)


def test_all_projectile_families_advance_once_even_on_snake_grid_step(monkeypatch):
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(1)
    game.snake = [(2, 2)]
    fireball = FlameProjectile(12 * GRID_SIZE, 22 * GRID_SIZE, (1, 0))
    x = fireball.rect.x
    game.flame_projectiles = [fireball]
    game.projectiles = [
        {"pos": (20.0, 20.0), "dir": (.15, 0),
         "projectile_type": "player_projectile"},
        {"pos": (25.0, 18.0), "dir": (.5, 0),
         "from_boss": True, "hit_players": ()},
    ]
    game.last_update_time = time.time() - 1.0
    game.update()
    assert fireball.rect.x - x in (4, 5)
    assert game.projectiles[0]["pos"] == pytest.approx((20.15, 20))
    assert game.projectiles[1]["pos"] == pytest.approx((25.5, 18))
    game.last_update_time = time.time() - 1.0
    game.update()
    assert fireball.rect.x - x == 9
    assert game.projectiles[0]["pos"] == pytest.approx((20.30, 20))
    assert game.projectiles[1]["pos"] == pytest.approx((26.0, 18))


def test_medusa_predicts_slow_shots_far_enough_ahead_for_reaction():
    defense = MedusaDefense()
    target = IncomingShot(1, (10.25, 6.5), (-.15, 0), .5)
    assert defense._is_approaching(target, (6.5, 6.5), 3)
    first = defense.visible_threats((6.5, 6.5), (1, 0), 3, [target], ())
    assert first == [target]
    assert not defense.observe((6.5, 6.5), (1, 0), 3, [target], (), 10)
    assert defense.observe((6.5, 6.5), (1, 0), 3, [target], (), 10.07)


@pytest.mark.parametrize("family", ["grid", "fireball"])
def test_actual_moving_player_shot_triggers_swipe_when_lane_is_clear(
        monkeypatch, family):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(1)
    game.start_boss_fight()
    boss = game.boss
    assert isinstance(boss, Boss)
    boss.x, boss.y = 5, 5
    boss.size = 3
    boss.facing = (1, 0)
    boss._visual_from = boss._visual_to = (5, 5)
    boss._visual_step_start = clock.now
    boss.last_move = clock.now
    boss.spawn_time = clock.now - 5
    boss.set_ai_preview(True)
    game.snake = [(2, 2)]
    game._vision_blockers = frozenset()
    if family == "grid":
        player_shot = {
            "pos": (11.0, 6.0), "dir": (-.15, 0),
            "projectile_type": "player_projectile",
        }
        game.projectiles = [player_shot]
    else:
        # Fireballs have a larger sprite/hitbox than the grid pickup shot.
        # They must be perceived *early* to permit a 2-cell side dodge.
        flame = FlameProjectile(13 * GRID_SIZE, round(6.5 * GRID_SIZE), (-1, 0))
        game.flame_projectiles = [flame]
    for _ in range(45):
        game._scan_boss_defense(clock.now)
        if boss.swipe.action is not None:
            break
        if family == "grid":
            px, py = player_shot["pos"]
            player_shot["pos"] = (px - .15, py)
        else:
            flame.update()
        clock.now += 1 / FPS

    assert boss.swipe.action is not None, (
        family, boss.swipe.last_reason, boss._boss_shot_debug,
    )
    assert boss.swipe.charges(clock.now) == 1
    assert any(event["type"] == "boss_swipe" for event in game.combat_events)
    assert boss.swipe.action.destination[0] == 5
