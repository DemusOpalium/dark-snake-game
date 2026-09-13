import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules.game import Game


def test_portal_expiry_without_custom_level_restores_default_background():
    game = Game()
    assert not hasattr(game, "level_map")
    expected_pixel = game.level_background_surface.get_at((0, 0))

    game.background.fill((1, 2, 3))
    game.portal_effect_active = True
    game.portal_effect_end = time.time() - 1
    game.update()

    assert not game.portal_effect_active
    assert game.background.get_at((0, 0)) == expected_pixel


def test_portal_expiry_keeps_custom_editor_background():
    game = Game()
    game.level_map = [[None]]
    assert game.build_background_from_map()
    custom_surface = game.level_background_surface

    game.background.fill((1, 2, 3))
    game.portal_effect_active = True
    game.portal_effect_end = time.time() - 1
    game.update()

    assert game.background is game.level_background_surface
    assert game.background is not custom_surface
