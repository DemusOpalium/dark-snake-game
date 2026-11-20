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
