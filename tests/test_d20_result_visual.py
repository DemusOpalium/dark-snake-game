"""Behavior-first checks for the revamped D20 result display.

Both classic item and portal rolls use one card with a dynamic 1..20 number.
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

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from modules.dice_visual import FrostDiceResultVisual, outcome_for_roll
from modules.game import Game


@pytest.mark.parametrize(
    ("roll", "label", "hint"),
    [
        (1, "KRITISCHER", "FEHLSCHLAG"),
        (5, "FEHLSCHLAG", "NEUER VERSUCH"),
        (6, "KLEINER ERFOLG", "WURF BESTÄTIGT"),
        (10, "KLEINER ERFOLG", "WURF BESTÄTIGT"),
        (11, "ERFOLG", "WURF BESTÄTIGT"),
        (15, "ERFOLG", "WURF BESTÄTIGT"),
        (16, "GROSSER ERFOLG", "SELTENER WURF"),
        (19, "GROSSER ERFOLG", "SELTENER WURF"),
        (20, "KRITISCHER", "ERFOLG"),
    ],
)
def test_dice_outcome_categories_have_distinct_readable_styles(roll, label, hint):
    title, info, accent = outcome_for_roll(roll)
    assert (title, info) == (label, hint)
    assert len(accent) == 3 and all(0 <= value <= 255 for value in accent)


@pytest.mark.parametrize("roll", [1, 6, 10, 12, 16, 19, 20])
def test_d20_panel_renders_each_roll_and_caches_its_art(roll):
    screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    background = (8, 15, 25)
    screen.fill(background)
    visual = FrostDiceResultVisual()
    visual.draw(screen, roll, now=100.0)

    rect = visual.card_rect(screen)
    assert rect.top > WINDOW_HEIGHT // 2 - 60
    assert rect.bottom < WINDOW_HEIGHT
    assert screen.get_at(rect.center)[:3] != background
    assert screen.get_at((rect.left - 2, rect.centery))[:3] == background

    card = visual._cards[roll]
    screen.fill(background)
    visual.draw(screen, roll, now=101.0)
    assert visual._cards[roll] is card  # No re-render at 60 fps.


def test_failed_and_critical_win_appear_visually_different():
    visual = FrostDiceResultVisual()
    failures = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    wins = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    failures.fill((8, 15, 25))
    wins.fill((8, 15, 25))
    visual.draw(failures, 1, now=100.0)
    visual.draw(wins, 20, now=100.0)

    rect = visual.card_rect(wins)
    assert pygame.image.tobytes(failures.subsurface(rect), "RGB") != pygame.image.tobytes(
        wins.subsurface(rect), "RGB"
    )


@pytest.mark.parametrize("players", [1, 2])
def test_real_game_draw_uses_new_card_with_old_d20_banner(players):
    game = Game(headless=True)
    game.start_game(players)
    game.dice_result = 19
    game.dice_display_until = time.time() + 5
    old_score = game.score
    game.draw()

    assert game._dice_banner is not None
    assert game._dice_visual is not None
    assert 19 in game._dice_visual._cards
    assert game.score == old_score
    banner = game._dice_banner.get_rect(
        midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60)
    )
    card = game._dice_visual.card_rect(game.screen)
    assert banner.bottom < card.top


def test_panel_softly_fades_at_end_of_five_second_roll():
    visual = FrostDiceResultVisual()
    screen_early = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    screen_late = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    screen_early.fill((8, 15, 25))
    screen_late.fill((8, 15, 25))
    visual.draw(screen_early, 20, display_until=10.0, now=9.0)
    visual.draw(screen_late, 20, display_until=10.0, now=9.99)

    rect = visual.card_rect(screen_late)
    # At least the central opaque panel changes as it dissolves.
    assert pygame.image.tobytes(screen_early.subsurface(rect), "RGB") != pygame.image.tobytes(
        screen_late.subsurface(rect), "RGB"
    )
    assert visual._cards[20].get_alpha() == 255
