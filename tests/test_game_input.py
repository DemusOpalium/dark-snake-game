import json
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

from config import GRID_SIZE
from modules.aoe_zones import BackgroundEffectZone, DamageZone, DebuffZone, HealZone
from modules.enums import Direction, GameState
from modules.game import Game


def press(game, code, text=""):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=code, unicode=text))
    game.handle_events()


@pytest.mark.parametrize(("code", "zone_type"), [
    (pygame.K_r, DamageZone),
    (pygame.K_t, DebuffZone),
    (pygame.K_z, HealZone),
])
def test_two_player_debug_zones_use_player_one_head(code, zone_type):
    game = Game(headless=True)
    game.start_game(2)
    assert not game.snake
    press(game, code)
    assert len(game.aoe_zones) == 1
    assert isinstance(game.aoe_zones[0], zone_type)
    assert tuple(game.aoe_zones[0].pos) == tuple(coord * GRID_SIZE for coord in game.snake1[0])


@pytest.mark.parametrize("players", [1, 2])
def test_reverse_input_is_rejected_on_the_next_real_grid_step(players):
    game = Game(headless=True)
    game.start_game(players)
    game.items.clear()
    snakes = [game.snake] if players == 1 else [game.snake1, game.snake2]
    original = [snake[0] for snake in snakes]
    press(game, pygame.K_a)
    if players == 2:
        press(game, pygame.K_LEFT)
    game.last_update_time -= 1.0
    game.update()
    assert [snake[0] for snake in snakes] == [(x + 1, y) for x, y in original]

    press(game, pygame.K_w)
    if players == 2:
        press(game, pygame.K_DOWN)
    game.last_update_time -= 1.0
    game.update()
    expected = [(original[0][0] + 1, original[0][1] - 1)]
    if players == 2:
        expected.append((original[1][0] + 1, original[1][1] + 1))
    assert [snake[0] for snake in snakes] == expected


@pytest.mark.parametrize(("players", "shooter"), [(1, 1), (2, 2)])
def test_enter_fires_once_for_the_player_in_context(players, shooter):
    game = Game(headless=True)
    game.start_game(players)
    press(game, pygame.K_RETURN)
    assert len(game.flame_projectiles) == 1
    assert [event["player"] for event in game.combat_events
            if event["type"] == "projectile_fired"] == [shooter]


def test_controls_menu_owns_debug_and_navigation_keys_during_capture():
    game = Game(headless=True)
    game.set_state(GameState.CONTROLS)
    press(game, pygame.K_TAB)
    assert game.controls_menu.group == 1
    assert not game.admin_panel.active

    press(game, pygame.K_RETURN)
    press(game, pygame.K_F2)
    assert game.controls_menu.waiting_for_binding
    assert not game.level_editor.active
    press(game, pygame.K_ESCAPE)
    assert game.game_state == GameState.CONTROLS
    assert not game.controls_menu.waiting_for_binding
    press(game, pygame.K_RETURN)
    press(game, pygame.K_r)
    assert game.input.bindings["p2_up"]["key"] == pygame.K_r
    assert not game.aoe_zones
    assert game.game_state == GameState.CONTROLS

    press(game, pygame.K_ESCAPE)
    game.start_game(2)
    press(game, pygame.K_r)
    assert game.next_direction2 == Direction.UP
    assert not game.aoe_zones


def test_remapped_pause_and_special_effect_are_global_gameplay_actions():
    game = Game(headless=True)
    game.start_game(2)
    game.set_state(GameState.BOSS_FIGHT)
    game.input.bind_event("pause", pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F7), save=False)
    game.input.bind_event("special_effect", pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F8), save=False)

    press(game, pygame.K_p)
    assert game.game_state == GameState.BOSS_FIGHT
    press(game, pygame.K_F7)
    assert game.game_state == GameState.PAUSE
    press(game, pygame.K_F8)
    assert not game.aoe_zones
    press(game, pygame.K_F7)
    assert game.game_state == GameState.BOSS_FIGHT
    press(game, 0, "ü")
    assert not game.aoe_zones
    press(game, pygame.K_F8)
    assert isinstance(game.aoe_zones[0], BackgroundEffectZone)


def test_headless_simulator_keys_are_independent_of_player_configuration(tmp_path, monkeypatch):
    path = tmp_path / "controls.json"
    path.write_text(json.dumps({"p1_up": {"key": None}, "p2_fire": {"key": pygame.K_F8}}),
                    encoding="utf-8")
    monkeypatch.setattr("modules.input_manager.user_data_path", lambda _: path)
    game = Game(headless=True)
    assert game.input.bindings["p1_up"]["key"] == pygame.K_w
    assert game.input.bindings["p2_fire"]["key"] == pygame.K_RETURN
