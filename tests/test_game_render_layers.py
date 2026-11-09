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

from config import DARK_GREY, RED, WHITE
from modules.enums import GameState
from modules.game import Game


EFFECT_COLOR = (48, 192, 144)


def assert_region(surface, rect, color):
    region = surface.subsurface(rect)
    expected = pygame.Surface(region.get_size(), pygame.SRCALPHA)
    expected.fill(color)
    assert pygame.image.tobytes(region, "RGB") == pygame.image.tobytes(expected, "RGB")


def assert_bar(surface, x, fill_width, fill_color):
    assert_region(surface, (x + 8, 80, 30, 2), WHITE)
    assert_region(surface, (x + 2, 84, fill_width - 2, 12), fill_color)
    assert_region(surface, (x + fill_width, 84, 198 - fill_width, 12), DARK_GREY)


def prepare_world(players):
    game = Game(headless=True)
    game.start_game(players)
    game.items.clear()
    game.achievement_messages.clear()
    game.background.fill((15, 23, 35))
    game.player_health = 25
    game.player_health_p1 = 75
    game.player_health_p2 = 60
    # The opaque world sprite spans the left bar and remains visible beside it.
    marker = pygame.Surface((260, 40), pygame.SRCALPHA)
    marker.fill(EFFECT_COLOR)
    effect = game.effect_manager.spawn("render_regression_marker", (130, 95), {"layer": "world"})
    effect.frames = [marker]
    return game


@pytest.mark.parametrize("players", [1, 2])
@pytest.mark.parametrize(("state", "shade"), [
    (GameState.GAME, 0),
    (GameState.PAUSE, 180),
    (GameState.GAME_OVER, 200),
])
def test_game_draw_composites_world_then_screen_overlay_then_hud(players, state, shade):
    game = prepare_world(players)
    game.game_state = state
    game.draw()

    screen = game.screen
    if players == 1:
        assert_bar(screen, 20, 50, (255, 127, 0))
    else:
        assert_bar(screen, 20, 150, (127, 255, 0))
        assert_bar(screen, screen.get_width() - 220, 120, (0, 128, 255))

    # The pause/game-over shade darkens the world but leaves the HUD at full color.
    expected = pygame.Surface((1, 1), pygame.SRCALPHA)
    expected.fill(EFFECT_COLOR)
    overlay = pygame.Surface((1, 1), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, shade))
    expected.blit(overlay, (0, 0))
    assert_region(screen, (230, 86, 20, 12), expected.get_at((0, 0)))
    assert_region(screen, (screen.get_width() - 34, 16, 18, 18), RED)
    score_area = screen.subsurface((20, 10, 145, 31))
    assert pygame.mask.from_threshold(score_area, WHITE, (1, 1, 1, 255)).count() > 0


def test_draw_game_keeps_hud_for_direct_callers():
    game = prepare_world(1)
    game.draw_game()
    assert_bar(game.screen, 20, 50, (255, 127, 0))
    assert_region(game.screen, (230, 86, 20, 12), EFFECT_COLOR)
