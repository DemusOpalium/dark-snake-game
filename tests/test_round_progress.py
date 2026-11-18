"""Progress foundation: authentic round stats, durable atomic save and replay defense.

No ranks/XP/unlocks exist yet, so these tests check only *measured* gameplay.
"""
import json
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

from modules import resources
from modules.enums import GameState
from modules.game import Game
from modules.round_progress import RoundJournal, begin_round, completed_round


def snapshot(*, players=1, score=70, bosses=1, enemies=3, items=5, deaths=3):
    token = begin_round(players)
    return completed_round(token, reason="life_depleted", score=score, level=2,
                           enemies=enemies, bosses=bosses, items=items,
                           lives_lost=deaths)


def test_unique_ids_and_confirmed_counts_are_versioned_and_persistent(tmp_path):
    journal = RoundJournal(tmp_path / "progress.json")
    a = snapshot(players=1)
    b = snapshot(players=2, score=160, bosses=2, enemies=9, items=1, deaths=4)
    assert a["round_id"] != b["round_id"]
    assert journal.append(a)
    assert journal.append(b)
    assert journal.read()["schema_version"] == 1
    assert journal.read()["rounds"] == [a, b]
    assert journal.read()["totals"] == {
        "rounds_completed": 2,
        "score": 230,
        "enemies_defeated": 12,
        "bosses_defeated": 3,
        "items_collected": 6,
        "lives_lost": 7,
    }
    assert not (tmp_path / "settings.json").exists()
    assert not (tmp_path / "leaderboard.txt").exists()


def test_repeated_finish_or_reopen_never_doubles_earnings(tmp_path):
    path = tmp_path / "progress.json"
    item = snapshot()
    journal = RoundJournal(path)
    assert journal.append(item)
    original = path.read_bytes()
    assert RoundJournal(path).append(dict(item)) is False
    assert path.read_bytes() == original
    altered = dict(item, score=99999)
    with pytest.raises(ValueError, match="cannot be rewritten"):
        RoundJournal(path).append(altered)
    assert path.read_bytes() == original
    assert journal.read()["totals"]["rounds_completed"] == 1


@pytest.mark.parametrize("invalid", [
    lambda r: dict(r, score=-1),
    lambda r: dict(r, score=True),
    lambda r: dict(r, bosses_defeated=-1),
    lambda r: dict(r, level=0),
    lambda r: dict(r, players=3),
    lambda r: dict(r, finished_reason="unverified_boss"),
    lambda r: dict(r, round_id="not-a-uuid"),
    lambda r: {**r, "untrusted": 123},
])
def test_unverified_rounds_cannot_enter_history(tmp_path, invalid):
    journal = RoundJournal(tmp_path / "progress.json")
    with pytest.raises(ValueError):
        journal.append(invalid(snapshot()))
    assert not journal.path.exists()


@pytest.mark.parametrize("corruption", [
    "{broken json",
    json.dumps({"schema_version": 999, "rounds": [], "totals": {}}),
    json.dumps({"schema_version": 1, "rounds": [], "totals": {"score": 999}}),
    json.dumps({"schema_version": 1, "rounds": {}, "totals": {}}),
])
def test_corrupt_and_future_versions_are_not_silently_overwritten(tmp_path, corruption):
    path = tmp_path / "progress.json"
    path.write_text(corruption, encoding="utf-8")
    with pytest.raises(ValueError):
        RoundJournal(path).append(snapshot())
    assert path.read_text(encoding="utf-8") == corruption


def test_failed_atomic_replacement_preserves_original_file(tmp_path, monkeypatch):
    path = tmp_path / "progress.json"
    journal = RoundJournal(path)
    journal.append(snapshot())
    original = path.read_bytes()

    def deny_replace(*args, **kwargs):
        raise OSError("Simulated read-only disk")

    monkeypatch.setattr("modules.round_progress.os.replace", deny_replace)
    with pytest.raises(OSError, match="Simulated"):
        journal.append(snapshot())
    assert path.read_bytes() == original
    assert list(tmp_path.glob(".round-progress-*.tmp")) == []


def test_incomplete_rounds_do_not_appear_in_history(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(1)
    assert game._round_token is not None
    assert game._round_token["players"] == 1
    # Leaving the menu or beginning another run is not an earned completion.
    game.reset_game()
    assert not resources.progress_file_path().exists()


def test_normal_life_loss_does_not_finish_or_save_round(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(1)
    game.lives = 2
    game.player_health = 0
    game.handle_death()
    assert game.lives == 1
    assert game.game_state != GameState.GAME_OVER
    assert not resources.progress_file_path().exists()


@pytest.mark.parametrize("players", [1, 2])
def test_real_final_health_death_saves_once_in_1p_and_2p(tmp_path, monkeypatch, players):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(players)
    initial_round_id = game._round_token["round_id"]
    game.round_items_collected = 5
    game.round_enemies_defeated = 7
    game.round_bosses_defeated = 2
    game.score = 1050
    game.level = 4
    game.lives = 1
    if players == 1:
        game.player_health = 0
    else:
        game.player_health_p1 = 0
        game.player_health_p2 = 100

    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert game.round_progress_error is None
    path = resources.progress_file_path()
    assert path.is_file()
    first = RoundJournal(path).read()
    record = first["rounds"][0]
    assert record["round_id"] == initial_round_id
    assert record["players"] == players
    assert record["finished_reason"] == "life_depleted"
    assert (record["score"], record["level"], record["enemies_defeated"],
            record["bosses_defeated"], record["items_collected"],
            record["lives_lost"]) == (1050, 4, 7, 2, 5, 1)
    assert first["totals"]["rounds_completed"] == 1
    game.handle_death()
    assert RoundJournal(path).read() == first
    # A new game is a different round, never a replay of the old one.
    game.start_game(players)
    assert game._round_token["round_id"] != initial_round_id
    assert RoundJournal(path).read() == first


def test_final_self_stall_uses_same_journal_without_fake_kills(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(1)
    game.lives = 1
    game.handle_self_collision()
    record = RoundJournal().read()["rounds"][0]
    assert game.game_state == GameState.GAME_OVER
    assert record["finished_reason"] == "self_stall"
    assert record["lives_lost"] == 1
    assert record["bosses_defeated"] == 0
    assert record["items_collected"] == 0


def test_headless_simulation_does_not_pollute_real_player_progress(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game.start_game(1)
    game.lives = 1
    game.player_health = 0
    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert not resources.progress_file_path().exists()


def test_unsaved_progress_is_reported_and_can_be_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(1)
    game.lives = 1
    game.player_health = 0
    original_replace = os.replace

    def deny_replace(*args):
        raise OSError("Disk full")

    monkeypatch.setattr("modules.round_progress.os.replace", deny_replace)
    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert game.round_progress_error == "Disk full"
    assert not resources.progress_file_path().exists()
    assert not game._round_recorded

    monkeypatch.setattr("modules.round_progress.os.replace", original_replace)
    assert game._finalize_round_progress("life_depleted")
    assert RoundJournal().read()["totals"]["rounds_completed"] == 1
