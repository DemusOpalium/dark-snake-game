"""Regression: no purple ghost-orbs after boss attacks or boss defeat."""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1280, 900))

from config import GRID_SIZE
from modules.game import Game
from modules.boss_projectiles import BossFlameProjectile, BossProjectile
from modules.projectile_config import BOSS_PROJECTILE_LIFETIME_TICKS


def game_with_boss():
    game = Game(headless=True)
    game.start_game(1)
    game.start_boss_fight()
    assert game.boss is not None
    return game


def test_aim_at_previous_boss_top_left_never_produces_a_zero_vector():
    game = game_with_boss()
    boss = game.boss
    game.snake = [(boss.x, boss.y)]
    dx, dy = game._boss_projectile_heading(game.snake[0])
    assert (dx, dy) != (0, 0)
    assert (dx, dy) == pytest.approx((-boss.size / 2 + .5,
                                     -boss.size / 2 + .5))


def test_boss_flame_uses_centre_target_and_facing_if_targets_overlap():
    game = game_with_boss()
    boss = game.boss
    boss.x, boss.y = (8, 6)
    boss.size = 3
    boss.facing = (0, -1)
    game.snake = [(9, 7)]  # head centre equals boss centre
    game.boss_shoots_flame()
    assert len(game.boss_flame_projectiles) == 1
    ball = game.boss_flame_projectiles[0]
    assert ball.direction == (0, -1)
    y = ball.rect.y
    for _ in range(10):
        assert ball.update()
    assert ball.rect.y - y == -24


@pytest.mark.parametrize("kind", [BossProjectile, BossFlameProjectile])
def test_boss_class_shots_keep_fractional_velocity_and_move_diagonally(kind):
    ball = kind(350, 350, (.2, .8))
    begin = ball.rect.topleft
    for _ in range(10):
        assert ball.update()
    assert ball.rect.x > begin[0]
    assert ball.rect.y > begin[1]
    assert ball.lifetime > 0


@pytest.mark.parametrize("kind", [BossProjectile, BossFlameProjectile])
def test_zero_vector_constructor_is_no_longer_a_permanent_stationary_orb(kind):
    ball = kind(350, 350, (0, 0))
    assert ball.direction == (1, 0)
    x = ball.rect.x
    assert ball.update()
    assert ball.rect.x > x


def test_existing_classic_zero_speed_mock_is_still_allowed():
    ball = BossFlameProjectile(150, 150, (1, 0), speed=0, damage=4)
    start = ball.rect.copy()
    ball.update()
    assert ball.rect == start
    assert ball.damage == 4


def test_grid_boss_zero_direction_removed_but_player_shot_untouched():
    game = game_with_boss()
    game.snake = [(3, 3)]
    still_boss = {"from_boss": True, "pos": (25.0, 20.0),
                  "dir": (0, 0), "projectile_type": "boss_projectile"}
    player_shot = {"pos": (22.0, 23.0), "dir": (0, 0),
                   "projectile_type": "player_projectile"}
    game.projectiles = [still_boss, player_shot]
    game.update_projectiles()
    assert game.projectiles == [player_shot]


def test_boss_grid_shot_lifetime_is_bounded_not_infinite():
    game = game_with_boss()
    shot = {"from_boss": True, "pos": (20.0, 20.0),
            "dir": (.02, 0), "lifetime_ticks": 2}
    game.projectiles = [shot]
    game.update_projectiles()
    assert game.projectiles == [shot]
    assert shot["lifetime_ticks"] == 1
    game.update_projectiles()
    assert game.projectiles == []
    assert BOSS_PROJECTILE_LIFETIME_TICKS > 2


def test_boss_death_purges_old_purple_orbs_and_preserves_player_shots():
    game = game_with_boss()
    boss_shot = {"from_boss": True, "pos": (20, 20), "dir": (.2, 0)}
    player_shot = {"pos": (25, 25), "dir": (.1, 0)}
    boss_flame = BossFlameProjectile(300, 250, (1, 0))
    game.projectiles = [boss_shot, player_shot]
    game.boss_flame_projectiles = [boss_flame]
    assert game.damage_boss(game.boss.health, "player_fireball")
    assert game.boss is None
    assert game.projectiles == [player_shot]
    assert game.boss_flame_projectiles == []


def test_boss_shoot_event_aims_without_stationary_grid_orbs(monkeypatch):
    game = game_with_boss()
    boss = game.boss
    boss.x, boss.y = (10, 10)
    boss.size = 3
    boss.spawn_time = 0
    boss.facing = (0, 1)
    game.snake = [(10, 10)]  # previously produced dir=(0,0)
    # Exercise exactly the real boss_shoot path without random attacks/moves.
    monkeypatch.setattr(boss, "update", lambda now: "boss_shoot")
    game.last_update_time -= 3
    game._vision_blockers = frozenset()
    game.update()
    boss_shots = [p for p in game.projectiles if p.get("from_boss")]
    assert len(boss_shots) == 1
    assert boss_shots[0]["dir"] != (0, 0)
    assert boss_shots[0]["lifetime_ticks"] == BOSS_PROJECTILE_LIFETIME_TICKS
