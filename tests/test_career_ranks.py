"""Career B: 40 persistent ranks from committed Classic runs, never from frame ticks."""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules import resources
from modules.career_ranks import (
    CareerLedger, XP_RULES_VERSION, CAREER_SCHEMA_VERSION,
    MAX_CAREER_RANK, RANK_MIN_XP, career_rank, career_rank_id, xp_for_round,
)
from modules.enums import GameState
from modules.game import Game
from modules.round_progress import RoundJournal, begin_round, completed_round


def finished(*, players=1, score=3030, enemies=28, bosses=3, items=46, deaths=3):
    return completed_round(begin_round(players), reason="life_depleted",
                           score=score, level=4, enemies=enemies,
                           bosses=bosses, items=items, lives_lost=deaths)


def test_exactly_40_ranks_are_monotonic_with_a_stable_version():
    assert CAREER_SCHEMA_VERSION == XP_RULES_VERSION == 1
    assert MAX_CAREER_RANK == len(RANK_MIN_XP) == 40
    assert RANK_MIN_XP[0] == 0
    assert RANK_MIN_XP[1] == 500
    assert RANK_MIN_XP[-1] == 390_000
    assert list(RANK_MIN_XP) == sorted(set(RANK_MIN_XP))
    for rank, requirement in enumerate(RANK_MIN_XP, 1):
        assert career_rank(requirement) == rank
        assert career_rank_id(rank) == f"rank_{rank:02d}"
        if rank > 1:
            assert career_rank(requirement - 1) == rank - 1
    assert career_rank(999_999_999) == 40
    for bad_xp in (-1, 1.5, True, "500"):
        with pytest.raises(ValueError):
            career_rank(bad_xp)
    for bad_rank in (0, 41, False, 3.5):
        with pytest.raises(ValueError):
            career_rank_id(bad_rank)


def test_xp_uses_only_confirmed_counters_not_utc_duration_or_unfinished_events():
    real = finished()
    assert xp_for_round(real) == 303 + 280 + 600 + 230 == 1413
    altered_time = dict(real, finished_at="2030-01-01T00:00:00+00:00")
    assert xp_for_round(altered_time) == xp_for_round(real)
    altered_level = dict(real, level=12)
    assert xp_for_round(altered_level) == xp_for_round(real)
    zero = finished(score=0, enemies=0, bosses=0, items=0)
    assert xp_for_round(zero) == 0
    with pytest.raises(ValueError):
        xp_for_round(dict(real, score=-1))


def test_career_ledger_persists_exact_award_once_and_keeps_sources_separate(tmp_path):
    rounds = RoundJournal(tmp_path / "rounds.json")
    career = CareerLedger(tmp_path / "career.json")
    assert career.read()["total_xp"] == 0
    assert career.read()["rank"] == 1
    record = finished()
    assert rounds.append(record)
    first = career.sync(rounds)
    assert first["awards"] == [{
        "round_id": record["round_id"], "xp": 1413,
        "rules_version": XP_RULES_VERSION
    }]
    assert (first["total_xp"], first["rank"]) == (1413, 2)
    original = career.path.read_bytes()
    assert CareerLedger(career.path).sync(rounds) == first
    assert career.path.read_bytes() == original
    another = finished(score=500, enemies=0, bosses=0, items=0)
    rounds.append(another)
    second = career.sync(rounds)
    assert second["total_xp"] == 1463
    assert len(second["awards"]) == 2
    assert rounds.read()["totals"]["score"] == 3530
    assert not (tmp_path / "settings.json").exists()
    assert not (tmp_path / "leaderboard.txt").exists()


def test_crash_between_round_commit_and_xp_commit_is_recovered(tmp_path, monkeypatch):
    journal = RoundJournal(tmp_path / "rounds.json")
    career = CareerLedger(tmp_path / "career.json")
    real = finished()
    journal.append(real)
    assert not career.path.exists()

    def disk_full(*_args):
        raise OSError("Disk full during career save")

    original_replace = os.replace
    monkeypatch.setattr("modules.career_ranks.os.replace", disk_full)
    with pytest.raises(OSError, match="Disk full"):
        career.sync(journal)
    assert not career.path.exists()
    assert list(tmp_path.glob(".career-progress-*.tmp")) == []
    assert journal.read()["rounds"] == [real]

    monkeypatch.setattr("modules.career_ranks.os.replace", original_replace)
    recovered = CareerLedger(career.path).sync(journal)
    assert recovered["total_xp"] == 1413
    assert len(recovered["awards"]) == 1
    assert career.sync(journal) == recovered


@pytest.mark.parametrize("bad", [
    "{not-json",
    json.dumps({"schema_version": 999, "rules_version": 1,
                "awards": [], "total_xp": 0, "rank": 1}),
    json.dumps({"schema_version": 1, "rules_version": 2,
                "awards": [], "total_xp": 0, "rank": 1}),
    json.dumps({"schema_version": 1, "rules_version": 1,
                "awards": [], "total_xp": 9999, "rank": 1}),
    json.dumps({"schema_version": 1, "rules_version": 1,
                "awards": [{"round_id": "fake", "xp": 50, "rules_version": 1}],
                "total_xp": 50, "rank": 1}),
])
def test_corrupt_or_newer_career_file_is_never_overwritten(tmp_path, bad):
    journal = RoundJournal(tmp_path / "rounds.json")
    journal.append(finished())
    career = CareerLedger(tmp_path / "career.json")
    career.path.write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError):
        career.sync(journal)
    assert career.path.read_text(encoding="utf-8") == bad
    assert len(journal.read()["rounds"]) == 1


def test_existing_awards_are_immutable_if_more_rounds_arrive(tmp_path):
    journal = RoundJournal(tmp_path / "rounds.json")
    career = CareerLedger(tmp_path / "career.json")
    first = finished(score=50, enemies=0, bosses=0, items=0)
    journal.append(first)
    initial = career.sync(journal)["awards"][0]
    for score in (60, 70, 80):
        journal.append(finished(score=score, enemies=0, bosses=0, items=0))
        career.sync(journal)
    assert career.read()["awards"][0] == initial


def test_parallel_reconciliation_does_not_award_same_round_twice(tmp_path):
    journal = RoundJournal(tmp_path / "rounds.json")
    for score in range(10):
        journal.append(finished(score=100 + score))
    path = tmp_path / "career.json"
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(
            lambda _: CareerLedger(path).sync(journal)["total_xp"], range(8)
        ))
    expected = sum(xp_for_round(record) for record in journal.read()["rounds"])
    assert results == [expected] * 8
    assert len(CareerLedger(path).read()["awards"]) == 10


@pytest.mark.parametrize("players", [1, 2])
def test_real_game_over_grants_xp_for_1p_and_2p_only_once(players, tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(players)
    assert game.round_career_xp == 0
    assert not resources.career_file_path().exists()
    game.score = 3030
    game.round_enemies_defeated = 28
    game.round_bosses_defeated = 3
    game.round_items_collected = 46
    game.lives = 1
    if players == 1:
        game.player_health = 0
    else:
        game.player_health_p1 = 0
        game.player_health_p2 = 100

    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert game.round_career_xp == 1413
    assert game.career_progress_error is None
    assert game.career_snapshot["rank"] == 2
    assert game.career_snapshot["total_xp"] == 1413
    assert len(game.career_snapshot["awards"]) == 1
    game.handle_death()
    assert CareerLedger().read()["total_xp"] == 1413
    game.start_game(players)
    assert game.round_career_xp == 0
    assert CareerLedger().read()["total_xp"] == 1413


def test_game_stall_end_and_normal_respawn_are_distinct(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(1)
    game.score = 100
    game.lives = 2
    game.handle_self_collision()
    assert game.game_state != GameState.GAME_OVER
    assert not resources.career_file_path().exists()
    game.respawn.clear()  # emulate completed respawn for final-stall test
    game.lives = 1
    game.handle_self_collision()
    assert CareerLedger().read()["total_xp"] == 10
    assert CareerLedger().read()["rank"] == 1


def test_game_recovery_after_award_write_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game.start_game(1)
    game.score = 1000
    game.lives = 1
    game.player_health = 0
    # Reject only the career commit; patching os.replace globally would also
    # block the independent authoritative round journal's first save.
    original_sync = CareerLedger.sync

    def reject(*_args):
        raise OSError("Career disk blocked")

    monkeypatch.setattr(CareerLedger, "sync", reject)
    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert game._round_recorded
    assert game.round_progress_error is None
    assert game.career_progress_error == "Career disk blocked"
    assert RoundJournal().read()["totals"]["rounds_completed"] == 1
    assert not resources.career_file_path().exists()

    monkeypatch.setattr(CareerLedger, "sync", original_sync)
    # A freshly created real GUI instance reconciles the saved round on boot.
    restarted = Game()
    assert restarted.career_progress_error is None
    assert restarted.career_snapshot["rank"] == 1
    assert restarted.career_snapshot["total_xp"] == 100
    assert len(restarted.career_snapshot["awards"]) == 1


def test_headless_simulation_never_grants_live_player_xp(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game.start_game(1)
    game.score = 10000
    game.lives = 1
    game.player_health = 0
    game.handle_death()
    assert not resources.career_file_path().exists()
    assert not resources.progress_file_path().exists()
