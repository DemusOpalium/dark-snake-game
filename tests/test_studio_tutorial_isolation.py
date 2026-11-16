"""Verify practice does not replace a user's draft or Classic round."""

import json

import pygame

from test_editor_sidebar import _action_center
from test_level_studio import cell, click, key, studio

from modules.level_drafts import load_level_document


def start_practice(game, editor):
    editor.sidebar.show("learn")
    launch = _action_center(editor.sidebar, editor, editor.layout.inspector, "learn_start")
    click(game, launch)
    assert editor.tutorial is not None


def test_practice_keeps_unsaved_edits_history_and_named_draft(studio):
    game, editor, profile = studio
    game.start_game(1)
    classic = (game.game_state, game.snake.copy(), game.score, game.lives)
    key(game, pygame.K_F2)
    assert editor.new_map("My Ice Crossing")
    click(game, cell(editor, 3, 3))
    assert editor.save_map()
    file = profile / "levels" / "My Ice Crossing.json"
    disk = file.read_bytes()
    click(game, cell(editor, 4, 3))
    click(game, cell(editor, 5, 3))
    editor.undo()
    editor.toggle_layer_lock("objects")
    editor.toggle_layer_visibility("roof")
    editor.toggle_layer_solo("ground")
    before = editor._snapshot()
    undo, redo = editor.undo_stack.copy(), editor.redo_stack.copy()
    assert editor.dirty and undo and redo

    start_practice(game, editor)
    assert editor._snapshot() != before and not editor.dirty
    assert not editor.undo_stack and not editor.redo_stack
    assert editor.solo_layer is None and not editor.layer_locked("objects") and editor.show_roofs
    click(game, cell(editor, 20, 13))
    assert editor.dirty
    key(game, pygame.K_s, pygame.KMOD_CTRL)
    key(game, pygame.K_n, pygame.KMOD_CTRL)
    key(game, pygame.K_o, pygame.KMOD_CTRL)
    assert not editor.dialog_open
    assert not editor.save_map() and not editor.load_map("My Ice Crossing")
    assert not editor.load_roof_demo()
    editor.select_classic_default()
    editor.select_for_classic()
    assert file.read_bytes() == disk
    assert sorted(p.name for p in file.parent.glob("*.json")) == [file.name]
    assert (game.game_state, game.snake, game.score, game.lives) == classic

    key(game, pygame.K_F2)
    assert editor.active and editor.tutorial is None and not editor.dialog_open
    assert editor._snapshot() == before and editor.dirty
    assert editor.undo_stack == undo and editor.redo_stack == redo
    assert editor.solo_layer == "ground" and editor.layer_locked("objects") and not editor.show_roofs
    assert editor.name == "My Ice Crossing"
    assert editor.save_map()
    assert json.loads(file.read_text(encoding="utf-8"))["version"] == 3
    assert load_level_document("My Ice Crossing").graphics == before[0]


def test_closing_the_window_during_practice_checks_the_original_draft(studio):
    game, editor, _ = studio
    key(game, pygame.K_F2)
    click(game, cell(editor, 3, 3))
    original = editor._snapshot()
    start_practice(game, editor)

    callbacks = []
    assert editor.request_close(lambda: callbacks.append(True)) is False
    assert editor.tutorial is None and editor._snapshot() == original and editor.dirty
    assert editor._dialog["kind"] == "discard" and not callbacks
    key(game, pygame.K_ESCAPE)
    assert editor.active and editor._snapshot() == original and not callbacks
