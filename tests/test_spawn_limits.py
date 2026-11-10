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

from modules import game as game_module
from modules.enums import Direction, ItemType
from modules.game import Game, Item


def test_food_and_items_use_the_only_free_cell_or_return_when_full(monkeypatch):
    game = Game(headless=True)
    game.start_game(2)
    game.items.clear()
    monkeypatch.setattr(game_module, "GRID_WIDTH", 2)
    monkeypatch.setattr(game_module, "GRID_HEIGHT", 2)
    monkeypatch.setattr(game_module.random, "randint", lambda _low, _high: 0)
    game.snake1 = [(0, 0), (0, 1)]
    game.snake2 = [(1, 0)]

    food = game.spawn_food()

    assert food.type is ItemType.FOOD
    assert (food.x, food.y) == (1, 1)
    assert game.spawn_new_item() is None
    assert game.spawn_food() is None
    assert game.items == [food]


@pytest.mark.parametrize("players, limit", [(1, 12), (2, 16)])
def test_bolbu_spawn_respects_shared_enemy_limit(monkeypatch, players, limit):
    game = Game(headless=True)
    game.start_game(players)
    game.enemies = [object() for _ in range(limit - 1)]
    existing = list(game.enemies)
    item = Item(ItemType.SPAWN_BOLBU)
    randint = game_module.random.randint
    monkeypatch.setattr(game_module.random, "randint",
                        lambda a, b: 3 if (a, b) == (1, 3) else randint(a, b))

    game.handle_item_pickup(item)
    game.handle_item_pickup(item)

    assert game.enemies[:-1] == existing
    assert len(game.enemies) == limit
    assert game.score == 25


def test_multishot_admits_only_free_slots_without_removing_existing_shots(monkeypatch):
    monkeypatch.setattr(game_module, "MAX_PLAYER_GRID_PROJECTILES", 3)
    game = Game(headless=True)
    game.start_game(1)
    boss_shot = {"from_boss": True, "pos": (4, 5), "dir": (0.5, 0)}
    player_shot = {"pos": (2, 3), "dir": (0.5, 0)}
    game.projectiles = [boss_shot, player_shot]
    game.extra_auto_shots = 6

    game.auto_shoot_for_head((5, 5), Direction.RIGHT)
    game.auto_shoot_for_head((5, 5), Direction.RIGHT)

    assert game.projectiles[:2] == [boss_shot, player_shot]
    assert len(game.projectiles) == 4
    assert [shot["projectile_type"] for shot in game.projectiles[2:]] == [
        "player_projectile", "multishot",
    ]
