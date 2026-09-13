import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from config import WINDOW_HEIGHT, WINDOW_WIDTH
from modules.enums import Direction, GameState
from modules.game import Game
from modules.input_manager import InputManager
from modules.resources import asset_path
from modules.graphics import ENEMY_TIM_IMG, SNAKE_HEAD_IMG, TITLE_IMG


def _has_visible_pixel(surface):
    return pygame.mask.from_surface(surface, threshold=0).count() > 0


def test_assets_resolve_from_repository_root():
    assert Path(asset_path("graphics", "titel1.png")).is_file()


def test_critical_graphics_are_loaded_and_visible():
    assert Path(asset_path("graphics", "SnakeHeadAlpha1.png")).is_file()
    assert Path(asset_path("graphics", "gegner-TimG40.png")).is_file()
    assert all(_has_visible_pixel(image) for image in
               (TITLE_IMG, SNAKE_HEAD_IMG, ENEMY_TIM_IMG))


def test_menu_draw_and_keyboard_start():
    game = Game()
    assert game.game_state is GameState.INTRO
    game.draw()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
    game.handle_events()
    assert game.game_state is GameState.GAME
    assert game.player_count == 1 and game.snake and not game.snake1


def test_headless_game_uses_offscreen_surface_without_changing_display(monkeypatch):
    display_surface = pygame.display.get_surface()
    monkeypatch.setattr(
        pygame.display, "set_mode",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("headless must not create a display")
        ),
    )

    game = Game(headless=True)

    assert isinstance(game.screen, pygame.Surface)
    assert game.screen.get_size() == (WINDOW_WIDTH, WINDOW_HEIGHT)
    assert pygame.display.get_surface() is display_surface


def test_two_player_reset_and_keyboard_input():
    game = Game()
    game.start_game(2)
    assert game.snake1 and game.snake2 and not game.snake
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w, unicode="w"))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, unicode=""))
    game.handle_events()
    assert game.next_direction1 is Direction.UP
    # A direct 180-degree reversal from RIGHT to LEFT must be rejected.
    assert game.next_direction2 is Direction.RIGHT
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, unicode=""))
    game.handle_events()
    assert game.next_direction2 is Direction.UP


def test_round_is_fully_cleared_when_returning_to_main_menu():
    game = Game()
    game.start_game(1)
    game.enemies.append(object())
    game.lives = 2

    game.set_state(GameState.INTRO)

    assert not game.snake and not game.snake1 and not game.snake2
    assert not game.items and not game.enemies and game.boss is None
    assert game.lives == 0 and game.player_health == 0
    assert game.background is game.level_background_surface


def test_gamepad_button_hat_axis_and_persistence(tmp_path):
    path = tmp_path / "controls.json"
    manager = InputManager(path, initialize_joysticks=False)
    manager.bind_event("p1_fire", pygame.event.Event(pygame.JOYBUTTONDOWN, joy=0, button=3))
    assert "p1_fire" in InputManager(path, False).actions_for(
        pygame.event.Event(pygame.JOYBUTTONDOWN, joy=0, button=3)
    )
    assert "p2_left" in manager.actions_for(
        pygame.event.Event(pygame.JOYHATMOTION, joy=1, value=(-1, 0))
    )
    assert "p1_down" in manager.actions_for(
        pygame.event.Event(pygame.JOYAXISMOTION, joy=0, axis=1, value=0.8)
    )
