import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE
from modules import game as game_module
from modules.boss_projectiles import BossFlameProjectile
from modules.enums import Direction, GameState
from modules.game import Game


def make_round(monkeypatch, players, *, headless=True):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=headless)
    game.start_game(players)
    game.items.clear()
    game.respawn_invincible_until = clock.now - 1
    return game, clock


def add_boss(game, clock, *, action=None):
    boss = SimpleNamespace(x=5, y=4, size=3, health=100, spawn_time=clock.now - 4)
    boss.get_rect = lambda: pygame.Rect(boss.x * GRID_SIZE, boss.y * GRID_SIZE,
                                        boss.size * GRID_SIZE, boss.size * GRID_SIZE)
    boss.update = Mock(return_value=action)
    game.boss = boss
    game.boss_fight_active = True
    game.game_state = GameState.BOSS_FIGHT
    return boss


def raster_turn(game, clock):
    game.last_update_time = clock.now - 1
    game.update()


def frame_without_turn(game, clock):
    game.last_update_time = clock.now
    game.update()


def test_boss_body_hurts_single_player_and_boss_can_still_attack(monkeypatch):
    game, clock = make_round(monkeypatch, 1)
    boss = add_boss(game, clock, action="boss_shoot")
    game.snake = [(4, 5)]

    raster_turn(game, clock)

    assert game.snake[0] == (5, 5)
    assert game.player_health == 90
    assert boss.health == 100
    assert game.lives == 3
    boss.update.assert_called_once_with(clock.now)
    assert any(shot.get("from_boss") for shot in game.projectiles)


@pytest.mark.parametrize("p1_y, p1_health", [(2, 100), (5, 90)])
def test_boss_body_hurts_second_player_even_if_first_is_outside(monkeypatch, p1_y, p1_health):
    game, clock = make_round(monkeypatch, 2)
    boss = add_boss(game, clock)
    game.snake1 = [(4, p1_y)]
    game.snake2 = [(4, 6)]

    raster_turn(game, clock)

    assert game.snake2[0] == (5, 6)
    assert (game.player_health_p1, game.player_health_p2) == (p1_health, 90)
    assert boss.health == 100
    assert game.lives == 3


def test_boss_body_cooldown_lasts_one_second_per_player(monkeypatch):
    game, clock = make_round(monkeypatch, 2)
    boss = add_boss(game, clock)
    game.snake1 = [(5, 5)]
    game.snake2 = [(4, 6)]
    frame_without_turn(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (90, 100)

    clock.now += 0.5
    raster_turn(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (90, 90)

    clock.now += 0.25
    frame_without_turn(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (90, 90)

    clock.now += 0.25
    frame_without_turn(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (80, 90)

    clock.now += 0.5
    frame_without_turn(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (80, 80)
    assert boss.health == 100


@pytest.mark.parametrize("protection", ["boss_spawn", "player_respawn"])
def test_boss_body_honors_protection_without_using_hit_cooldown(monkeypatch, protection):
    game, clock = make_round(monkeypatch, 1)
    boss = add_boss(game, clock)
    game.snake = [(4, 5)]
    if protection == "boss_spawn":
        boss.spawn_time = clock.now - 2.5
    else:
        game.respawn_invincible_until = clock.now + 0.5

    raster_turn(game, clock)
    assert game.snake[0] == (5, 5)
    assert game.player_health == 100

    clock.now += 0.5
    frame_without_turn(game, clock)
    assert game.player_health == 90


@pytest.mark.parametrize("lives", [1, 2])
def test_lethal_boss_body_contact_costs_one_shared_life(monkeypatch, lives):
    game, clock = make_round(monkeypatch, 2)
    add_boss(game, clock)
    game.snake1 = [(4, 5)]
    game.snake2 = [(4, 6)]
    game.player_health_p1 = game.player_health_p2 = 10
    game.lives = lives

    raster_turn(game, clock)

    assert game.lives == lives - 1
    if lives == 1:
        assert game.game_state is GameState.GAME_OVER
        assert game.player_health_p1 == game.player_health_p2 == 0
    else:
        assert game.game_state is GameState.BOSS_FIGHT
        assert game.player_health_p1 == game.player_health_p2 == 100
        assert game.respawn_invincible_until > clock.now


@pytest.mark.parametrize("lives", [1, 2])
def test_lethal_boss_flame_on_both_heads_costs_one_shared_life(monkeypatch, lives):
    game, clock = make_round(monkeypatch, 2, headless=False)
    game.snake1 = [(5, 5)]
    game.snake2 = [(5, 5)]
    game.player_health_p1 = game.player_health_p2 = 4
    game.lives = lives
    center = 5 * GRID_SIZE + GRID_SIZE // 2
    flame = BossFlameProjectile(center, center, (1, 0), speed=0, damage=4)
    game.boss_flame_projectiles.append(flame)

    frame_without_turn(game, clock)

    assert not game.boss_flame_projectiles
    assert len(game.explosions) == 1
    assert game.lives == lives - 1
    assert game.game_state is (GameState.GAME_OVER if lives == 1 else GameState.GAME)


@pytest.mark.parametrize(("p2_start", "p2_end"), [(6, 5), (5, 4)])
def test_classic_two_player_heads_can_share_or_swap_cells(monkeypatch, p2_start, p2_end):
    game, clock = make_round(monkeypatch, 2)
    game.snake1 = [(4, 4)]
    game.snake2 = [(p2_start, 4)]
    game.snake_direction1 = game.next_direction1 = Direction.RIGHT
    game.snake_direction2 = game.next_direction2 = Direction.LEFT

    raster_turn(game, clock)

    assert game.snake1 == [(5, 4)]
    assert game.snake2 == [(p2_end, 4)]
    assert game.lives == 3
    assert game.player_health_p1 == game.player_health_p2 == 100
