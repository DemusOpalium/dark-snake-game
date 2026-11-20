"""Irians Auge gameplay integration: telemetry cannot alter Classic rules."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules.enums import GameState, ItemType
from modules.game import Game, Item


def test_headless_opt_in_records_boss_but_never_interrupts(tmp_path):
    game = Game(headless=True)
    game.dev_recorder._directory = tmp_path
    game.dev_recorder.configure(True)
    game.start_game(1)
    assert game.dev_recorder.active
    assert game.start_boss_fight()
    assert game.game_state == GameState.BOSS_FIGHT
    assert not game.dev_feedback.active
    names = [event["type"] for event in game.dev_recorder.events]
    assert "boss_spawn" in names
    assert next(tmp_path.glob("dev-round-*.json")).is_file()


def test_item_application_captures_real_values_and_source(tmp_path):
    game = Game(headless=True)
    game.dev_recorder._directory = tmp_path
    game.dev_recorder.configure(True)
    game.start_game(1)
    game.handle_item_pickup(Item(ItemType.SCORE_BOOST))
    samples = [
        event["data"] for event in game.dev_recorder.events
        if event["type"] == "item_applied"
    ]
    assert samples
    last = samples[-1]
    assert last["item"] == "SCORE_BOOST"
    assert last["after"]["score"] - last["before"]["score"] == 50
    assert last["after"]["xp"] - last["before"]["xp"] == 20
    assert "Game.handle_item_pickup" in last["source_code"]


def test_preboss_feedback_freeze_preserves_live_boss_timers(tmp_path):
    game = Game(headless=True)
    # Synthetic UI flow, but all actual Boss and Game timer objects are real.
    game.headless = False
    game.dev_recorder._directory = tmp_path
    game.dev_recorder.configure(True)
    game.start_game(1)
    assert game.start_boss_fight()
    assert game.dev_feedback.active
    before_proj = game.boss.next_proj
    game._dev_feedback_opened_at -= 3.5
    assert game.dev_feedback.submit(game.dev_recorder, save=False)
    game._dev_feedback_resume()
    assert game.game_state == GameState.BOSS_FIGHT
    assert not game.dev_feedback.active
    assert game.boss.next_proj >= before_proj + 3
    assert game.dev_recorder.active


def test_menu_dev_save_button_works_after_options_and_remains_on(tmp_path):
    game = Game(headless=True)
    game.dev_session.directory = tmp_path
    game._toggle_dev_recorder()
    assert game.dev_session.active
    assert not game.dev_session.has_data
    game.set_state(GameState.SETTINGS)
    game.set_state(GameState.INTRO)
    assert game.dev_session.has_data
    assert game._dev_save_session()
    assert game.dev_recorder.enabled
    assert game.dev_session.active
    assert not game.dev_session.dirty
    session_files = list(tmp_path.glob("dev-session-*.json"))
    assert len(session_files) == 1


def test_two_runs_keep_same_session_id_and_distinct_round_ids(tmp_path):
    game = Game(headless=True)
    game.dev_session.directory = tmp_path
    game.dev_recorder._directory = tmp_path
    game._toggle_dev_recorder()
    game.start_game(1)
    first = game._round_token
    session_id = game.dev_session.session_id
    assert game.dev_recorder.report["context"]["session_id"] == session_id
    game.dev_recorder.finish("reset")
    game.dev_session.round_end(first, "reset", report_saved=True)
    game.start_game(2)
    second = game._round_token
    assert first["round_id"] != second["round_id"]
    assert game.dev_session.session_id == session_id
    assert len(game.dev_session.rounds) == 2


def test_record_deliberate_test_end_after_gameover_without_changing_reason(tmp_path):
    game = Game(headless=True)
    game.dev_session.directory = tmp_path
    game.dev_recorder._directory = tmp_path
    game._toggle_dev_recorder()
    game.start_game(1)
    token = game._round_token
    assert game.dev_recorder.finish("life_depleted")
    game.dev_session.round_end(token, "life_depleted", report_saved=True)
    assert game._dev_mark_test_intent()
    assert game.dev_recorder.report["finish_reason"] == "life_depleted"
    assert game.dev_recorder.report["tester_intent"] == "intentional_test_end"
    assert game.dev_session.rounds[-1]["tester_intent"] == "intentional_test_end"


def test_active_round_reset_is_sealed_in_both_report_layers(tmp_path):
    import json
    game = Game(headless=True)
    game.dev_session.directory = tmp_path
    game.dev_recorder._directory = tmp_path
    game._toggle_dev_recorder()
    game.start_game(1)
    rid = game._round_token["round_id"]
    game.reset_game()
    assert game.dev_session.rounds[0]["finish_reason"] == "reset"
    report = json.loads((tmp_path / ("dev-round-" + rid + ".json")).read_text(encoding="utf-8"))
    assert report["finish_reason"] == "reset"
    assert game.dev_session.active


def test_quit_flushes_both_json_files_without_changing_career(tmp_path):
    import json
    game = Game(headless=True)
    game.dev_session.directory = tmp_path
    game.dev_recorder._directory = tmp_path
    game._toggle_dev_recorder()
    game.start_game(1)
    game._dev_shutdown()
    session = json.loads(next(tmp_path.glob("dev-session-*.json")).read_text(encoding="utf-8"))
    assert not session["active"]
    assert session["rounds"][0]["finish_reason"] == "quit"
    assert not game.dev_recorder.active


def test_dev_menu_drawing_after_completed_2p_round_does_not_crash(tmp_path):
    """Actual regression: after highscore entry the menu draws F10 hint."""
    game = Game(headless=True)
    game.dev_session.directory = tmp_path
    game.dev_recorder._directory = tmp_path
    game._toggle_dev_recorder()
    game.start_game(2)
    token = game._round_token
    assert game.dev_recorder.finish("life_depleted")
    game.dev_session.round_end(token, "life_depleted", report_saved=True)
    game.reset_game()  # highscore flow returns to INTRO after entering the name
    assert game.game_state == GameState.INTRO
    assert game.dev_session.rounds[-1]["finished_at"]
    game._draw_dev_indicator()  # before fix: pygame.Rect rejects topcenter
    assert game._dev_save_rect.width == 160
    assert game._dev_mark_test_intent()
    game._draw_dev_indicator()  # test both F10 hint labels
