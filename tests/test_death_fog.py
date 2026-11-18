"""Death Transition B: the three approved fog images play only on final death.

Tests check actual rendered composition and timing, not fragile opaque pixels.
"""
import hashlib
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

from modules.death_fog import (
    AbyssFogVisual, FINAL_DEATH_SECONDS, FOG_ASSETS, FOG_STARTS,
    darkness_opacity, layer_opacity,
)
from modules.enums import GameState
from modules.game import Game
from modules.resources import find_asset


ORIGINALS = (
    "Dynamische violettrote Abyss-Nebelschwaden.png",
    "Violett-rote Nebelsturm-Überlagerung.png",
    "Violetter Nebelwirbel mit roten Funken.png",
)


def test_three_real_fog_sources_are_bundled_unchanged():
    root = Path(__file__).resolve().parents[1] / "GamePICs"
    assert len(FOG_ASSETS) == 3
    for asset, name in zip(FOG_ASSETS, ORIGINALS):
        actual = find_asset(*asset)
        original = root / name
        assert actual.is_file() and original.is_file()
        assert hashlib.sha256(actual.read_bytes()).digest() == hashlib.sha256(
            original.read_bytes()
        ).digest()
        assert pygame.image.load(str(actual)).get_width() >= 1024


def test_layers_enter_one_after_another_and_do_not_loop():
    for step in range(3):
        assert layer_opacity(FOG_STARTS[step] - 0.01, step) == 0
        assert layer_opacity(FOG_STARTS[step] + 0.45, step) > 0
        assert layer_opacity(FOG_STARTS[step] + 2, step) > 0
    assert darkness_opacity(0.5) == 0
    assert 0 < darkness_opacity(2.5) < darkness_opacity(2.99) <= 215
    assert FINAL_DEATH_SECONDS == pytest.approx(3.0)


def test_actual_three_fog_images_are_drawn_and_cache_surfaces():
    screen = pygame.Surface((550, 380), pygame.SRCALPHA)
    visual = AbyssFogVisual()
    base = (13, 20, 32)
    screen.fill(base)
    original = pygame.image.tobytes(screen, "RGB")

    visual.draw(screen, 0.3)
    assert pygame.image.tobytes(screen, "RGB") == original
    assert visual._sources is None  # No image I/O before the first visible fog.

    visual.draw(screen, 2.6)
    changed = pygame.image.tobytes(screen, "RGB")
    assert changed != original
    assert all(image is not None for image in visual._sources)
    assert len(visual._layers) == 3
    cached = visual._layers

    screen.fill(base)
    visual.draw(screen, 2.7)
    assert visual._layers is cached  # No resize on subsequent animation frames.

    screen.fill(base)
    visual.draw(screen, FINAL_DEATH_SECONDS + 0.1)
    assert pygame.image.tobytes(screen, "RGB") == original  # No loop.


@pytest.mark.parametrize("players", [1, 2])
def test_regular_respawn_shows_soul_without_starting_fog(players):
    game = Game(headless=True)
    game.start_game(players)
    if players == 1:
        game.player_health = 0
    else:
        game.player_health_p2 = 0
    game.handle_death()
    assert game.respawn.active
    game.draw()
    assert game._death_soul_visual is not None
    assert game._death_fog_visual is None
    assert game.lives == 2


@pytest.mark.parametrize("players", [1, 2])
def test_final_death_fog_layers_freeze_then_hand_over_to_abyss(players):
    game = Game(headless=True)
    game.start_game(players)
    game.lives = 1
    if players == 1:
        game.player_health = 0
    else:
        game.player_health_p2 = 0
    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert game._death_soul_event.final

    game.draw()
    snapshot = game._death_soul_frozen_world
    assert snapshot is not None
    assert game._game_over_visual is None
    game._death_soul_event = replace(
        game._death_soul_event, began_at=time.time() - 2.6
    )
    game.draw()
    assert game._death_fog_visual is not None
    assert game._death_fog_visual._sources is not None
    assert game._death_soul_frozen_world is snapshot
    assert game._game_over_visual is None
    assert game.lives == 0

    game._death_soul_event = replace(
        game._death_soul_event,
        began_at=time.time() - FINAL_DEATH_SECONDS - 0.15,
    )
    game.draw()
    assert game._game_over_visual is not None
    assert game.lives == 0
    assert not game.respawn.active
