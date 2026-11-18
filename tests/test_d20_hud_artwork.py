"""The user's existing Random D20 banner is visible for every roll.

A single image is reused; the result and outcome text remain dynamic.
"""
import hashlib
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

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from modules.game import Game
from modules.resources import find_asset

BANNER_NAME = "Random_D20-removebg-preview.png"
BANNER = Path(find_asset("graphics", "hud", BANNER_NAME))
SOURCE = Path(__file__).resolve().parents[1] / "GamePICs" / "Miscellaneos" / BANNER_NAME
BACKGROUND = (9, 17, 33)


def test_d20_uses_the_original_artwork_in_runtime_assets():
    assert BANNER.is_file()
    assert SOURCE.is_file()
    assert hashlib.sha256(BANNER.read_bytes()).digest() == hashlib.sha256(SOURCE.read_bytes()).digest()
    assert pygame.image.load(str(BANNER)).get_width() > 330


@pytest.mark.parametrize("roll", [1, 6, 10, 12, 19, 20])
def test_d20_render_shows_original_banner_and_dynamic_roll(roll):
    game = Game(headless=True)
    game.dice_result = roll
    game.screen.fill(BACKGROUND)

    game.draw_dice_result()

    art = pygame.image.load(str(BANNER)).convert_alpha()
    banner = pygame.transform.smoothscale(art, (330, 51))
    rect = banner.get_rect(midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
    expected = pygame.Surface(rect.size)
    expected.fill(BACKGROUND)
    expected.blit(banner, (0, 0))
    # Verify the real image is composited, not a drawn rectangular placeholder.
    assert pygame.image.tobytes(game.screen.subsurface(rect), "RGB") == pygame.image.tobytes(expected, "RGB")
    assert game._dice_banner is not None

    cached = game._dice_banner
    game.dice_result = 7 if roll != 7 else 8
    game.screen.fill(BACKGROUND)
    game.draw_dice_result()
    assert game._dice_banner is cached


def test_dice_pickup_shows_banner_in_actual_game_draw(monkeypatch):
    from modules import game as game_module
    from modules.enums import ItemType
    from modules.game import Item

    game = Game(headless=True)
    game.start_game(1)
    game.exp_to_next_level = 1000
    original_randint = game_module.random.randint
    monkeypatch.setattr(
        game_module.random, "randint",
        lambda low, high: 12 if (low, high) == (1, 20) else original_randint(low, high),
    )
    game.handle_item_pickup(Item(ItemType.DICE_EVENT))
    assert game.dice_result == 12
    assert game._dice_banner is None

    game.draw()

    assert game._dice_banner is not None
    banner_rect = game._dice_banner.get_rect(midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
    region = game.screen.subsurface(banner_rect)
    assert pygame.mask.from_surface(region).count() > 0
