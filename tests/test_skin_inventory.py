"""Snake Inventory C: verified rank rewards, replay defense, and locked UI."""
import json
import os
import sys
from collections import Counter
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
from modules.career_ranks import CareerLedger, career_rank
from modules.enums import GameState
from modules.game import Game
from modules.round_progress import RoundJournal, begin_round, completed_round
from modules.skin_inventory import SkinInventory, skin_registry, starter_inventory


def real_round(journal, *, score=3000, enemies=30, bosses=2, items=40, players=1):
    item = completed_round(
        begin_round(players), reason="life_depleted",
        score=score, level=4, enemies=enemies, bosses=bosses,
        items=items, lives_lost=3,
    )
    assert journal.append(item)
    return item


def test_registry_covers_all_92_runtime_skins_with_six_starters():
    registry = skin_registry()
    assert len(registry.entries) == 92
    assert len(registry.by_id) == 92
    counter = Counter((e["type"], e["group"]) for e in registry.entries)
    assert counter == Counter({
        ("head", "starter"): 4, ("body", "starter"): 2,
        ("head", "career"): 30, ("body", "career"): 8,
        ("head", "achievement"): 18, ("body", "achievement"): 5,
        ("head", "boss"): 8, ("body", "boss"): 3,
        ("head", "reserve"): 12, ("body", "reserve"): 2,
    })
    assert len(registry.career) == 38
    assert registry.career[0]["required_rank"] == 2
    assert registry.career[1]["required_rank"] == 3
    assert registry.career[-1]["required_rank"] == 39
    assert registry.career[0]["type"] == "head"
    assert registry.career[1]["type"] == "body"
    assert len({item["required_rank"] for item in registry.career}) == 38


def test_empty_inventory_has_exactly_six_free_skins(tmp_path):
    registry = skin_registry()
    path = tmp_path / "skins.json"
    store = SkinInventory(path)
    fresh = store.read(registry)
    assert len(fresh["unlocked"]) == 6
    assert set(fresh["unlocked"]) == set(registry.starters)
    assert fresh["grants"] == []
    assert not path.exists()
    assert registry.is_unlocked(fresh, "Heads", "Items1.png")
    assert registry.is_unlocked(fresh, "Bodies", "items3.png")
    assert not registry.is_unlocked(fresh, "Heads", registry.career[0]["filename"])
    assert "Gesperrt" in registry.status(
        fresh, "Heads", registry.career[0]["filename"]
    )


def test_two_confirmed_runs_grant_one_head_and_one_body_at_ranks_2_and_3(tmp_path):
    registry = skin_registry()
    journal = RoundJournal(tmp_path / "rounds.json")
    ledger = CareerLedger(tmp_path / "career.json")
    inventory = SkinInventory(tmp_path / "skins.json")
    first = real_round(journal, score=3030, enemies=28, bosses=3, items=46)
    second = real_round(journal, score=2458, enemies=30, bosses=2, items=51)
    state = inventory.sync(ledger.sync(journal), registry)
    assert state["processed_rounds"] == [first["round_id"], second["round_id"]]
    assert len(state["grants"]) == 2
    assert state["grants"][0] == {
        "round_id": first["round_id"], "skin_id": registry.career[0]["id"],
        "required_rank": 2,
    }
    assert state["grants"][1] == {
        "round_id": second["round_id"], "skin_id": registry.career[1]["id"],
        "required_rank": 3,
    }
    assert len(state["unlocked"]) == 8
    assert ledger.read()["total_xp"] == 2613
    assert ledger.read()["rank"] == 3
    assert inventory.sync(ledger.read(), registry) == state
    assert len(SkinInventory(inventory.path).read(registry)["grants"]) == 2


def test_multiple_rankups_in_one_run_grant_only_one_cosmetic(tmp_path):
    registry = skin_registry()
    journal = RoundJournal(tmp_path / "rounds.json")
    ledger = CareerLedger(tmp_path / "career.json")
    inventory = SkinInventory(tmp_path / "skins.json")
    first = real_round(journal, score=150000, enemies=0, bosses=0, items=0)
    state = inventory.sync(ledger.sync(journal), registry)
    assert career_rank(ledger.read()["total_xp"]) >= 8
    assert len(state["grants"]) == 1
    assert state["grants"][0]["round_id"] == first["round_id"]
    assert state["grants"][0]["skin_id"] == registry.career[0]["id"]

    # Earned but undelivered items are queued until *later* completed rounds.
    for expected in range(2, 5):
        real_round(journal, score=0, enemies=0, bosses=0, items=0)
        state = inventory.sync(ledger.sync(journal), registry)
        assert len(state["grants"]) == expected
        assert state["grants"][-1]["skin_id"] == registry.career[expected - 1]["id"]
    assert len(set(entry["round_id"] for entry in state["grants"])) == 4


def test_unearned_boss_achievement_and_reserve_items_stay_locked(tmp_path):
    registry = skin_registry()
    journal = RoundJournal(tmp_path / "rounds.json")
    ledger = CareerLedger(tmp_path / "career.json")
    inventory = SkinInventory(tmp_path / "skins.json")
    real_round(journal, score=300_000, enemies=100, bosses=100, items=200)
    state = inventory.sync(ledger.sync(journal), registry)
    assert len(state["grants"]) == 1
    assert all(entry["skin_id"] not in state["unlocked"]
               for entry in [])  # no external, unverified token accepted
    for entry in registry.entries:
        if entry["group"] in {"achievement", "boss", "reserve"}:
            assert entry["id"] not in state["unlocked"]


def test_legacy_equipped_skin_is_preserved_once_but_cannot_mint_later(tmp_path):
    registry = skin_registry()
    journal = RoundJournal(tmp_path / "rounds.json")
    career = CareerLedger(tmp_path / "career.json")
    store = SkinInventory(tmp_path / "skin.json")
    legacy_head = next(e for e in registry.entries
                       if e["type"] == "head" and e["group"] == "reserve")
    legacy_body = next(e for e in registry.entries
                       if e["type"] == "body" and e["group"] == "boss")
    initial = {
        "custom_head_p1": legacy_head["filename"],
        "custom_body_p2": legacy_body["filename"],
    }
    state = store.sync(career.sync(journal), registry, existing_settings=initial)
    assert legacy_head["id"] in state["unlocked"]
    assert legacy_body["id"] in state["unlocked"]
    assert set(state["legacy_unlocked"]) == {legacy_head["id"], legacy_body["id"]}
    # A later hand-edit of settings must not mint a new locked skin.
    injected = next(e for e in registry.entries if e["group"] == "reserve"
                    and e["id"] != legacy_head["id"])
    after = store.sync(career.read(), registry,
                       existing_settings={"custom_head_p1": injected["filename"]})
    assert after == state
    assert injected["id"] not in after["unlocked"]


def test_unsupported_or_corrupt_inventory_keeps_bytes_untouched(tmp_path):
    registry = skin_registry()
    career = CareerLedger(tmp_path / "career.json")
    journal = RoundJournal(tmp_path / "rounds.json")
    real_round(journal)
    data = career.sync(journal)
    inventory = SkinInventory(tmp_path / "inventory.json")
    for invalid in (
        "{",
        json.dumps({"schema_version": 999, "registry_version": 1}),
        json.dumps({"schema_version": 1, "registry_version": 999,
                    "legacy_unlocked": [], "processed_rounds": [],
                    "grants": [], "unlocked": sorted(registry.starters)}),
    ):
        inventory.path.write_text(invalid, encoding="utf-8")
        with pytest.raises(ValueError):
            inventory.sync(data, registry)
        assert inventory.path.read_text(encoding="utf-8") == invalid


def test_forged_reward_is_rejected_without_overwriting(tmp_path):
    registry = skin_registry()
    journal = RoundJournal(tmp_path / "rounds.json")
    career = CareerLedger(tmp_path / "career.json")
    store = SkinInventory(tmp_path / "inventory.json")
    first = real_round(journal, score=0, enemies=0, bosses=0, items=0)
    data = career.sync(journal)
    state = store.sync(data, registry)
    assert not state["grants"]
    # Fake "rank 2" on a round that earned zero XP.
    tampered = dict(state)
    prize = registry.career[0]
    tampered["grants"] = [{
        "round_id": first["round_id"], "skin_id": prize["id"],
        "required_rank": 2,
    }]
    tampered["unlocked"] = sorted([*tampered["unlocked"], prize["id"]])
    store.path.write_text(json.dumps(tampered), encoding="utf-8")
    before = store.path.read_bytes()
    with pytest.raises(ValueError, match="before verified career rank"):
        store.sync(data, registry)
    assert store.path.read_bytes() == before


def test_atomic_failure_and_restart_reconcile_without_duplicate_grant(
        tmp_path, monkeypatch):
    registry = skin_registry()
    journal = RoundJournal(tmp_path / "rounds.json")
    career = CareerLedger(tmp_path / "career.json")
    store = SkinInventory(tmp_path / "inventory.json")
    real_round(journal, score=3030, enemies=28, bosses=3, items=46)
    data = career.sync(journal)
    original_replace = os.replace

    def fail(*args):
        raise OSError("disk unavailable")

    monkeypatch.setattr("modules.skin_inventory.os.replace", fail)
    with pytest.raises(OSError, match="disk unavailable"):
        store.sync(data, registry)
    assert not store.path.exists()
    assert list(tmp_path.glob(".skin-inventory-*.tmp")) == []
    monkeypatch.setattr("modules.skin_inventory.os.replace", original_replace)
    recovered = SkinInventory(store.path).sync(data, registry)
    assert len(recovered["grants"]) == 1
    assert len(SkinInventory(store.path).sync(data, registry)["grants"]) == 1


def test_parallel_snapshots_cannot_double_grant_or_erase_newer_rounds(tmp_path):
    registry = skin_registry()
    journal = RoundJournal(tmp_path / "rounds.json")
    career = CareerLedger(tmp_path / "career.json")
    store = SkinInventory(tmp_path / "inventory.json")
    for i in range(5):
        real_round(journal, score=4000 + i)
    full = career.sync(journal)
    half = dict(full)
    half["awards"] = full["awards"][:2]
    half["total_xp"] = sum(a["xp"] for a in half["awards"])
    half["rank"] = career_rank(half["total_xp"])
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(lambda snapshot: SkinInventory(store.path).sync(snapshot, registry),
                          [full, full, half, full, half]))
    final = store.read(registry)
    assert len(final["processed_rounds"]) == 5
    assert len({g["round_id"] for g in final["grants"]}) == len(final["grants"])
    assert len(final["grants"]) <= 5


def test_locked_picture_can_be_inspected_but_not_equipped_or_saved(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    registry = skin_registry()
    game = Game(headless=True)
    menu = game.options_menu
    menu.apply_skin_inventory(registry, starter_inventory(registry))
    locked = next(x for x in menu.head_options
                  if registry.by_id[registry.skin_id("Heads", x[0])]["group"] == "career")
    menu.current_tab = "Heads"
    menu.current_selected_img = locked
    prior = menu.selected_head_p1
    menu.assign_image(1)
    assert menu.selected_head_p1 == prior
    assert menu.inventory_notice.startswith("Gesperrt")
    assert not menu.skin_allowed("Heads", locked[0])
    menu.selected_head_p1 = locked[0]  # bypass the button as a hostile/stale UI write
    menu.save()
    assert game.settings["custom_head_p1"] is None

    starter = next(x for x in menu.head_options
                   if registry.is_unlocked(starter_inventory(registry), "Heads", x[0]))
    menu.current_selected_img = starter
    menu.assign_image(1)
    menu.save()
    assert game.settings["custom_head_p1"] == starter[0]


@pytest.mark.parametrize("size", [(900, 620), (1350, 930)])
def test_frostage_lock_overlay_and_preview_are_drawable(size, tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    registry = skin_registry()
    menu = game.options_menu
    menu.apply_skin_inventory(registry, starter_inventory(registry))
    canvas = pygame.Surface(size)
    menu.draw(canvas)
    assert menu._frost_view._lock_shades
    assert canvas.get_rect().contains(menu.inventory_grid_rect)
    menu.current_tab = "Bodies"
    menu.draw(canvas)
    assert game.game_state is not GameState.GAME_OVER


@pytest.mark.parametrize("players", [1, 2])
def test_final_game_over_awards_skin_only_once_for_1p_and_2p(
        players, tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    game = Game(headless=True)
    game._record_completed_rounds = True
    registry = skin_registry()
    game._sync_career_progress()
    assert game._sync_skin_inventory()
    game.start_game(players)
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
    assert game.skin_inventory_error is None
    first = SkinInventory().read(registry)
    assert len(first["grants"]) == 1
    assert first["grants"][0]["required_rank"] == 2
    game.handle_death()
    assert SkinInventory().read(registry) == first
    assert game.options_menu.skin_allowed(
        "Heads", registry.career[0]["filename"]
    )


def test_actual_gui_start_migrates_saved_favorite_before_enabling_locks(
        tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    registry = skin_registry()
    chosen = next(e for e in registry.entries
                  if e["type"] == "head" and e["group"] == "boss")
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "settings.json").write_text(json.dumps({
        "custom_head_p1": chosen["filename"],
    }), encoding="utf-8")
    game = Game()  # dummy SDL display, real non-headless user-data path
    assert game.skin_inventory_error is None
    assert game.settings["custom_head_p1"] == chosen["filename"]
    assert game.options_menu.selected_head_p1 == chosen["filename"]
    assert game.options_menu.skin_allowed("Heads", chosen["filename"])
    state = SkinInventory().read(registry)
    assert chosen["id"] in state["legacy_unlocked"]
