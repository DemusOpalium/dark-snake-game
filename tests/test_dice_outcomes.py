import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules import game as game_module
from modules.enums import GameState, ItemType
from modules.game import Game, Item


def test_d20_item_outcomes_cover_every_face(monkeypatch):
    game = Game(headless=True)
    points = (1, 2, 3, 4, 5, 12, 14, 16, 18, 20, 33, 36, 39, 42, 45, 80, 85, 90, 95, 400)
    experience = (0, 0, 0, 0, 0, 3, 3, 4, 4, 5, 11, 12, 13, 14, 15, 32, 34, 36, 38, 0)
    randint = game_module.random.randint
    for roll, expected in enumerate(zip(points, experience), start=1):
        game.start_game(1)
        game.exp_to_next_level = 1000
        lives = game.lives
        monkeypatch.setattr(game_module.random, "randint",
                            lambda a, b: roll if (a, b) == (1, 20) else randint(a, b))

        game.handle_item_pickup(Item(ItemType.DICE_EVENT))

        assert game.dice_result == roll
        assert (game.score, game.experience) == expected, roll
        assert game.lives == lives
        assert (game.game_state is GameState.BOSS_FIGHT) == (roll == 20)


def test_portal_d20_rewards_only_the_upper_half(monkeypatch):
    game = Game(headless=True)
    game.start_game(1)
    randint = game_module.random.randint
    for roll in range(1, 21):
        game.score = 0
        monkeypatch.setattr(game_module.random, "randint",
                            lambda a, b: roll if (a, b) == (1, 20) else randint(a, b))

        game.activate_portal("dice_event")

        assert game.dice_result == roll
        assert game.score == (5 * roll if roll > 10 else 0)
        assert game.experience == 0
