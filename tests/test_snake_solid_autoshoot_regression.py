"""Regression for boss-spawned auto-shoot pickup and solid snake body.

Historically slower pickup shots spawned in the player's own head tile and
were deleted in the first projectile update as an apparent head collision.
"""
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

from modules.enums import Direction, ItemType
from modules.game import Game
from modules.enemies import NormalEnemy
from modules.projectile_config import MAX_PLAYER_GRID_PROJECTILES


@pytest.mark.parametrize("players", [1, 2])
def test_boss_spawn_pickup_autofires_and_shots_survive_owner_head(players):
    game = Game(headless=True)
    game.start_game(players)
    game.start_boss_fight()
    boss = game.boss
    assert boss is not None
    assert any(item.type == ItemType.PROJECTILE_SHOOT for item in game.items)
    boss.x, boss.y = (19, 4)
    game.enemies.clear()
    game.items.clear()
    game.snake = [(4, 4), (3, 4)] if players == 1 else []
    game.snake1 = [(4, 4), (3, 4)] if players == 2 else []
    game.snake2 = [(4, 6), (3, 6)] if players == 2 else []
    target_snake = game.snake if players == 1 else game.snake1
    pickup = game_module_item(ItemType.PROJECTILE_SHOOT, (5, 4))
    game.items.append(pickup)
    assert game._move_snake(1, target_snake, Direction.RIGHT, False)
    assert pickup not in game.items
    assert game.extra_auto_shots == 0
    assert game.effects["projectile_shoot"] > time.time()
    assert not game.projectiles

    # Next update can fire immediately, no two-second apparent dead zone.
    game.auto_shoot()
    assert len(game.projectiles) == players
    assert all(not p.get("from_boss", False) for p in game.projectiles)
    assert all(p["projectile_type"] == "player_projectile" for p in game.projectiles)
    assert all(p["dir"][0] > 0 for p in game.projectiles)

    # The shot is slow and remains inside the head's tile for several frames.
    # Never swallow friendly shots because of that initial overlap.
    first = game.projectiles[0]
    for _ in range(3):
        game.update_projectiles()
    assert first in game.projectiles
    assert first["pos"][0] > 5
    assert len(game.projectiles) == players


def game_module_item(kind, cell):
    from modules.game import Item
    item = Item(kind)
    item.x, item.y = cell
    return item


@pytest.mark.parametrize("players", [1, 2])
def test_pickup_shots_target_boss_and_keep_player_damage_outside_owner(players):
    game = Game(headless=True)
    game.start_game(players)
    game.level = 1
    game.start_boss_fight()
    game.boss.x, game.boss.y = 15, 5
    game.items.clear()
    game.enemies.clear()
    if players == 1:
        game.snake = [(6, 6)]
        head = game.snake[0]
    else:
        game.snake1 = [(6, 6)]
        game.snake2 = [(7, 12)]
        head = game.snake1[0]
    game.handle_item_pickup(game_module_item(ItemType.PROJECTILE_SHOOT, head))
    game.auto_shoot()
    expected = players
    assert len(game.projectiles) == expected
    start_health = game.player_health if players == 1 else game.player_health_p1
    for _ in range(6):
        game.update_projectiles()
    assert len(game.projectiles) == expected
    assert (game.player_health if players == 1 else game.player_health_p1) == start_health


def test_slow_pickup_projectile_hits_enemy_only_once(monkeypatch):
    game = Game(headless=True)
    game.start_game(1)
    game.settings["enemy_spawn_rate"] = 0
    game.last_update_time = time.time() + 50
    game.snake = [(3, 3)]
    enemy = NormalEnemy()
    enemy.x, enemy.y, enemy.health = (8, 5, 3)
    enemy.spawn_time = time.time() - 10
    monkeypatch.setattr(enemy, "update", lambda *_args, **_kwargs: None)
    game.enemies[:] = [enemy]
    game.projectiles = [
        {"pos": (8.05, 5.05), "dir": (.05, 0),
         "projectile_type": "player_projectile"},
    ]
    game.update()
    assert enemy.health == 2
    assert not game.projectiles
    game.update()
    assert enemy.health == 2


def test_boss_bullets_cannot_kill_other_enemies(monkeypatch):
    game = Game(headless=True)
    game.start_game(1)
    game.settings["enemy_spawn_rate"] = 0
    game.last_update_time = time.time() + 50
    game.snake = [(3, 3)]
    enemy = NormalEnemy()
    enemy.x, enemy.y, enemy.health = (8, 5, 3)
    enemy.spawn_time = time.time() - 10
    monkeypatch.setattr(enemy, "update", lambda *_args, **_kwargs: None)
    game.enemies[:] = [enemy]
    game.projectiles = [
        {"pos": (8.05, 5.05), "dir": (.05, 0), "from_boss": True,
         "projectile_type": "boss_projectile"},
    ]
    game.update()
    assert enemy.health == 3


def test_repeated_pickups_extend_duration_without_stacking_bullets():
    game = Game(headless=True)
    game.start_game(1)
    for _ in range(12):
        game.handle_item_pickup(game_module_item(ItemType.PROJECTILE_SHOOT, (0, 0)))
    assert game.extra_auto_shots == 0
    assert game.effects["projectile_shoot"] > time.time() + 900
    game.auto_shoot()
    assert len(game.projectiles) == 1
    assert len(game.projectiles) < MAX_PLAYER_GRID_PROJECTILES
