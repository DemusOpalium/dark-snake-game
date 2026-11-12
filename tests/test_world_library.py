import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

from config import GRID_HEIGHT, GRID_WIDTH
from modules import level_drafts, resources
from modules.world_library import WorldLibrary


@pytest.fixture
def profile(tmp_path, monkeypatch):
    path = tmp_path / "profile"
    monkeypatch.setattr(resources, "DATA_DIR", path)
    return path


def create_draft(name, tile):
    level = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
    level[0][0] = tile
    level_drafts.write_draft(name, level)
    return level


def test_discovery_is_read_only_and_keeps_legacy_draft_files(profile):
    original = create_draft("Sternentor", "galactic_01")
    draft = profile / "levels" / "Sternentor.json"
    legacy = profile / "custom_level.json"
    legacy.write_text(json.dumps(original), encoding="utf-8")
    original_bytes = draft.read_bytes()
    legacy_bytes = legacy.read_bytes()

    library = WorldLibrary.load()
    level = library.level_for_draft("Sternentor")
    assert level.name == "Sternentor"
    assert level.world_id is None and level.available
    assert WorldLibrary.load().level_for_draft("Sternentor").id == level.id
    assert not resources.world_library_path().exists()

    world_id = library.create_world("Galaxie")
    library.assign_level(level.id, world_id)
    library.rename_level(level.id, "Sternentor bei Nacht")
    library.rename_world(world_id, "Sternenwelten")

    reopened = WorldLibrary.load()
    assert reopened.worlds[world_id].name == "Sternenwelten"
    assert reopened.levels[level.id].name == "Sternentor bei Nacht"
    assert reopened.levels[level.id].world_id == world_id
    assert reopened.levels[level.id].draft_name == "Sternentor"
    assert level_drafts.read_draft("Sternentor") == original
    assert draft.read_bytes() == original_bytes
    assert legacy.read_bytes() == legacy_bytes


def test_explicit_game_order_survives_rename_move_removal_and_reopen(profile):
    for draft_name in ("Alfa", "Beta", "Gamma"):
        create_draft(draft_name, draft_name)
    library = WorldLibrary.load()
    alfa, beta, gamma = (library.level_for_draft(name).id for name in ("Alfa", "Beta", "Gamma"))
    world_id = library.create_world("Pilzwelt")
    library.assign_level(beta, world_id)
    for level_id in (beta, alfa, gamma, beta):
        library.add_to_game_order(level_id)
    assert library.game_order == (beta, alfa, gamma)

    library.move_in_game_order(gamma, -2)
    library.move_in_game_order(gamma, -1)  # Top edge stays put.
    library.rename_level(gamma, "Zeta")
    library.assign_level(beta, None)
    library.remove_from_game_order(alfa)

    reopened = WorldLibrary.load()
    assert reopened.game_order == (gamma, beta)
    assert reopened.levels[gamma].name == "Zeta"
    assert reopened.levels[beta].world_id is None
    assert reopened.levels[alfa].available
    assert level_drafts.list_drafts() == ["Alfa", "Beta", "Gamma"]


def test_missing_draft_retains_identity_and_order_until_file_returns(profile):
    create_draft("Frosttempel", "frozen_01")
    library = WorldLibrary.load()
    level_id = library.level_for_draft("Frosttempel").id
    library.add_to_game_order(level_id)
    path = profile / "levels" / "Frosttempel.json"
    path.unlink()

    missing = WorldLibrary.load()
    assert missing.game_order == (level_id,)
    assert not missing.levels[level_id].available
    with pytest.raises(ValueError, match="Leveldatei fehlt"):
        missing.add_to_game_order(level_id)

    create_draft("Frosttempel", "frozen_02")
    restored = WorldLibrary.load()
    assert restored.game_order == (level_id,)
    assert restored.levels[level_id].available


@pytest.mark.parametrize("invalid", [
    b"{",
    b"\xff",
    b'{"version":2,"worlds":[],"levels":[],"game_order":[]}',
    b'{"version":1,"worlds":{},"levels":[],"game_order":[]}',
    b'{"version":1,"worlds":[],"levels":[],"game_order":["missing"]}',
])
def test_invalid_catalog_is_never_overwritten(profile, invalid):
    original = create_draft("Wiese", "verdant_01")
    library = WorldLibrary.load()
    path = resources.world_library_path()
    path.write_bytes(invalid)

    with pytest.raises(ValueError):
        WorldLibrary.load()
    with pytest.raises(ValueError):
        library.create_world("Natur")
    assert path.read_bytes() == invalid
    assert library.worlds == {}
    assert level_drafts.read_draft("Wiese") == original


def test_failed_publication_keeps_previous_catalog_and_view(profile, monkeypatch):
    library = WorldLibrary.load()
    world_id = library.create_world("Frost")
    path = resources.world_library_path()
    original = path.read_bytes()

    def denied_replace(source, destination):
        assert destination == path
        raise PermissionError("Datei gesperrt")

    monkeypatch.setattr(Path, "replace", denied_replace)
    with pytest.raises(PermissionError):
        library.rename_world(world_id, "Eis")

    assert library.worlds[world_id].name == "Frost"
    assert path.read_bytes() == original
    assert not list(profile.glob(".world-library-*.tmp"))


def test_parallel_changes_fail_safely_and_retry_reads_latest_catalog(profile, monkeypatch):
    first = WorldLibrary.load()
    second = WorldLibrary.load()
    save = WorldLibrary._save
    pending = Event()
    release = Event()

    def blocked_save(path, payload):
        pending.set()
        assert release.wait(timeout=5)
        save(path, payload)

    monkeypatch.setattr(WorldLibrary, "_save", staticmethod(blocked_save))
    with ThreadPoolExecutor(max_workers=1) as pool:
        operation = pool.submit(first.create_world, "Frost")
        try:
            assert pending.wait(timeout=5)
            with pytest.raises(OSError, match="bereits bearbeitet"):
                second.create_world("Feuer")
        finally:
            release.set()
        operation.result(timeout=5)

    second.create_world("Feuer")
    assert {world.name for world in WorldLibrary.load().worlds.values()} == {"Frost", "Feuer"}
