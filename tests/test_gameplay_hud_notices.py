"""Regression checks for gameplay HUD notices and the dice caption.

The playfield is intentionally unchanged: only notice placements are tested.
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

from config import WINDOW_HEIGHT, WINDOW_WIDTH, WHITE
from modules.game import Game, draw_health_bar_two


@pytest.mark.parametrize("players", [1, 2])
def test_achievement_notices_do_not_cover_health_bars(players):
    game = Game(headless=True)
    game.start_game(players)
    game.screen.fill((9, 18, 29))
    if players == 1:
        game.player_health = 45
        game.draw_health_bar()
        health_regions = [(20, 80, 200, 20)]
    else:
        game.player_health_p1 = 75
        game.player_health_p2 = 30
        draw_health_bar_two(game)
        health_regions = [(20, 80, 200, 20), (WINDOW_WIDTH - 220, 80, 200, 20)]

    expected = [
        pygame.image.tobytes(game.screen.subsurface(rect), "RGB")
        for rect in health_regions
    ]
    for message in ("Enemy roasted!", "Level 3 erreicht!", "Multi-Shoot aktiviert!",
                    "Boss Down Easy Going !!", "Enemy roasted!", "Loot Boost!"):
        game.add_achievement(message)
    game.portal_effect_active = True
    game.portal_effect_type = "loot"

    game.achievement_manager.draw_achievements(game.screen)
    game.achievement_manager.draw_portal_event(game.screen)

    actual = [
        pygame.image.tobytes(game.screen.subsurface(rect), "RGB")
        for rect in health_regions
    ]
    assert actual == expected
    # Both notice groups remain visible below the player health bars.
    assert game.screen.get_at((14, 145))[:3] != (9, 18, 29)
    assert game.screen.get_at((WINDOW_WIDTH - 14, 145))[:3] != (9, 18, 29)


def test_achievement_expiry_is_preserved_without_overlaying_hud():
    game = Game(headless=True)
    game.start_game(1)
    game.achievement_messages = [("Expired", time.time() - 1), ("Visible", time.time() + 10)]
    game.screen.fill((9, 18, 29))

    game.achievement_manager.draw_achievements(game.screen)

    assert [text for text, _ in game.achievement_messages] == ["Visible"]
    # The area occupied by the health bar is still pristine.
    assert game.screen.get_at((30, 90))[:3] == (9, 18, 29)


def test_dice_result_card_fits_below_the_existing_d20_banner():
    game = Game(headless=True)
    game.dice_result = 6
    game.screen.fill((9, 18, 29))
    game.draw_dice_result()

    visual = game._dice_visual
    assert visual is not None
    card = visual.card_rect(game.screen)
    banner = game._dice_banner.get_rect(
        midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60)
    )
    assert card.top > banner.bottom
    assert card.left >= 0 and card.right <= WINDOW_WIDTH
    assert card.bottom <= WINDOW_HEIGHT
    # Real game pixels are drawn in the new result card, not the old solid box.
    assert game.screen.get_at((card.left + 22, card.top + 22))[:3] != (9, 18, 29)
    assert game.screen.get_at((card.left - 2, card.top + 22))[:3] == (9, 18, 29)
