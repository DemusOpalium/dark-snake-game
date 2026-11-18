"""The life HUD follows chosen snake skins without storing duplicate icon state."""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from config import WINDOW_WIDTH
from modules.game import Game


def solid_head(color):
    image = pygame.Surface((60, 60), pygame.SRCALPHA)
    image.fill((*color, 255))
    return image


def test_single_player_life_icons_follow_selected_skin_and_remaining_lives(monkeypatch):
    game = Game(headless=True)
    game.start_game(1)
    heads = {
        "green.png": solid_head((27, 225, 80)),
        "blue.png": solid_head((35, 105, 227)),
    }
    monkeypatch.setattr(
        game.options_menu, "get_skin_image", lambda tab, name: heads.get(name)
    )

    game.settings["custom_head_p1"] = "green.png"
    game.lives = 3
    game.screen.fill((0, 0, 0))
    game.draw_hud()
    for i in range(3):
        assert game.screen.get_at((WINDOW_WIDTH - 26 - 34 * i, 25))[:3] == (27, 225, 80)

    # Changing the existing selection changes the display automatically;
    # no new life-skin setting or registration is required.
    game.settings["custom_head_p1"] = "blue.png"
    game.lives = 1
    game.screen.fill((0, 0, 0))
    game.draw_hud()
    assert game.screen.get_at((WINDOW_WIDTH - 26, 25))[:3] == (35, 105, 227)
    assert game.screen.get_at((WINDOW_WIDTH - 60, 25))[:3] == (0, 0, 0)


def test_two_player_shows_distinct_selected_heads_and_preserves_shared_lives(monkeypatch):
    game = Game(headless=True)
    game.start_game(2)
    heads = {
        "green.png": solid_head((27, 225, 80)),
        "blue.png": solid_head((35, 105, 227)),
    }
    monkeypatch.setattr(
        game.options_menu, "get_skin_image", lambda tab, name: heads.get(name)
    )
    game.settings["custom_head_p1"] = "green.png"
    game.settings["custom_head_p2"] = "blue.png"
    game.lives = 2
    game.player_health_p1 = 68
    game.player_health_p2 = 36
    game.screen.fill((0, 0, 0))

    game.draw_hud()

    assert game.screen.get_at((245, 93))[:3] == (27, 225, 80)
    assert game.screen.get_at((WINDOW_WIDTH - 245, 93))[:3] == (35, 105, 227)
    assert (game.lives, game.player_health_p1, game.player_health_p2) == (2, 68, 36)
    # Player health bars remain at their independent, original coordinates.
    assert game.screen.get_at((22, 85))[:3] != (0, 0, 0)
    assert game.screen.get_at((WINDOW_WIDTH - 218, 85))[:3] != (0, 0, 0)


def test_missing_selected_head_uses_existing_fallback(monkeypatch):
    game = Game(headless=True)
    game.start_game(1)
    game.settings["custom_head_p1"] = "deleted.png"
    monkeypatch.setattr(game.options_menu, "get_skin_image", lambda *_: None)
    game.screen.fill((0, 0, 0))

    game.draw_hud()  # Must not crash when a saved asset is no longer present.

    assert game.screen.get_at((WINDOW_WIDTH - 41, 22))[:3] == (153, 123, 186)
