"""Regression coverage for Classic normal-enemy spawning independent of Auto-Shoot."""

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

from modules import game as game_module
from modules.game import Game


class HarmlessEnemy:
    """A normal-enemy stand-in that does not affect a player's test movement."""

    def __init__(self):
        self.x, self.y = 0, 0
        self.spawn_time = time.time()
        self.health = 1

    def update(self, *_args, **_kwargs):
        pass

    def get_hitbox(self):
        return pygame.Rect(-100, -100, 1, 1)


def _prepare_game(monkeypatch, players, auto_shoot):
    game = Game(headless=True)
    game.start_game(players)
    game.respawn_invincible_until = float("inf")
    game.effects["projectile_shoot"] = time.time() + 60 if auto_shoot else 0
    fired = []
    monkeypatch.setattr(game, "auto_shoot", lambda: fired.append(True))
    monkeypatch.setattr(game_module, "NormalEnemy", HarmlessEnemy)
    return game, fired


@pytest.mark.parametrize("players", [1, 2])
@pytest.mark.parametrize("auto_shoot", [False, True])
def test_normal_enemies_spawn_without_needing_auto_shoot(monkeypatch, players, auto_shoot):
    game, fired = _prepare_game(monkeypatch, players, auto_shoot)
    game.settings["enemy_spawn_rate"] = 1.0
    # Succeeds for a spawn rate of 1.0, but does not trigger the independent AoE.
    monkeypatch.setattr(game_module.random, "random", lambda: 0.5)

    game.update()

    assert len(game.enemies) == 1
    assert isinstance(game.enemies[0], HarmlessEnemy)
    assert bool(fired) is auto_shoot


@pytest.mark.parametrize("players", [1, 2])
@pytest.mark.parametrize("auto_shoot", [False, True])
def test_normal_enemy_spawn_obeys_probability(monkeypatch, players, auto_shoot):
    game, fired = _prepare_game(monkeypatch, players, auto_shoot)
    game.settings["enemy_spawn_rate"] = 0.002
    monkeypatch.setattr(game_module.random, "random", lambda: 0.5)

    game.update()

    assert game.enemies == []
    assert bool(fired) is auto_shoot


@pytest.mark.parametrize("players,limit", [(1, 12), (2, 16)])
@pytest.mark.parametrize("auto_shoot", [False, True])
def test_normal_enemy_spawn_keeps_shared_limit(monkeypatch, players, limit, auto_shoot):
    game, fired = _prepare_game(monkeypatch, players, auto_shoot)
    game.settings["enemy_spawn_rate"] = 1.0
    game.enemies = [HarmlessEnemy() for _ in range(limit)]
    # A successful spawn roll must not exceed the shared normal/Bolbu cap.
    monkeypatch.setattr(game_module.random, "random", lambda: 0.5)

    game.update()

    assert len(game.enemies) == limit
    assert bool(fired) is auto_shoot
