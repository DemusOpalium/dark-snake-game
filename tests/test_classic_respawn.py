"""Classic respawn must be safe, readable and independent of framerate."""

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

from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH
from modules import game as game_module
from modules.enums import Direction, GameState
from modules.game import Game
from modules.respawn import (FrostRespawnVisual, RespawnCountdown, RESPAWN_SECONDS,
                             safe_spawn_cells)


class DummyEnemy:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.updates = 0
        self.spawn_time = 0
        self.last_move = 0

    def update(self, *_args, **_kwargs):
        self.updates += 1

    def get_hitbox(self):
        return pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, GRID_SIZE, GRID_SIZE)

    def draw(self, screen):
        pass


def round_with_clock(monkeypatch, players):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(players)
    game.settings["enemy_spawn_rate"] = 0
    game.items.clear()
    game.enemies.clear()
    return game, clock


def lose_life(game):
    game.player_health = 0
    game.player_health_p1 = 0
    game.handle_death()
    assert game.lives == 2
    assert game.respawn.active


@pytest.mark.parametrize("players", [1, 2])
def test_lose_life_restores_classic_placements_but_pauses_movement(monkeypatch, players):
    game, clock = round_with_clock(monkeypatch, players)
    lose_life(game)
    center = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
    assert (game.snake1 if players == 2 else game.snake) == [center]
    if players == 2:
        assert game.snake2 == [(center[0], center[1] + 2)]

    start = game.snake1[0] if players == 2 else game.snake[0]
    for seconds in (0.125, 1, 2.99):
        clock.now = 100 + seconds
        game.last_update_time = 0  # Any regular gameplay update would move.
        game.update()
        assert game.respawn.active
        assert (game.snake1 if players == 2 else game.snake)[0] == start
        assert game.lives == 2
    assert game.respawn.number == 1
    clock.now = 103
    game.update()  # GO frame itself still cannot move.
    assert not game.respawn.active
    assert (game.snake1 if players == 2 else game.snake)[0] == start
    assert game.respawn_invincible_until == pytest.approx(104.0)
    assert game.last_update_time == pytest.approx(clock.now)


def test_directions_are_queued_independently_and_fire_is_ignored(monkeypatch):
    game, clock = round_with_clock(monkeypatch, 2)
    lose_life(game)
    game._apply_gameplay_actions({"p1_left", "p2_up", "p1_fire", "p2_fire", "special_effect"})
    assert game.next_direction1 == Direction.LEFT
    assert game.next_direction2 == Direction.UP
    assert not game.flame_projectiles
    assert not game.aoe_zones

    clock.now += 3
    game.update()
    game.respawn_invincible_until = 0  # Movement is allowed after GO.
    game.last_update_time = clock.now - 1
    game.update()
    assert game.snake1[0][0] == GRID_WIDTH // 2 - 1
    assert game.snake2[0][1] == GRID_HEIGHT // 2 + 1


def test_countdown_pauses_while_pause_menu_is_open(monkeypatch):
    game, clock = round_with_clock(monkeypatch, 1)
    lose_life(game)
    clock.now += 1
    game.update()
    assert game.respawn.number == 2
    game.set_state(GameState.PAUSE)
    clock.now += 20
    game.update()
    assert game.respawn.number == 2
    game.set_state(GameState.GAME)
    game.update()
    assert game.respawn.active
    clock.now += 2
    game.update()
    assert not game.respawn.active


def test_world_enemy_and_boss_timers_are_not_consumed_by_countdown(monkeypatch):
    game, clock = round_with_clock(monkeypatch, 1)
    enemy = DummyEnemy(4, 4)
    enemy.last_move = 80
    enemy.spawn_time = 90
    game.enemies.append(enemy)
    timer = game.boss_spawn_timer
    lose_life(game)
    clock.now += 1
    game.update()
    clock.now += 2
    game.update()
    assert not game.respawn.active
    assert enemy.updates == 0
    assert enemy.last_move == pytest.approx(83)
    assert enemy.spawn_time == pytest.approx(93)
    assert game.boss_spawn_timer == pytest.approx(timer + 3)


def test_safe_respawn_avoids_enemies_and_spawns_both_heads_apart(monkeypatch):
    game, _ = round_with_clock(monkeypatch, 2)
    mid = (GRID_WIDTH // 2, GRID_HEIGHT // 2)
    game.enemies += [DummyEnemy(*mid), DummyEnemy(mid[0], mid[1] + 2)]
    lose_life(game)
    p1, p2 = game.snake1[0], game.snake2[0]
    assert p1 != p2
    assert p1 not in (mid, (mid[0], mid[1] + 2))
    assert p2 not in (mid, (mid[0], mid[1] + 2))
    assert abs(p1[0] - p2[0]) + abs(p1[1] - p2[1]) >= 2


def test_no_free_cells_still_yields_distinct_inbounds_protected_heads():
    positions = safe_spawn_cells(2, 10, 10, safe=lambda _: False)
    assert len(positions) == len(set(positions)) == 2
    assert all(0 <= x < 10 and 0 <= y < 10 for x, y in positions)


def test_final_life_goes_to_game_over_without_respawn(monkeypatch):
    game, _ = round_with_clock(monkeypatch, 2)
    game.lives = 1
    game.player_health_p2 = 0
    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert not game.respawn.active


def test_stall_loss_also_uses_the_same_countdown(monkeypatch):
    game, _ = round_with_clock(monkeypatch, 2)
    game.handle_self_collision()
    assert game.respawn.active
    assert game.snake1 != game.snake2


def test_new_round_clears_pending_overlay(monkeypatch):
    game, _ = round_with_clock(monkeypatch, 1)
    lose_life(game)
    game.start_game(1)
    assert not game.respawn.active
    assert game.lives == 3


def test_frostage_overlay_draws_fallback_and_centered_countdown(monkeypatch):
    monkeypatch.setattr("modules.respawn.load_frostage_image", lambda asset: None)
    overlay = FrostRespawnVisual()
    state = RespawnCountdown()
    state.begin(100.0)
    screen = pygame.Surface((900, 620))
    screen.fill((1, 2, 3))
    overlay.draw(screen, state, [(450, 310)])
    assert screen.get_at((450, 310)) != pygame.Color(1, 2, 3)
    assert screen.get_at((10, 10)) == pygame.Color(1, 2, 3)
    assert state.number == 3
    state.step(102.1, playing=True)
    assert state.number == 1
