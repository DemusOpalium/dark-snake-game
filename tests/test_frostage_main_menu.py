"""FrostAge menu integration through the real Pygame event queue."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules import resources
from modules.enums import GameState
from modules.frostage_assets import frostage_assets, load_frostage_image
from modules.game import Game
from modules.main_menu import FrostAgeMenu, cover_background, load_frostage_background


ART_KEYS = {
    "single_player", "multiplayer", "continue", "options", "highscore",
    "level_studio", "workshop", "boss_rush", "inventory", "statistics",
    "credits", "quit",
}
UNAVAILABLE_KEYS = {"workshop", "boss_rush", "inventory", "statistics", "credits"}


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game.main_menu.layout(game.screen.get_size())
    pygame.event.clear()
    return game


def send(game, event_type, **attrs):
    pygame.event.post(pygame.event.Event(event_type, **attrs))
    game.handle_events()


def press(game, key):
    send(game, pygame.KEYDOWN, key=key, unicode="")


def entry(menu, key):
    return next(button for button in menu.buttons if button.key == key)


def click_at(game, pos, *, button=1):
    send(game, pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


def click_menu(game, key):
    click_at(game, entry(game.main_menu, key).rect.center)


def open_main_menu_from_pause(game):
    press(game, pygame.K_p)
    assert game.game_state is GameState.PAUSE
    pause_to_menu = next(button for button in game.pause_buttons if button.text == "HAUPTMENÜ")
    click_at(game, pause_to_menu.rect.center)
    assert game.game_state is GameState.INTRO
    assert game.can_continue() and game.main_menu.is_enabled("continue")


def test_all_frostage_menu_pngs_are_assigned_and_preserve_proportions(game):
    menu = game.main_menu
    assets = frostage_assets()
    for width, height in ((900, 620), (1350, 930)):
        surface = pygame.Surface((width, height))
        menu.draw(surface)
        assert {button.key for button in menu.buttons if button.asset_id} == ART_KEYS
        for button in menu.buttons:
            assert surface.get_rect().contains(button.rect)
            assert button.rect.width > 0 and button.rect.height > 0
            if button.asset_id is None:
                continue
            assert button.asset_id == f"frostage_menu_{button.key}"
            asset = assets[button.asset_id]
            image = load_frostage_image(button.asset_id)
            assert image is not None and image.get_size() == (asset.width, asset.height)
            assert button.image is not None and button.image.get_size() == button.rect.size
            expected_height = button.rect.width * asset.height / asset.width
            assert button.rect.height == pytest.approx(expected_height, abs=1.5)


def test_cover_background_crops_centrally_without_stretch_or_side_bars():
    source = pygame.Surface((12, 4))
    source.fill((60, 210, 90))
    source.fill((220, 50, 30), (0, 0, 3, 4))
    source.fill((40, 100, 230), (9, 0, 3, 4))

    cropped = cover_background(source, (8, 8))

    assert cropped.get_size() == (8, 8)
    assert cropped.get_at((0, 0))[:3] == (60, 210, 90)
    assert cropped.get_at((7, 7))[:3] == (60, 210, 90)
    assert source.get_at((0, 0))[:3] == (220, 50, 30)


def test_game_uses_packaged_frostage_title_background(game):
    path = resources.find_asset("graphics", "menu", "frostage_title_background.png")
    assert path.is_file()
    source = pygame.image.load(str(path))
    active = game.main_menu._background_source
    assert active is not None
    assert active.get_size() == source.get_size()
    assert active.get_at((0, 0))[:3] == source.get_at((0, 0))[:3]
    assert game.main_menu.background.get_size() == game.screen.get_size()


def test_frostage_background_falls_back_if_the_asset_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.main_menu.find_asset", lambda *parts: tmp_path / "missing.png")
    legacy = pygame.Surface((11, 17))
    assert load_frostage_background(legacy) is legacy


def test_main_menu_background_is_cached_per_viewport_size():
    background = pygame.Surface((320, 180))
    background.fill((100, 80, 70))
    menu = FrostAgeMenu({}, can_continue=lambda: False, background=background)
    menu.layout((900, 620))
    cached = menu.background
    assert cached.get_size() == (900, 620)
    menu.draw(pygame.Surface((900, 620)))
    assert menu.background is cached
    menu.layout((1350, 930))
    assert menu.background is not cached
    assert menu.background.get_size() == (1350, 930)


@pytest.mark.parametrize("key, player_count", [("single_player", 1), ("multiplayer", 2)])
def test_clicking_play_art_starts_the_matching_classic_round(game, key, player_count):
    assert game.game_state is GameState.INTRO and not game.can_continue()
    click_menu(game, key)
    assert game.game_state is GameState.GAME and game.player_count == player_count
    snakes = (game.snake,) if player_count == 1 else (game.snake1, game.snake2)
    assert all(snakes) and game.score == 0 and game.lives == 3


@pytest.mark.parametrize(("key", "target"), [
    ("options", GameState.SETTINGS),
    ("highscore", GameState.LEADERBOARD),
    ("controls", GameState.CONTROLS),
    ("developer", GameState.SIMULATION),
])
def test_menu_keeps_existing_destinations(game, key, target):
    assert game.main_menu.is_enabled(key)
    click_menu(game, key)
    assert game.game_state is target


def test_level_studio_button_opens_existing_editor_and_escape_returns(game):
    click_menu(game, "level_studio")
    assert game.game_state is GameState.INTRO and game.level_editor.active
    press(game, pygame.K_ESCAPE)
    assert game.game_state is GameState.INTRO and not game.level_editor.active
    click_menu(game, "single_player")
    assert game.game_state is GameState.GAME


def test_quit_art_calls_existing_exit_action(game):
    with pytest.raises(SystemExit):
        click_menu(game, "quit")


def test_unavailable_art_and_fresh_continue_do_not_dispatch(game):
    menu = game.main_menu
    assert not game.can_continue()
    for key in UNAVAILABLE_KEYS | {"continue"}:
        assert not menu.is_enabled(key)
        click_menu(game, key)
        assert game.game_state is GameState.INTRO
    assert not game.snake and not game.snake1 and not game.snake2


def test_mouse_hover_draws_feedback_without_stealing_keyboard_focus(game):
    menu = game.main_menu
    options = entry(menu, "options").rect
    disabled = entry(menu, "continue").rect

    def rendered_region(rect):
        game.draw()
        return pygame.image.tostring(game.screen.subsurface(rect.inflate(8, 6)), "RGB")

    idle_options = rendered_region(options)
    idle_disabled = rendered_region(disabled)
    send(game, pygame.MOUSEMOTION, pos=options.center, rel=(0, 0), buttons=(0, 0, 0))
    assert rendered_region(options) != idle_options
    assert menu.focus == "single_player"

    send(game, pygame.MOUSEMOTION, pos=disabled.center, rel=(0, 0), buttons=(0, 0, 0))
    assert rendered_region(options) == idle_options
    assert rendered_region(disabled) == idle_disabled


def test_keyboard_focus_skips_disabled_entries_and_return_dispatches(game):
    menu = game.main_menu
    assert menu.focus == "single_player"
    press(game, pygame.K_DOWN)
    assert menu.focus != "single_player" and menu.is_enabled(menu.focus)
    press(game, pygame.K_UP)
    assert menu.focus == "single_player"
    press(game, pygame.K_RETURN)
    assert game.game_state is GameState.GAME and game.player_count == 1


def test_mapped_controller_hat_and_button_navigate_and_activate(game, monkeypatch):
    controller = SimpleNamespace(init=lambda: None, get_instance_id=lambda: 71,
                                 get_guid=lambda: "test-gamepad", get_name=lambda: "Test Gamepad")
    monkeypatch.setattr(pygame.joystick, "Joystick", lambda _: controller)
    send(game, pygame.JOYDEVICEADDED, device_index=0)
    assert game.main_menu.focus == "single_player"
    send(game, pygame.JOYHATMOTION, instance_id=71, joy=0, hat=0, value=(0, -1))
    assert game.main_menu.focus != "single_player" and game.main_menu.is_enabled(game.main_menu.focus)
    send(game, pygame.JOYHATMOTION, instance_id=71, joy=0, hat=0, value=(0, 0))
    send(game, pygame.JOYHATMOTION, instance_id=71, joy=0, hat=0, value=(0, 1))
    assert game.main_menu.focus == "single_player"
    send(game, pygame.JOYBUTTONDOWN, instance_id=71, joy=0, button=0)
    assert game.game_state is GameState.GAME and game.player_count == 1


@pytest.mark.parametrize("boss_round", [False, True])
def test_pause_to_menu_continue_preserves_real_round_after_submenu(game, boss_round):
    click_menu(game, "single_player")
    if boss_round:
        assert game.start_boss_fight()
    original_state = game.game_state
    boss = game.boss
    game.score, game.player_health, game.lives = 172, 61, 2
    x, y = game.snake[0]
    game.snake.append((x - 1, y))
    snake = game.snake.copy()
    items = game.items.copy()

    open_main_menu_from_pause(game)
    game.run_frame()
    assert game.snake == snake and game.items == items

    click_menu(game, "options")
    assert game.game_state is GameState.SETTINGS
    press(game, pygame.K_ESCAPE)
    assert game.game_state is GameState.INTRO and game.can_continue()

    click_menu(game, "level_studio")
    assert game.level_editor.active
    press(game, pygame.K_ESCAPE)
    assert not game.level_editor.active and game.can_continue()

    click_menu(game, "continue")
    assert game.game_state is original_state and game.boss is boss
    assert game.snake == snake and game.items == items
    assert (game.score, game.player_health, game.lives) == (172, 61, 2)


def test_multiplayer_round_survives_highscore_back_button_and_continue(game):
    click_menu(game, "multiplayer")
    game.score, game.lives = 293, 2
    game.player_health_p1, game.player_health_p2 = 42, 79
    snakes = game.snake1.copy(), game.snake2.copy()
    open_main_menu_from_pause(game)

    click_menu(game, "highscore")
    assert game.game_state is GameState.LEADERBOARD
    click_at(game, game.leaderboard_back_button.rect.center)
    assert game.game_state is GameState.INTRO and game.can_continue()

    click_menu(game, "continue")
    assert game.game_state is GameState.GAME and game.player_count == 2
    assert (game.snake1, game.snake2) == snakes
    assert (game.score, game.lives) == (293, 2)
    assert (game.player_health_p1, game.player_health_p2) == (42, 79)


def test_escape_resumes_paused_round_without_discarding_it(game):
    click_menu(game, "single_player")
    game.score = 172
    snake = game.snake.copy()
    press(game, pygame.K_p)
    assert game.game_state is GameState.PAUSE
    press(game, pygame.K_ESCAPE)
    assert game.game_state is GameState.GAME
    assert game.snake == snake and game.score == 172


def test_game_over_to_main_menu_cannot_continue_old_round(game, monkeypatch):
    click_menu(game, "single_player")
    game.set_state(GameState.GAME_OVER)
    game_over_to_menu = next(button for button in game.game_over_buttons if button.text == "HAUPTMENÜ")
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: game_over_to_menu.rect.center)
    click_at(game, game_over_to_menu.rect.center)
    assert game.game_state is GameState.INTRO
    assert not game.can_continue() and not game.main_menu.is_enabled("continue")
    click_menu(game, "continue")
    assert game.game_state is GameState.INTRO and not game.snake
