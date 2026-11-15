"""Test language switching through the actual World Studio controls."""

import json

import pygame
import pytest

from test_editor_button_actions import target
from test_level_studio import cell, click, key, send, text

from modules import resources
from modules.enums import GameState
from modules.game import Game
from modules.studio_locale import StudioLocale


@pytest.fixture
def fresh_studio(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    monkeypatch.setattr(resources, "DATA_DIR", profile)
    monkeypatch.chdir(tmp_path)
    game = Game()
    pygame.event.clear()
    key(game, pygame.K_F2)
    return game, game.level_editor, profile


def choose(game, editor, action_id):
    click(game, target(editor, action_id).rect.center)


def test_language_switch_persists_without_resetting_editor_or_classic(fresh_studio):
    game, editor, profile = fresh_studio
    assert editor.tr.language == "en"
    assert target(editor, "build_eraser").label == "Eraser"
    game.settings["difficulty"] = 1.25
    game.start_game(1)
    classic_round = game.game_state, game.lives, game.score, game.snake.copy()

    assert editor.new_map("Winter Test")
    click(game, cell(editor, 3, 3))
    editor.toggle_layer_lock("roof")
    editor.toggle_layer_visibility("effects")
    editor.toggle_layer_solo("ground")
    picture = editor._snapshot()
    history = editor.undo_stack.copy()
    choose(game, editor, "nav_language")
    assert editor.tr.language == "de" and target(editor, "build_eraser").label == "Radierer"
    assert editor._snapshot() == picture and editor.undo_stack == history
    assert editor.active and editor.dirty and editor.solo_layer == "ground"
    assert editor.layer_locked("roof") and not editor.layer_visible("effects")

    assert editor.save_map()
    editor.toggle_layer_solo("ground")
    assert not editor.layer_visible("effects")
    key(game, pygame.K_F2)
    assert not editor.active
    assert (game.game_state, game.lives, game.score, game.snake) == classic_round
    assert game.game_state == GameState.GAME

    saved = json.loads((profile / "settings.json").read_text(encoding="utf-8"))
    assert saved["studio_language"] == "de" and saved["difficulty"] == 1.25
    fresh = Game()
    key(fresh, pygame.K_F2)
    reopened = fresh.level_editor
    assert reopened.tr.language == "de"
    assert reopened.load_map("Winter Test") and reopened._snapshot() == picture
    choose(fresh, reopened, "nav_language")
    assert reopened.tr.language == "en" and reopened._snapshot() == picture
    assert json.loads((profile / "settings.json").read_text(encoding="utf-8"))["studio_language"] == "en"


@pytest.mark.parametrize("size", [(900, 620), (1350, 930), (2560, 1369)])
def test_rendered_toolbar_help_and_dialogs_in_both_languages(fresh_studio, monkeypatch, size):
    game, editor, _ = fresh_studio
    game.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    editor.resize(size)
    seen = []
    original_draw_text = editor._draw_text

    def record(screen, label, pos, *args, **kwargs):
        seen.append(label)
        return original_draw_text(screen, label, pos, *args, **kwargs)

    monkeypatch.setattr(editor, "_draw_text", record)
    for language, storage_label, new_title, invalid_name in (
        ("en", "Unsaved", "New draft", "Invalid level name."),
        ("de", "Ungespeichert", "Neuer Entwurf", "Ungültiger Levelname."),
    ):
        assert editor.tr.language == language
        choose(game, editor, "nav_help")
        assert editor.sidebar.tab == "help"
        assert all(editor.layout.header.contains(control.rect) for control in editor.buttons)
        pos = target(editor, "nav_help").rect.center
        send(game, pygame.event.Event(pygame.MOUSEMOTION, pos=pos, rel=(0, 0), buttons=(0, 0, 0)))
        game.draw()
        assert any(line.startswith(storage_label) for line in seen)
        tooltip = "Open World Studio help." if language == "en" else "Die Hilfe zum World Studio öffnen."
        assert tooltip in seen
        pane = editor.layout.inspector
        assert pane.width > 0
        help_pixels = pygame.image.tobytes(game.screen.subsurface(pane), "RGB")
        if language == "en":
            english_help = help_pixels
        else:
            assert help_pixels != english_help

        choose(game, editor, "nav_file")
        choose(game, editor, "file_new")
        text(game, "../forbidden")
        key(game, pygame.K_RETURN)
        game.draw()
        assert new_title in seen
        assert any(line.startswith(invalid_name) for line in seen)
        key(game, pygame.K_ESCAPE)
        seen.clear()
        choose(game, editor, "nav_language")


@pytest.mark.parametrize("players", [1, 2])
def test_language_switch_keeps_running_roof_demo(fresh_studio, players):
    game, editor, _ = fresh_studio
    size = 900, 620
    game.screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    editor.resize(size)
    board = editor.camera.board_rect.copy()
    language_button = target(editor, "nav_language").rect.copy()
    choose(game, editor, "nav_test")
    choose(game, editor, "test_roof_demo")
    choose(game, editor, f"test_player_{players}")
    session = editor.playtest
    assert session.player_count == players
    assert editor.camera.board_rect == board and target(editor, "nav_language").rect == language_button
    assert target(editor, "test_stop").label == "Stop test"

    choose(game, editor, "nav_language")
    assert editor.playtest is session
    assert target(editor, "test_stop").label == "Test beenden"
    key(game, pygame.K_w)
    if players == 2:
        key(game, pygame.K_UP)
    for _ in range(6):
        session.update(session.players[0].next_step)
    assert all(player.cell[0] == 22 and player.cell[1] <= 11 for player in session.players)
    choose(game, editor, "test_stop")
    assert editor.playtest is None and not editor.dirty


def test_unknown_language_and_missing_translation_have_readable_fallback():
    locale = StudioLocale("unknown")
    assert locale.language == "en"
    assert locale("Sondermeldung für {name}", name="Demo") == "Sondermeldung für Demo"
    locale.language = " DE "
    assert locale.language == "de" and locale("Vorschau beenden") == "Vorschau beenden"
