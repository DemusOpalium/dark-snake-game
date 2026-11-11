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
from modules.boss_projectiles import BossFlameProjectile
from modules.enemies import NormalEnemy
from modules.enums import Direction, GameState, ItemType
from modules.game import Game, Item


PLAYER_CASES = [(1, ""), (2, "1"), (2, "2")]
LOOP = [(4, 4), (4, 3), (5, 3), (5, 4)]
BODY_CONTACT = LOOP + [(6, 4)]
DESTINATION = (5, 4)


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
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    monkeypatch.setattr(game_module.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=True)
    game.settings["initial_speed"] = 8
    game.start_game(players)
    game.items.clear()
    setattr(game, f"snake{suffix}", list(segments))
    setattr(game, f"snake_direction{suffix}", Direction.DOWN)
    setattr(game, f"next_direction{suffix}", Direction.RIGHT)
    game._reset_snake_interpolation()
    game.respawn_invincible_until = clock.now - 1
    game.last_update_time = clock.now - 1
    return game, clock


def advance_frames(clock, callback, frames):
    for _ in range(frames):
        clock.now += 0.125
        callback()


def post_key(key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=""))


def place_item(game, kind, position):
    item = Item(kind)
    item.x, item.y = position
    game.items.append(item)
    return item


def respawn_position():
    return [(game_module.GRID_WIDTH // 2, game_module.GRID_HEIGHT // 2)]


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

    assert game.lives == 3
    assert getattr(game, f"snake{suffix}") == LOOP
    assert item in game.items
    assert game.score == 0


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_body_block_preserves_position_and_health_until_three_seconds(monkeypatch, players, suffix):
    game, clock = setup_turn(monkeypatch, players, suffix, BODY_CONTACT)
    health_attr = f"player_health_p{suffix}" if suffix else "player_health"
    setattr(game, health_attr, 60)
    game.update()

    assert game.lives == 3
    assert getattr(game, health_attr) == 60
    assert getattr(game, f"snake{suffix}") == BODY_CONTACT

    advance_frames(clock, game.update, 23)
    assert game.lives == 3
    assert getattr(game, health_attr) == 60
    assert getattr(game, f"snake{suffix}") == BODY_CONTACT

    advance_frames(clock, game.update, 1)
    assert game.lives == 2
    assert game.game_state == GameState.GAME
    assert getattr(game, health_attr) == 100
    assert getattr(game, f"snake{suffix}") == getattr(game, f"previous_snake{suffix}") == respawn_position()
    assert game.respawn_invincible_until > clock.now


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
def test_body_block_can_end_game_after_three_seconds(monkeypatch, players, suffix):
    game, clock = setup_turn(monkeypatch, players, suffix, BODY_CONTACT)
    game.lives = 1
    game.update()
    assert game.lives == 1
    assert game.game_state == GameState.GAME

    advance_frames(clock, game.update, 24)

    assert game.lives == 0
    assert game.game_state == GameState.GAME_OVER


def test_body_block_can_expire_between_raster_turns(monkeypatch):
    game, clock = setup_turn(monkeypatch, 1, "", BODY_CONTACT)
    game.update()
    clock.now += 2.9375
    game.update()
    assert game.lives == 3

    clock.now += 0.0625
    game.update()
    assert game.lives == 2
    assert game.snake == respawn_position()


def test_player_can_escape_before_three_seconds_and_restart_the_timer(monkeypatch):
    game, clock = setup_turn(monkeypatch, 1, "", BODY_CONTACT)
    game.update()
    advance_frames(clock, game.update, 20)

    post_key(pygame.K_a)
    game.handle_events()
    advance_frames(clock, game.update, 1)
    assert game.snake == [(3, 4), *BODY_CONTACT[:-1]]
    assert game.lives == 3

    # A new blocked turn shortly after the escape needs its own three seconds.
    game.snake = list(BODY_CONTACT)
    game.snake_direction = Direction.DOWN
    game.next_direction = Direction.RIGHT
    advance_frames(clock, game.update, 1)
    advance_frames(clock, game.update, 23)
    assert game.snake == BODY_CONTACT
    assert game.lives == 3
    advance_frames(clock, game.update, 1)
    assert game.lives == 2


@pytest.mark.parametrize("pause_key", [pygame.K_p, pygame.K_TAB, pygame.K_F2])
def test_body_block_timer_excludes_pause_admin_and_editor(monkeypatch, pause_key):
    game, clock = setup_turn(monkeypatch, 1, "", BODY_CONTACT)
    monkeypatch.setattr(game, "draw", lambda: None)
    game.update()
    advance_frames(clock, game.run_frame, 8)
    post_key(pause_key)
    game.run_frame()
    assert game.game_state == GameState.PAUSE or game.admin_panel.active or game.level_editor.active

    clock.now += 10
    game.run_frame()
    assert game.lives == 3
    assert game.snake == BODY_CONTACT

    post_key(pygame.K_p if pause_key == pygame.K_p else pygame.K_ESCAPE)
    game.run_frame()
    assert game.game_state == GameState.GAME
    assert not game.admin_panel.active and not game.level_editor.active
    advance_frames(clock, game.run_frame, 15)
    assert game.lives == 3
    advance_frames(clock, game.run_frame, 1)
    assert game.lives == 2


@pytest.mark.parametrize("blocked, free", [("1", "2"), ("2", "1")])
def test_other_player_and_world_keep_moving_while_one_head_is_blocked(monkeypatch, blocked, free):
    game, clock = setup_turn(monkeypatch, 2, blocked, BODY_CONTACT)
    setattr(game, f"snake{free}", [(20, 10)])

    def choose_direction(options):
        return 1 if options == [-1, 0, 1] else options[0]

    monkeypatch.setattr(game_module.random, "choice", choose_direction)
    assert game.start_boss_fight()
    game.boss.x, game.boss.y = (32, 23)
    game.boss.chase_speed = 0.125
    game.boss.last_move = clock.now - 0.125
    enemy = NormalEnemy()
    enemy.x, enemy.y = (24, 20)
    enemy.speed = 8
    enemy.last_move = clock.now - 0.125
    game.enemies.append(enemy)
    shot = {"from_boss": True, "pos": (10, 20), "dir": (0.5, 0)}
    game.projectiles.append(shot)

    game.update()
    advance_frames(clock, game.update, 1)

    assert getattr(game, f"snake{blocked}") == BODY_CONTACT
    assert getattr(game, f"snake{free}") == [(22, 10)]
    assert shot["pos"] == (12, 20)
    assert (enemy.x, enemy.y) == (26, 22)
    assert (game.boss.x, game.boss.y) == (34, 25)
    assert game.lives == 3


def test_two_expiring_body_block_timers_cost_one_shared_life(monkeypatch):
    game, clock = setup_turn(monkeypatch, 2, "1", BODY_CONTACT)
    second_body = [(x, y + 8) for x, y in BODY_CONTACT]
    game.snake2 = list(second_body)
    game.update()
    advance_frames(clock, game.update, 23)

    assert game.snake1 == BODY_CONTACT
    assert game.snake2 == second_body
    assert game.lives == 3

    advance_frames(clock, game.update, 1)
    assert game.lives == 2
    assert game.snake1 == game.snake2 == respawn_position()
    advance_frames(clock, game.update, 1)
    assert game.lives == 2


def test_first_player_escape_does_not_change_second_players_deadline(monkeypatch):
    game, clock = setup_turn(monkeypatch, 2, "1", BODY_CONTACT)
    game.update()
    advance_frames(clock, game.update, 8)

    second_body = [(x, y + 8) for x, y in BODY_CONTACT]
    game.snake2 = list(second_body)
    game.snake_direction2 = Direction.DOWN
    game.next_direction2 = Direction.RIGHT
    advance_frames(clock, game.update, 8)

    post_key(pygame.K_a)
    game.handle_events()
    advance_frames(clock, game.update, 1)
    assert game.snake1[0] == (3, 4)
    advance_frames(clock, game.update, 15)
    assert game.snake2 == second_body
    assert game.lives == 3

    advance_frames(clock, game.update, 1)
    assert game.lives == 2
    assert game.snake1 == game.snake2 == respawn_position()


def test_teleport_restarts_the_timer_for_a_new_body_block(monkeypatch):
    game, clock = setup_turn(monkeypatch, 1, "", BODY_CONTACT)
    game.update()
    advance_frames(clock, game.update, 16)
    original_randint = game_module.random.randint

    def teleport_coordinates(low, high):
        if low == 0 and high in (game_module.GRID_WIDTH - 1, game_module.GRID_HEIGHT - 1):
            return 3
        return original_randint(low, high)

    monkeypatch.setattr(game_module.random, "randint", teleport_coordinates)
    game.activate_portal("teleport")
    assert game.snake[0] == (3, 3)
    advance_frames(clock, game.update, 24)
    assert game.snake[0] == (3, 3)
    assert game.lives == 3

    advance_frames(clock, game.update, 1)
    assert game.lives == 2
    assert game.snake == respawn_position()


@pytest.mark.parametrize("round_change", ["restart", "respawn"])
def test_new_body_block_after_round_change_gets_a_fresh_timer(monkeypatch, round_change):
    game, clock = setup_turn(monkeypatch, 1, "", BODY_CONTACT)
    game.update()
    if round_change == "restart":
        advance_frames(clock, game.update, 16)
        game.start_game(1)
        game.items.clear()
        remaining_lives = 3
    else:
        advance_frames(clock, game.update, 24)
        assert game.snake == respawn_position()
        assert game.lives == 2
        remaining_lives = 2

    game.snake = list(BODY_CONTACT)
    game.next_direction = Direction.RIGHT
    game.respawn_invincible_until = clock.now - 1
    game.last_update_time = clock.now - 1
    game.update()
    advance_frames(clock, game.update, 23)
    assert game.snake == BODY_CONTACT
    assert game.lives == remaining_lives

    advance_frames(clock, game.update, 1)
    assert game.lives == remaining_lives - 1


@pytest.mark.parametrize("players,suffix", PLAYER_CASES)
@pytest.mark.parametrize("protection", ["respawn", "item"])
def test_invincibility_allows_body_contact(monkeypatch, players, suffix, protection):
    game, clock = setup_turn(monkeypatch, players, suffix, BODY_CONTACT)
    if protection == "respawn":
        game.respawn_invincible_until = clock.now + 1
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
    game, clock = setup_turn(monkeypatch, players, suffix, [(4, 4)])
    health_attr = f"player_health_p{suffix}" if suffix else "player_health"
    game.last_update_time = clock.now
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
