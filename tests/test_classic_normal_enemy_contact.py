"""Regression checks for normal-enemy contact damage in Classic 1P/2P.

The head is held stationary so the test measures real elapsed time rather
than the movement cadence or number of rendered frames.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE
from modules import game as game_module
from modules.enums import GameState
from modules.game import Game


class StationaryEnemy:
    def __init__(self):
        self.x, self.y = 5, 5
        self.health = 3
        self.spawn_time = 0

    def update(self, *_args, **_kwargs):
        pass

    def get_hitbox(self):
        return pygame.Rect(5 * GRID_SIZE, 5 * GRID_SIZE, GRID_SIZE, GRID_SIZE)


def make_game(monkeypatch, players):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(players)
    game.settings["enemy_spawn_rate"] = 0
    game.respawn_invincible_until = 0
    game.items.clear()
    game.enemies[:] = [StationaryEnemy()]
    if players == 1:
        game.snake = [(5, 5)]
    else:
        game.snake1 = [(5, 5)]
        game.snake2 = [(9, 5)]
    return game, clock


def frame_without_movement(game, clock):
    game.last_update_time = clock.now
    game.update()


@pytest.mark.parametrize("players", [1, 2])
def test_overlap_hurts_once_per_second_not_every_frame(monkeypatch, players):
    game, clock = make_game(monkeypatch, players)
    attribute = "player_health" if players == 1 else "player_health_p1"

    frame_without_movement(game, clock)
    assert getattr(game, attribute) == 90

    for elapsed in (0.01, 0.25, 0.5, 0.99):
        clock.now = 100 + elapsed
        frame_without_movement(game, clock)
        assert getattr(game, attribute) == 90

    clock.now = 101.0
    frame_without_movement(game, clock)
    assert getattr(game, attribute) == 80
    assert game.lives == 3
    if players == 2:
        assert game.player_health_p2 == 100


def test_two_player_contact_has_independent_hit_timers(monkeypatch):
    game, clock = make_game(monkeypatch, 2)
    frame_without_movement(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (90, 100)

    clock.now += 0.5
    game.snake2 = [(5, 5)]
    frame_without_movement(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (90, 90)

    clock.now += 0.5
    frame_without_movement(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (80, 90)

    clock.now += 0.5
    frame_without_movement(game, clock)
    assert (game.player_health_p1, game.player_health_p2) == (80, 80)


@pytest.mark.parametrize("players", [1, 2])
def test_respawn_protection_ignores_normal_enemy_until_expiry(monkeypatch, players):
    game, clock = make_game(monkeypatch, players)
    game.respawn_invincible_until = clock.now + 0.5
    frame_without_movement(game, clock)
    assert (game.player_health if players == 1 else game.player_health_p1) == 100

    clock.now += 0.5
    frame_without_movement(game, clock)
    assert (game.player_health if players == 1 else game.player_health_p1) == 90


def test_simultaneous_lethal_contact_costs_only_one_shared_life(monkeypatch):
    game, clock = make_game(monkeypatch, 2)
    game.snake2 = [(5, 5)]
    game.player_health_p1 = game.player_health_p2 = 10
    game.lives = 2

    frame_without_movement(game, clock)

    assert game.lives == 1
    assert game.game_state is GameState.GAME
    assert (game.player_health_p1, game.player_health_p2) == (100, 100)
    assert game.respawn_invincible_until > clock.now


def test_new_round_resets_normal_enemy_contact_timer(monkeypatch):
    game, clock = make_game(monkeypatch, 1)
    frame_without_movement(game, clock)
    assert game.player_health == 90

    clock.now += 0.25
    game.start_game(1)
    game.settings["enemy_spawn_rate"] = 0
    game.respawn_invincible_until = 0
    game.enemies[:] = [StationaryEnemy()]
    game.snake = [(5, 5)]
    frame_without_movement(game, clock)
    assert game.player_health == 90
