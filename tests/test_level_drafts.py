import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

from config import GRID_HEIGHT, GRID_WIDTH
from modules import level_drafts, resources
from modules.graphic_objects import GraphicObject
from modules.level_effects import CellEffects, DamageField, SlowField


@pytest.fixture
def profile(tmp_path, monkeypatch):
    path = tmp_path / "profile"
    monkeypatch.setattr(resources, "DATA_DIR", path)
    return path


def level_with(tile=None):
    level = [[None] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
    level[0][0] = tile
    return level


def test_graphic_objects_upgrade_and_round_trip_with_existing_layers(profile):
    graphics = level_with("existing_tile")
    collisions = {(3, 4): "WALL"}
    effects = {(3, 4): CellEffects(slow=SlowField(25))}
    level_drafts.write_draft("Alt", graphics, collision=collisions, effects=effects)
    assert level_drafts.read_level_document("Alt") == (graphics, collisions, effects, {})
    objects = {(3, 4): GraphicObject("frostage_6x6_001", 6, 6),
               (12, 4): GraphicObject("frostage_missing_future_asset", 1, 10)}
    level_drafts.write_draft("Alt", graphics, objects=objects, replace=True)
    path = profile / "levels" / "Alt.json"
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 3
    assert level_drafts.read_level_document("Alt") == (graphics, collisions, effects, objects)
    level_drafts.write_draft("Alt", level_with("other"), replace=True)
    assert level_drafts.read_level_document("Alt") == (level_with("other"), collisions, effects, objects)
    level_drafts.write_draft("Alt", graphics, objects={}, replace=True)
    assert level_drafts.read_level_document("Alt") == (graphics, collisions, effects, {})


@pytest.mark.parametrize("invalid_records", [
    [{"x": 44, "y": 0, "asset_id": "frostage_a", "width": 2, "height": 1}],
    [{"x": 0, "y": 0, "asset_id": "../unsafe", "width": 1, "height": 1}],
    [{"x": 0, "y": 0, "asset_id": "frostage_a", "width": True, "height": 1}],
    [{"x": 0, "y": 0, "asset_id": "frostage_a", "width": 2, "height": 1},
     {"x": 1, "y": 0, "asset_id": "frostage_b", "width": 1, "height": 1}],
])
def test_bad_object_records_do_not_get_replaced(profile, invalid_records):
    level_drafts.write_draft("Kaputt", level_with(), objects={})
    path = profile / "levels" / "Kaputt.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["objects"] = invalid_records
    path.write_text(json.dumps(payload), encoding="utf-8")
    original = path.read_bytes()
    with pytest.raises(ValueError):
        level_drafts.read_level_document("Kaputt")
    with pytest.raises(ValueError):
        level_drafts.write_draft("Kaputt", level_with(), objects={}, replace=True)
    assert path.read_bytes() == original

def test_two_named_drafts_round_trip_independently(profile, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert level_drafts.list_drafts() == []
    assert level_drafts.suggest_draft_name() == "Level_001"
    assert not profile.exists()

    first = level_with("tile_01")
    second = level_with("ältere-kachel")
    assert level_drafts.write_draft("Level_001", first) == "Level_001"
    assert level_drafts.write_draft("  Pilzwelt_Östlich.json ", second) == "Pilzwelt_Östlich"

    assert level_drafts.suggest_draft_name() == "Level_002"
    assert level_drafts.list_drafts() == ["Level_001", "Pilzwelt_Östlich"]
    assert level_drafts.read_draft("Level_001.json") == first
    assert level_drafts.read_draft("Pilzwelt_Östlich") == second
    assert not (profile / "custom_level.json").exists()
    assert json.loads((profile / "levels" / "Level_001.json").read_text(encoding="utf-8")) == first


def test_duplicate_name_requires_explicit_replacement(profile):
    original, update = level_with("old"), level_with("new")
    level_drafts.write_draft("Bossarena", original)
    path = profile / "levels" / "Bossarena.json"
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        level_drafts.write_draft("bossarena.JSON", update)
    assert path.read_bytes() == before

    assert level_drafts.write_draft("Bossarena", update, replace=True) == "Bossarena"
    assert level_drafts.read_draft("bossarena") == update
    with pytest.raises(FileNotFoundError):
        level_drafts.write_draft("Andere Arena", original, replace=True)
    assert level_drafts.list_drafts() == ["Bossarena"]


def test_first_save_never_clobbers_a_concurrent_save(profile, monkeypatch):
    publication = level_drafts._publish_new_draft
    both_writers = Barrier(2)

    def synchronized_publish(source, destination):
        both_writers.wait(timeout=5)
        publication(source, destination)

    def save(tile):
        try:
            level_drafts.write_draft("Gleichzeitig", level_with(tile))
        except FileExistsError:
            return None
        return tile

    monkeypatch.setattr(level_drafts, "_publish_new_draft", synchronized_publish)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, ["erste-kachel", "zweite-kachel"]))

    assert results.count(None) == 1
    assert level_drafts.read_draft("Gleichzeitig") == level_with(next(tile for tile in results if tile))
    assert [path.name for path in (profile / "levels").iterdir()] == ["Gleichzeitig.json"]


@pytest.mark.parametrize("collision,effects", [
    (None, None),
    ({(2, 3): "BARRIER"}, None),
    ({(2, 3): "BARRIER"}, {(2, 3): CellEffects(slow=SlowField())}),
])
def test_failed_replace_keeps_prior_file_and_cleans_up(profile, monkeypatch, collision, effects):
    level_drafts.write_draft("Level_001", level_with("old"), collision=collision, effects=effects)
    path = profile / "levels" / "Level_001.json"
    original = path.read_bytes()

    def denied_replace(source, destination):
        assert destination == path
        raise PermissionError("Datei gesperrt")

    monkeypatch.setattr(Path, "replace", denied_replace)
    with pytest.raises(PermissionError):
        level_drafts.write_draft("Level_001", level_with("new"), collision=collision,
                                 effects=effects, replace=True)

    assert path.read_bytes() == original
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize("name", ["../Escape", r"..\Escape", "X:/Escape", "CON", "LPT1.txt",
                                  "Level.", ".json", "Level.json.json"])
def test_unsafe_draft_names_rejected_before_writing(profile, name):
    with pytest.raises(ValueError):
        level_drafts.write_draft(name, level_with())
    assert not profile.exists()


@pytest.mark.parametrize("invalid", [b"{", b"\xff", b'{"map":[]}', b"[[]]"])
def test_corrupt_level_is_reported_without_touching_it(profile, invalid):
    directory = profile / "levels"
    directory.mkdir(parents=True)
    path = directory / "Kaputt.json"
    path.write_bytes(invalid)
    assert level_drafts.list_drafts() == ["Kaputt"]

    with pytest.raises(ValueError):
        level_drafts.read_draft("Kaputt")
    assert path.read_bytes() == invalid


def test_invalid_level_cannot_overwrite_existing_file(profile):
    original = level_with("old")
    level_drafts.write_draft("Level_001", original)
    invalid = level_with(23)
    with pytest.raises(ValueError, match="Level-Kachel"):
        level_drafts.write_draft("Level_001", invalid, replace=True)
    assert level_drafts.read_draft("Level_001") == original


def test_legacy_grid_is_readable_and_remains_unchanged(profile):
    profile.mkdir()
    old_map = level_with("old-tile-id")
    path = profile / "custom_level.json"
    path.write_text(json.dumps(old_map), encoding="utf-8-sig")
    old_bytes = path.read_bytes()

    assert level_drafts.legacy_map_exists()
    assert level_drafts.read_legacy_map() == old_map
    assert level_drafts.list_drafts() == []
    level_drafts.write_draft("Alte Karte", old_map)
    assert level_drafts.read_level("Alte Karte") == (old_map, {})
    assert path.read_bytes() == old_bytes


def test_versioned_draft_round_trips_graphics_and_both_collision_types(profile):
    graphics = level_with("Wandgrafik")
    collision = {(GRID_WIDTH - 1, GRID_HEIGHT - 1): "BARRIER", (0, 0): "WALL"}

    level_drafts.write_draft("Mauer", graphics, collision=collision)

    assert level_drafts.read_level("Mauer") == (graphics, collision)
    assert level_drafts.read_draft("Mauer") == graphics
    path = profile / "levels" / "Mauer.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "version": 1,
        "graphics": graphics,
        "collision": [
            {"x": 0, "y": 0, "type": "WALL"},
            {"x": GRID_WIDTH - 1, "y": GRID_HEIGHT - 1, "type": "BARRIER"},
        ],
    }


def test_graphics_only_save_keeps_collision_until_explicitly_removed(profile):
    collision = {(0, 0): "WALL"}
    level_drafts.write_draft("Mauer", level_with("Wandgrafik"), collision=collision)
    decorated = level_with("Dekoration")

    level_drafts.write_draft("Mauer", decorated, replace=True)
    assert level_drafts.read_level("Mauer") == (decorated, collision)

    level_drafts.write_draft("Mauer", decorated, collision={}, replace=True)
    assert level_drafts.read_level("Mauer") == (decorated, {})
    path = profile / "levels" / "Mauer.json"
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 1


@pytest.mark.parametrize("collision", [None, {(3, 2): "WALL"}])
def test_raw_and_v1_drafts_load_empty_effects_and_migrate_without_data_loss(profile, collision):
    graphics = level_with("alte-kachel")
    level_drafts.write_draft("Alt", graphics, collision=collision)
    path = profile / "levels" / "Alt.json"
    before = path.read_bytes()

    assert level_drafts.read_level_layers("Alt") == (graphics, collision or {}, {})
    assert path.read_bytes() == before

    effects = {(3, 2): CellEffects(damage=DamageField(12, 0.5))}
    level_drafts.write_draft("Alt", graphics, effects=effects, replace=True)
    assert level_drafts.read_level_layers("Alt") == (graphics, collision or {}, effects)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2


def test_version_two_round_trip_keeps_two_effects_and_collision_on_same_cell(profile):
    graphics = level_with("dekor")
    collision = {(2, 3): "BARRIER"}
    effects = {
        (2, 3): CellEffects(DamageField(23, 0.75, 12.5), SlowField(90)),
        (1, 2): CellEffects(damage=DamageField()),
        (0, 1): CellEffects(slow=SlowField(25)),
    }
    level_drafts.write_draft("Labor", graphics, collision=collision, effects=effects)
    assert level_drafts.read_level_layers("Labor") == (graphics, collision, effects)
    assert level_drafts.read_level("Labor") == (graphics, collision)
    assert level_drafts.read_draft("Labor") == graphics
    path = profile / "levels" / "Labor.json"
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "version": 2,
        "graphics": graphics,
        "collision": [{"x": 2, "y": 3, "type": "BARRIER"}],
        "effects": [
            {"x": 0, "y": 1, "slow": {"percent": 25}},
            {"x": 1, "y": 2, "damage": {"amount": 10, "interval": 1.0, "duration": None}},
            {"x": 2, "y": 3, "damage": {"amount": 23, "interval": 0.75, "duration": 12.5},
             "slow": {"percent": 90}},
        ],
    }


def test_updating_layers_preserves_omitted_effects_until_explicitly_removed(profile):
    effects = {(0, 0): CellEffects(slow=SlowField(50))}
    collision = {(0, 0): "WALL"}
    level_drafts.write_draft("Tempo", level_with("Original"), collision=collision, effects=effects)

    graphics = level_with("Neue Grafik")
    level_drafts.write_draft("Tempo", graphics, replace=True)
    assert level_drafts.read_level_layers("Tempo") == (graphics, collision, effects)
    level_drafts.write_draft("Tempo", graphics, collision={}, replace=True)
    assert level_drafts.read_level_layers("Tempo") == (graphics, {}, effects)

    level_drafts.write_draft("Tempo", graphics, effects={}, replace=True)
    assert level_drafts.read_level_layers("Tempo") == (graphics, {}, {})
    path = profile / "levels" / "Tempo.json"
    level_drafts.write_draft("Tempo", graphics, replace=True)
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == 2


@pytest.mark.parametrize("changes", [
    {"version": 3},
    {"effects": {}},
    {"effects": [{"x": 0, "y": 0}]},
    {"effects": [{"x": False, "y": 0, "slow": {"percent": 10}}]},
    {"effects": [{"x": 0, "y": GRID_HEIGHT, "slow": {"percent": 10}}]},
    {"effects": [{"x": 0, "y": 0, "slow": {"percent": 15}}]},
    {"effects": [{"x": 0, "y": 0, "slow": {"percent": 50.0}}]},
    {"effects": [{"x": 0, "y": 0, "damage": {"amount": True, "interval": 0.5}}]},
    {"effects": [{"x": 0, "y": 0, "damage": {"amount": 10, "interval": 0}}]},
    {"effects": [{"x": 0, "y": 0, "damage": {"amount": 10, "interval": float("nan")}}]},
    {"effects": [{"x": 0, "y": 0, "damage": {"amount": 10, "interval": 1, "duration": -1}}]},
    {"effects": [{"x": 0, "y": 0, "damage": {"amount": 10, "interval": 1, "extra": 0}}]},
    {"effects": [{"x": 0, "y": 0, "slow": {"percent": 10}},
                 {"x": 0, "y": 0, "slow": {"percent": 25}}]},
])
def test_invalid_effect_document_cannot_be_opened_or_replaced(profile, changes):
    directory = profile / "levels"
    directory.mkdir(parents=True)
    path = directory / "Kaputt.json"
    document = {"version": 2, "graphics": level_with(), "collision": [], "effects": []} | changes
    path.write_text(json.dumps(document), encoding="utf-8")
    original = path.read_bytes()

    with pytest.raises(ValueError):
        level_drafts.read_level_layers("Kaputt")
    with pytest.raises(ValueError):
        level_drafts.write_draft("Kaputt", level_with(), collision={}, effects={}, replace=True)
    assert path.read_bytes() == original


@pytest.mark.parametrize("effects", [
    {(1, 1): CellEffects()},
    {(1, 1): {"slow": 50}},
    {(False, 0): CellEffects(slow=SlowField())},
    {(1,): CellEffects(slow=SlowField())},
    [(1, 1)],
])
def test_invalid_effect_settings_never_replace_existing_file(profile, effects):
    level_drafts.write_draft("Labor", level_with(), effects={(0, 0): CellEffects(slow=SlowField())})
    path = profile / "levels" / "Labor.json"
    original = path.read_bytes()

    with pytest.raises(ValueError):
        level_drafts.write_draft("Labor", level_with(), effects=effects, replace=True)
    assert path.read_bytes() == original


@pytest.mark.parametrize("changes", [
    {"version": 2},
    {"version": True},
    {"graphics": [[]]},
    {"collision": {}},
    {"collision": [{"x": True, "y": 0, "type": "WALL"}]},
    {"collision": [{"x": GRID_WIDTH, "y": 0, "type": "WALL"}]},
    {"collision": [{"x": 0, "y": -1, "type": "BARRIER"}]},
    {"collision": [{"x": 0, "y": 0, "type": "DAMAGE"}]},
    {"collision": [{"x": 0, "y": 0, "type": "WALL"},
                   {"x": 0, "y": 0, "type": "BARRIER"}]},
    {"effect": []},
])
def test_invalid_versioned_level_is_rejected_without_writing(profile, changes):
    directory = profile / "levels"
    directory.mkdir(parents=True)
    path = directory / "Kaputt.json"
    invalid = {"version": 1, "graphics": level_with(), "collision": []} | changes
    path.write_text(json.dumps(invalid), encoding="utf-8")
    original = path.read_bytes()

    with pytest.raises(ValueError):
        level_drafts.read_level("Kaputt")
    with pytest.raises(ValueError):
        level_drafts.write_draft("Kaputt", level_with("Dekoration"), replace=True)
    with pytest.raises(ValueError):
        level_drafts.write_draft("Kaputt", level_with("Dekoration"), collision={}, replace=True)
    assert path.read_bytes() == original


@pytest.mark.parametrize("invalid", [
    {(False, 0): "WALL"}, {(0, GRID_HEIGHT): "BARRIER"},
    {(1, 1): "SLOW"}, {(1,): "WALL"}, ["WALL"],
])
def test_invalid_collision_cannot_replace_saved_level(profile, invalid):
    original = level_with("Wandgrafik")
    collision = {(0, 0): "WALL"}
    level_drafts.write_draft("Mauer", original, collision=collision)
    path = profile / "levels" / "Mauer.json"
    before = path.read_bytes()

    with pytest.raises(ValueError):
        level_drafts.write_draft("Mauer", level_with("Dekoration"), collision=invalid, replace=True)
    assert path.read_bytes() == before


def test_drafts_are_never_written_inside_pyinstaller_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "_MEI"
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr(resources, "DATA_DIR", bundle / "profile")
    with pytest.raises(OSError, match="temporären Spielordner"):
        level_drafts.write_draft("Level_001", level_with())
    assert not bundle.exists()
