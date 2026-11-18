"""Regression checks for Soul of the Fallen (the first Death Transition layer).

The three abyss fog assets are deliberately NOT used by this PR.
"""
import os
import sys
import time
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE, WINDOW_HEIGHT, WINDOW_WIDTH
from modules.death_soul import (DeathSoulEvent, DeathSoulVisual, FRAME_COUNT,
                                SIZES, SOUL_ART, SOUL_SECONDS)
from modules.enums import GameState
from modules.game import Game
from modules.resources import find_asset


def test_soul_is_real_bundled_png_not_only_staged_art():
    game_asset = find_asset(*SOUL_ART)
    original = Path(__file__).resolve().parents[1] / "GamePICs" / "Geisterschlange im Seelensturm.png"
    assert game_asset.is_file()
    assert original.is_file()
    assert game_asset.read_bytes() == original.read_bytes()
    assert pygame.image.load(str(game_asset)).get_width() >= 240


def test_one_shot_frame_order_and_size_progression():
    renderer = DeathSoulVisual()
    assert tuple(renderer.target_size(n) for n in (1, 2, 3)) == SIZES
    assert renderer.frame_index(0) == 0
    assert renderer.frame_index(SOUL_SECONDS * 0.5) > 0
    assert renderer.frame_index(SOUL_SECONDS) == FRAME_COUNT - 1
    event = DeathSoulEvent(((350, 280),), 1, 100.0, False)
    screen = pygame.Surface((710, 560), pygame.SRCALPHA)
    screen.fill((8, 14, 23))
    before = pygame.image.tobytes(screen, "RGB")
    renderer.draw(screen, event, 0.85)
    assert pygame.image.tobytes(screen, "RGB") != before
    assert len(renderer._frames) == 1
    renderer.draw(screen, event, 0.85)
    assert len(renderer._frames) == 1  # No new resize for same animation frame.
    screen.fill((8, 14, 23))
    renderer.draw(screen, event, SOUL_SECONDS + 0.01)
    assert pygame.image.tobytes(screen, "RGB") == before  # One-shot, no looping.


@pytest.mark.parametrize("players", [1, 2])
def test_health_death_uses_original_head_before_respawn(players):
    game = Game(headless=True)
    game.start_game(players)
    if players == 1:
        game.snake = [(4, 7)]
        game.player_health = 0
        expected = ((4.5 * GRID_SIZE, 7.5 * GRID_SIZE),)
    else:
        game.snake1 = [(2, 5)]
        game.snake2 = [(10, 8)]
        game.player_health_p1 = 100
        game.player_health_p2 = 0
        expected = ((10.5 * GRID_SIZE, 8.5 * GRID_SIZE),)
    game.handle_death()

    death = game._death_soul_event
    assert death is not None
    assert death.centers == expected
    assert (death.tier, death.final) == (1, False)
    assert game.lives == 2
    assert game.respawn.active
    assert game.game_state != GameState.GAME_OVER
    # A different safe spawn location cannot move the soul itself.
    game.draw()
    assert game._death_soul_visual is not None


def test_stall_death_selects_blocked_p2_not_arbitrary_p1():
    game = Game(headless=True)
    game.start_game(2)
    game.snake1 = [(3, 3)]
    game.snake2 = [(16, 17)]
    game._blocked_since = {2: time.monotonic() - 4}
    game.handle_self_collision()

    assert game._death_soul_event.centers == ((16.5 * GRID_SIZE, 17.5 * GRID_SIZE),)
    assert game.respawn.active
    assert game.lives == 2


def test_sequential_life_losses_grow_soul_but_do_not_modify_respawn_rules():
    game = Game(headless=True)
    game.start_game(1)
    tiers = []
    for current_lives in (3, 2):
        game.lives = current_lives
        game.respawn.clear()  # Simulate the previous countdown finishing.
        game.snake = [(8, 9)]
        game.player_health = 0
        game.handle_death()
        tiers.append(game._death_soul_event.tier)
        assert game.respawn.active
        assert game.lives == current_lives - 1
    assert tiers == [1, 2]


def test_final_life_freezes_real_world_then_yields_to_dark_abyss():
    game = Game(headless=True)
    game.start_game(1)
    game.snake = [(12, 8)]
    game.lives = 1
    game.player_health = 0
    game.handle_death()
    event = game._death_soul_event

    assert game.game_state == GameState.GAME_OVER
    assert not game.respawn.active
    assert event.final
    assert event.tier == 3  # Every final death uses the largest soul.
    game.draw()
    assert game._death_soul_frozen_world is not None
    frozen = game._death_soul_frozen_world
    game.draw()
    assert game._death_soul_frozen_world is frozen
    assert game._game_over_visual is None  # No immediate cut to the Abyss.

    # Advance the original event without sleeping or updating gameplay.
    game._death_soul_event = replace(
        event, began_at=time.time() - SOUL_SECONDS - 0.1
    )
    game.draw()
    assert game._game_over_visual is not None
    assert game.lives == 0
    assert not game.respawn.active


def test_new_game_clears_prior_soul_and_frozen_screen():
    game = Game(headless=True)
    game.start_game(1)
    game.player_health = 0
    game.handle_death()
    assert game._death_soul_event is not None
    game.start_game(1)
    assert game._death_soul_event is None
    assert game._death_soul_frozen_world is None
    assert game.round_death_count == 0
    assert game.lives == 3


def test_final_2p_soul_only_uses_actually_fallen_player():
    game = Game(headless=True)
    game.start_game(2)
    game.snake1 = [(8, 8)]
    game.snake2 = [(11, 12)]
    game.lives = 1
    game.player_health_p1 = 100
    game.player_health_p2 = -20
    game.handle_death()
    assert game._death_soul_event.centers == (
        (11.5 * GRID_SIZE, 12.5 * GRID_SIZE),
    )
    assert game.game_state == GameState.GAME_OVER
