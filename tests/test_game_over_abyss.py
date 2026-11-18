"""Game Over ceremony: actual data, stable callbacks, cached full-window artwork."""
import json
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
from modules.enums import Direction, GameState, ItemType
from modules.game import Game, Item
from modules.game_over_visual import (ABYSS_IMAGE, RITES_FILE, choose_rite,
                                      load_rites)
from modules.resources import find_asset


def test_dark_abyss_art_and_editable_rites_are_bundled_runtime_assets():
    image = find_asset(*ABYSS_IMAGE)
    phrases = find_asset(*RITES_FILE)
    assert image.is_file() and phrases.is_file()
    assert image.stat().st_size > 10_000
    assert pygame.image.load(str(image)).get_size()[0] >= WINDOW_WIDTH // 2
    with phrases.open(encoding="utf-8") as stream:
        catalog = json.load(stream)
    assert catalog["version"] == 1
    assert len(catalog["common"]) >= 3


def test_rite_selection_is_contextual_deterministic_and_safe():
    rites = load_rites()
    context = dict(score=781, level=4, foes=23, relics=6, bosses=2, players=1)
    assert choose_rite(rites, **context) in rites["boss_victor"]
    assert choose_rite(rites, **context) == choose_rite(rites, **context)
    assert choose_rite(rites, **{**context, "players": 2}) in rites["two_player"]
    assert choose_rite(rites, **{**context, "bosses": 0}) in rites["high_level"]
    assert choose_rite(rites, **{**context, "level": 1, "bosses": 0}) in rites["common"]


@pytest.mark.parametrize("players", [1, 2])
@pytest.mark.parametrize("highscore", [True, False])
def test_cinematic_game_over_draws_without_changing_score_or_input(players, highscore):
    game = Game(headless=True)
    game.start_game(players)
    game.score = 1287
    game.level = 7
    game.round_enemies_defeated = 19
    game.round_items_collected = 8
    game.round_bosses_defeated = 1
    game.game_state = GameState.GAME_OVER
    game.leaderboard_mode = highscore
    game.name_input = "DarkTraveler"
    before = (game.score, game.level, game.player_count, game.name_input,
              game.round_enemies_defeated, game.round_items_collected,
              game.round_bosses_defeated)

    game.draw()
    image = game._game_over_visual._image_for(game.screen.get_size())
    assert game._game_over_visual._image is not None
    assert image.get_size() == (WINDOW_WIDTH, WINDOW_HEIGHT)
    # Outside the ceremony panel and interactives, every pixel is image art,
    # not the old HUD nor the paused game world.
    for x, y in ((12, 80), (WINDOW_WIDTH - 12, 80), (12, 760)):
        assert game.screen.get_at((x, y))[:3] == image.get_at((x, y))[:3]
    assert before == (game.score, game.level, game.player_count, game.name_input,
                      game.round_enemies_defeated, game.round_items_collected,
                      game.round_bosses_defeated)
    original_backdrop = game._game_over_visual._backdrop
    original_panel = game._game_over_visual._panel
    game.draw()
    assert game._game_over_visual._backdrop is original_backdrop
    assert game._game_over_visual._panel is original_panel


def test_round_statistics_count_real_items_enemies_and_reset():
    game = Game(headless=True)
    game.start_game(1)
    assert (game.round_items_collected, game.round_enemies_defeated,
            game.round_bosses_defeated) == (0, 0, 0)

    game.snake = [(10, 10)]
    food = Item(ItemType.FOOD)
    food.x, food.y = 11, 10
    game.items = [food]
    assert game._move_snake(1, game.snake, Direction.RIGHT, False)
    assert game.round_items_collected == 1

    class Target:
        health = 1
        spawn_time = time.time() - 10
        def get_hitbox(self):
            return pygame.Rect(200, 200, 30, 30)
    class Flame:
        damage = 2
        def get_hitbox(self):
            return pygame.Rect(200, 200, 30, 30)
    game.enemies = [Target()]
    assert game._resolve_fireball_hit(Flame()) == "enemy"
    assert game.round_enemies_defeated == 1
    assert not game.enemies

    game.start_game(1)
    assert (game.round_items_collected, game.round_enemies_defeated,
            game.round_bosses_defeated) == (0, 0, 0)


def test_game_over_controls_keep_original_actions_and_callback_areas():
    game = Game(headless=True)
    game.start_game(1)
    buttons = game.game_over_buttons
    assert [b.text for b in buttons] == ["NEUSTART", "HAUPTMENÜ"]
    assert buttons[0].rect.colliderect(buttons[1].rect) is False
    game.game_state = GameState.GAME_OVER
    buttons[0].check_hover(buttons[0].rect.center)
    buttons[0].handle_event(pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": buttons[0].rect.center}))
    assert game.game_state in (GameState.GAME, GameState.BOSS_FIGHT)
