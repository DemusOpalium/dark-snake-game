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

from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH
from modules import game as game_module
from modules.boss_projectiles import BossFlameProjectile
from modules.enemies import NormalEnemy
from modules.enums import Direction, GameState, ItemType
from modules.game import Game, Item


PLAYER_CASES = [(1, ""), (2, "1"), (2, "2")]
LOOP = [(4, 4), (4, 3), (5, 3), (5, 4)]
BODY_CONTACT = LOOP + [(6, 4)]
DESTINATION = (5, 4)
RESPAWN = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]


def test_boss_flame_is_removed_once_when_both_players_overlap(monkeypatch):
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game()
    game.start_game(2)
    game.snake1 = game.snake2 = [(5, 5)]
    center = (5 * GRID_SIZE + GRID_SIZE // 2,) * 2
    flame = BossFlameProjectile(*center, (1, 0), speed=0, damage=4)
    game.boss_flame_projectiles.append(flame)
    game.last_update_time = game_module.time.time() + 10

    game.update()

    assert not game.boss_flame_projectiles
    assert (game.player_health_p1, game.player_health_p2) == (96, 96)
    assert len(game.explosions) == 1


def setup_turn(monkeypatch, players, suffix, segments):
    game = Game(headless=True)
    game.start_game(players)
    game.items.clear()
    setattr(game, f"snake{suffix}", list(segments))
    setattr(game, f"snake_direction{suffix}", Direction.DOWN)
    setattr(game, f"next_direction{suffix}", Direction.RIGHT)
    game._reset_snake_interpolation()
    now = game_module.time.time()
    monkeypatch.setattr(game_module.time, "time", lambda: now)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game.respawn_invincible_until = now - 1
    game.last_update_time = now - 1
    return game, now


def place_item(game, kind, position):
    item = Item(kind)
    item.x, item.y = position
    game.items.append(item)
    return item


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_head_can_enter_own_tail_cell_when_tail_moves(monkeypatch, players, suffix):
    game, _ = setup_turn(monkeypatch, players, suffix, LOOP)
    game.update()

    assert game.lives == 3
    assert getattr(game, f"snake{suffix}") == [DESTINATION, *LOOP[:-1]]


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_item_on_tail_cell_keeps_it_occupied(monkeypatch, players, suffix):
    game, _ = setup_turn(monkeypatch, players, suffix, LOOP)
    item = place_item(game, ItemType.SCORE_BOOST, DESTINATION)
    game.update()

    assert game.lives == 2
    assert getattr(game, f"snake{suffix}") == RESPAWN
    assert item in game.items
    assert game.score == 0


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_body_collision_costs_a_life_at_positive_health(monkeypatch, players, suffix):
    game, now = setup_turn(monkeypatch, players, suffix, BODY_CONTACT)
    health_attr = f"player_health_p{suffix}" if suffix else "player_health"
    setattr(game, health_attr, 60)
    game.update()

    assert game.lives == 2
    assert game.game_state == GameState.GAME
    assert getattr(game, health_attr) == 100
    assert getattr(game, f"snake{suffix}") == getattr(game, f"previous_snake{suffix}") == RESPAWN
    assert game.respawn_invincible_until > now


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_body_collision_can_end_game_at_positive_health(monkeypatch, players, suffix):
    game, _ = setup_turn(monkeypatch, players, suffix, BODY_CONTACT)
    game.lives = 1
    game.update()
    assert game.lives == 0
    assert game.game_state == GameState.GAME_OVER


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
@pytest.mark.parametrize("protection", ["respawn", "item"])
def test_invincibility_allows_body_contact(monkeypatch, players, suffix, protection):
    game, now = setup_turn(monkeypatch, players, suffix, BODY_CONTACT)
    if protection == "respawn":
        game.respawn_invincible_until = now + 1
    else:
        game.handle_item_pickup(Item(ItemType.INVINCIBILITY))
    game.update()

    assert game.lives == 3
    assert getattr(game, f"snake{suffix}") == [DESTINATION, *BODY_CONTACT[:-1]]


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_food_on_free_cell_is_consumed_and_grows_snake(monkeypatch, players, suffix):
    segments = [(4, 4), (4, 3), (4, 2)]
    game, _ = setup_turn(monkeypatch, players, suffix, segments)
    food = place_item(game, ItemType.FOOD, DESTINATION)
    game.update()

    assert getattr(game, f"snake{suffix}") == [DESTINATION, *segments]
    assert food not in game.items
    assert game.lives == 3
    assert game.score == game.experience == 10


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_enemy_contact_uses_sprite_rectangle_without_extra_offset(monkeypatch, players, suffix):
    game, now = setup_turn(monkeypatch, players, suffix, [(4, 4)])
    health_attr = f"player_health_p{suffix}" if suffix else "player_health"
    game.last_update_time = now
    enemy = NormalEnemy()
    enemy.x, enemy.y = 5, 4
    enemy.width = enemy.height = int(GRID_SIZE * 1.5)
    enemy.sprint_chance = 0
    game.enemies.append(enemy)

    game.update()
    assert getattr(game, health_attr) == 100

    enemy.x = 4
    game.update()
    assert getattr(game, health_attr) == 90
