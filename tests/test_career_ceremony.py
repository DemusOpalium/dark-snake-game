"""Game Over D: show only committed career XP, rank and one real skin award."""
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules import resources
from modules.career_ceremony import career_ceremony_for_round, CareerCeremony
from modules.career_ranks import CareerLedger
from modules.enums import GameState
from modules.game import Game
from modules.round_progress import RoundJournal, begin_round, completed_round
from modules.skin_inventory import SkinInventory, skin_registry


def commit_real_round(journal, players=1, score=3030, enemies=28, bosses=3, items=46):
    record = completed_round(
        begin_round(players), reason="life_depleted",
        score=score, level=4, enemies=enemies, bosses=bosses,
        items=items, lives_lost=3,
    )
    assert journal.append(record)
    return record


def stores(tmp_path):
    return (RoundJournal(tmp_path / "journal.json"),
            CareerLedger(tmp_path / "career.json"),
            SkinInventory(tmp_path / "skins.json"),
            skin_registry())


def test_verified_xp_rank_and_skin_belong_to_exact_saved_round(tmp_path):
    journal, ledger, skin_store, registry = stores(tmp_path)
    first = commit_real_round(journal, score=3030, enemies=28, bosses=3, items=46)
    second = commit_real_round(journal, score=2458, enemies=30, bosses=2, items=51)
    third = commit_real_round(journal, score=3152, enemies=44, bosses=3, items=59)
    career = ledger.sync(journal)
    skins = skin_store.sync(career, registry)
    assert career["total_xp"] == 4263 and career["rank"] == 4

    results = [
        career_ceremony_for_round(rec["round_id"], career, skins, registry)
        for rec in (first, second, third)
    ]
    assert [r.earned_xp for r in results] == [1413, 1200, 1650]
    assert [(r.rank_before, r.rank_after) for r in results] == [
        (1, 2), (2, 3), (3, 4)
    ]
    assert [r.reward_type for r in results] == ["head", "body", "head"]
    assert all(r.reward_state == "granted" for r in results)
    assert [r.total_xp for r in results] == [1413, 2613, 4263]
    assert results[-1].next_rank_xp == 5000
    assert results[-1].xp_to_next_rank == 737
    assert len(set(r.reward_id for r in results)) == 3
    assert results[-1].reward_filename == registry.career[2]["filename"]
    assert skin_store.sync(career, registry) == skins
    assert career_ceremony_for_round(third["round_id"], career, skins, registry) == results[-1]


def test_no_rankup_no_skin_is_reported_without_inventing_achievement(tmp_path):
    journal, ledger, skin_store, registry = stores(tmp_path)
    first = commit_real_round(journal, score=0, enemies=0, bosses=0, items=0)
    second = commit_real_round(journal, score=100, enemies=0, bosses=0, items=0)
    career = ledger.sync(journal)
    inventory = skin_store.sync(career, registry)
    result = career_ceremony_for_round(second["round_id"], career, inventory, registry)
    assert result.rank_before == result.rank_after == 1
    assert result.earned_xp == 10
    assert result.reward_state == "none"
    assert result.reward_id is None
    assert len(inventory["grants"]) == 0
    assert first["round_id"] in inventory["processed_rounds"]


def test_unprocessed_skin_commit_is_pending_not_false_absent_reward(tmp_path):
    journal, ledger, skin_store, registry = stores(tmp_path)
    rec = commit_real_round(journal)
    career = ledger.sync(journal)
    without_inventory = career_ceremony_for_round(rec["round_id"], career)
    assert without_inventory.earned_xp == 1413
    assert without_inventory.reward_state == "pending"
    # The created but empty starter-only inventory also hasn't processed the run.
    empty = skin_store.read(registry)
    pending = career_ceremony_for_round(rec["round_id"], career, empty, registry)
    assert pending.reward_state == "pending"
    committed = skin_store.sync(career, registry)
    assert career_ceremony_for_round(
        rec["round_id"], career, committed, registry
    ).reward_state == "granted"


def test_absent_or_corrupt_round_data_is_not_shown_as_earned_xp(tmp_path):
    journal, ledger, skin_store, registry = stores(tmp_path)
    rec = commit_real_round(journal)
    career = ledger.sync(journal)
    with pytest.raises(ValueError, match="absent"):
        career_ceremony_for_round("not-a-real-uuid", career)
    with pytest.raises(ValueError):
        career_ceremony_for_round(rec["round_id"], {**career, "total_xp": 99})
    tampered = {**career, "awards": [{**career["awards"][0], "xp": -5}]}
    with pytest.raises(ValueError):
        career_ceremony_for_round(rec["round_id"], tampered)
    assert not skin_store.path.exists()


def test_max_rank_has_no_next_rank_and_not_repeatedly_granted(tmp_path):
    journal, ledger, skin_store, registry = stores(tmp_path)
    rec = commit_real_round(journal, score=4_000_000, enemies=0, bosses=0, items=0)
    career = ledger.sync(journal)
    inventory = skin_store.sync(career, registry)
    first = career_ceremony_for_round(rec["round_id"], career, inventory, registry)
    assert (first.rank_before, first.rank_after) == (1, 40)
    assert first.next_rank_xp is None
    assert first.xp_to_next_rank is None
    assert len(inventory["grants"]) == 1


@pytest.mark.parametrize("players", [1, 2])
@pytest.mark.parametrize("finish_reason", ["damage", "stall"])
def test_game_over_renders_verified_card_and_keeps_highscore_name(
        players, finish_reason, tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game._sync_career_progress()
    assert game._sync_skin_inventory()
    game.start_game(players)
    game.score = 3030
    game.round_enemies_defeated = 28
    game.round_bosses_defeated = 3
    game.round_items_collected = 46
    game.lives = 1
    if finish_reason == "stall":
        game.handle_self_collision()
    else:
        if players == 1:
            game.player_health = 0
        else:
            game.player_health_p1 = 0
            game.player_health_p2 = 100
        game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    ceremony = game.round_career_result
    assert isinstance(ceremony, CareerCeremony)
    assert (ceremony.rank_before, ceremony.rank_after) == (1, 2)
    assert ceremony.earned_xp == 1413
    assert ceremony.reward_type == "head"
    assert ceremony.reward_state == "granted"
    assert game.leaderboard_mode
    game.name_input = "NameStays"
    # The actual game plays its death-soul/fog transition BEFORE the
    # Dark Abyss appears. Complete that transition for this UI test.
    game._death_soul_event = None
    game.draw()
    assert game._game_over_visual._career_card_cache is not None
    first_card = game._game_over_visual._career_card_cache
    before = (game.name_input, game.score, game.round_career_result)
    game.draw()
    assert game._game_over_visual._career_card_cache is first_card
    assert (game.name_input, game.score, game.round_career_result) == before
    assert len(SkinInventory().read(skin_registry())["grants"]) == 1
    game.start_game(players)
    assert game.round_career_result is None
    assert len(SkinInventory().read(skin_registry())["grants"]) == 1


def test_inventory_failure_shows_pending_reward_without_losing_xp(
        tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    game._sync_career_progress()
    game._sync_skin_inventory()
    game.start_game(1)
    game.score = 3030
    game.round_enemies_defeated = 28
    game.round_bosses_defeated = 3
    game.round_items_collected = 46
    game.lives = 1
    game.player_health = 0

    def fail(*args, **kwargs):
        raise OSError("skin inventory unavailable")
    monkeypatch.setattr(SkinInventory, "sync", fail)
    game.handle_death()
    assert game.game_state == GameState.GAME_OVER
    assert game.round_career_result is not None
    assert game.round_career_result.earned_xp == 1413
    assert game.round_career_result.reward_state == "pending"
    assert game.skin_inventory_error == "skin inventory unavailable"
    game._death_soul_event = None
    game.draw()
    assert game._game_over_visual._career_card_cache is not None


def test_aborted_unrecorded_round_never_shows_fake_career_prize(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game.start_game(1)
    game.score = 4000
    game.game_state = GameState.GAME_OVER
    game.draw()
    assert game.round_career_result is None
    assert game._game_over_visual._career_card_cache is None
    assert not resources.career_file_path().exists()
