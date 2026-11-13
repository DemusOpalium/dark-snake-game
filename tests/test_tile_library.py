import json
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

from modules import resources
from modules.frostage_assets import frostage_assets
from modules.tile_catalog import load_tile_catalog
from modules.tile_library import TileLibrary


@pytest.fixture(autouse=True)
def isolated_catalog(tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)


def test_catalog_classifies_existing_assets_without_losing_keys():
    directory = resources.find_asset_directory("graphics", "tiles")
    names = {path.stem for path in directory.iterdir() if path.suffix.lower() == ".png"}
    entries, warnings = load_tile_catalog(names | {"unknown_wall_new"})
    by_name = {entry.key: entry for entry in entries}

    assert len(names) >= 495
    assert set(by_name) == names | {"unknown_wall_new"}
    assert len(entries) == len(by_name)
    assert not warnings
    expected = {
        "bone_corner_tl": "bones", "boneshard_frostpath_0_0": "bones",
        "frosthauch_0_0": "frost", "frozen_skull_0_0": "frost", "frozenbase_0_0": "frost",
        "galactic_planetcore1_0_0": "galaxy", "planetset_brightgalactic_0_0": "galaxy",
        "altar_base_tile1": "dungeon", "altar2_circle1": "dungeon",
        "cathedral_tile_0_0": "gothic", "chorus_cathedral_0_0": "gothic",
        "venom_tile_0_0": "poison", "acid_tile_roots1": "poison",
        "verdant_grassdetails_0_0": "nature", "hellground_0_0": "fire",
        "tile_bone_border_variant4": "bones", "unknown_wall_new": "other",
    }
    for name, category in expected.items():
        assert by_name[name].category == category
        assert by_name[name].group == "single"


def test_user_override_uses_exact_filename_and_changes_only_catalogue_metadata():
    user_file = resources.tile_catalog_override_path()
    user_file.write_text(json.dumps({
        "version": 1,
        "overrides": {
            "BONE_CORNER_TL.PNG": {"category": "frost", "group": "walls"},
            "tile_bone_border_variant4": {"group": "stamps"},
        },
    }), encoding="utf-8")
    names = ("bone_corner_tl", "bone_corner_tr", "tile_bone_border_variant4")
    entries, warnings = load_tile_catalog(names)

    assert not warnings
    assert [(entry.key, entry.category, entry.group) for entry in entries] == [
        ("bone_corner_tl", "frost", "walls"),
        ("bone_corner_tr", "bones", "single"),
        ("tile_bone_border_variant4", "bones", "stamps"),
    ]


@pytest.mark.parametrize("content", [
    "{",
    '{"version":2,"overrides":{}}',
    '{"version":1,"overrides":{"bone_corner_tl":{"category":[]}}}',
    '{"version":1,"overrides":{"bone_corner_tl":{"collision":true}}}',
])
def test_invalid_user_catalogue_falls_back_to_defaults(content):
    resources.tile_catalog_override_path().write_text(content, encoding="utf-8")
    entries, warnings = load_tile_catalog(("bone_corner_tl", "new_asset"))
    assert [(entry.category, entry.group) for entry in entries] == [
        ("bones", "single"), ("other", "single"),
    ]
    assert len(warnings) == 1
    assert "tile_catalog.json" in warnings[0]


@pytest.fixture
def library():
    pygame.font.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))
    names = ["bone_corner_tl", "frosthauch_tal", "galactic_stern", "unbekannt"]
    names += [f"stone_{number:02}" for number in range(30)]
    colors = {name: (44, 156, 232) for name in names}
    tiles = {}
    for name in names:
        tiles[name] = pygame.Surface((30, 30))
        tiles[name].fill(colors[name])
    chosen, favorites = [], []
    bounds = pygame.Rect(0, 0, 900, 620)
    view = TileLibrary(tiles, favorites, bounds, pygame.font.SysFont("Arial", 16), chosen.append)
    view.open()
    yield view, chosen, favorites, bounds
    view.close()


def _row_position(view, kind, target):
    for row, rect in view._visible_rows():
        if row.kind == kind and row.target == target:
            return rect.clip(view.list_rect).center
    raise AssertionError(f"Zeile für {target!r} fehlt.")


def _click(view, pos, button=1):
    return view.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button))


def test_category_group_favorite_and_tile_selection_use_the_same_keys(library):
    view, chosen, favorites, _ = library
    assert not any(row.kind == "tile" for row in view._rows)

    assert not _click(view, _row_position(view, "category", "frost"))
    frost = _row_position(view, "tile", "frosthauch_tal")
    assert [row.target for row in view._rows if row.kind == "tile"] == ["frosthauch_tal"]
    assert not _click(view, frost, button=3)
    assert favorites == ["frosthauch_tal"]

    assert not _click(view, _row_position(view, "group", ("frost", "single")))
    assert not any(row.kind == "tile" for row in view._rows)
    assert not _click(view, _row_position(view, "category", "favorites"))
    assert _click(view, _row_position(view, "tile", "frosthauch_tal"))
    assert chosen == ["frosthauch_tal"]


def test_search_by_theme_and_filename_and_enter_selects_unique_match(library):
    view, chosen, _, _ = library
    assert not view.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="GALAXIE stern.png"))
    assert [row.target for row in view._rows if row.kind == "tile"] == ["galactic_stern"]
    assert view.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert chosen == ["galactic_stern"]
    assert not _click(view, view.clear_rect.center)
    assert not any(row.kind == "tile" for row in view._rows)


def test_frostage_menu_art_is_excluded_from_tile_search(library):
    view, chosen, _, _ = library
    view.frost_assets = frostage_assets()
    view.open()
    view.handle_event(pygame.event.Event(pygame.TEXTINPUT, text="frostage_menu_single_player"))
    assert not view.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert not chosen
    assert not view._matches
    assert any(entry.category == "frostage_roof" for entry in view._entries)


def test_scroll_reaches_last_thumbnail_and_respects_viewport(library):
    view, chosen, _, bounds = library
    assert not _click(view, _row_position(view, "category", "dungeon"))
    outside = view.close_rect.center
    view.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-50, pos=outside))
    assert view._scroll == 0
    view.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-50, pos=view.list_rect.center))
    assert view._scroll > 0
    position = _row_position(view, "tile", "stone_29")
    surface = pygame.Surface(bounds.size)
    view.draw(surface, "stone_29")
    sample = view.list_rect.left + 8 + 32 + 4, position[1]
    assert surface.get_at(sample)[:3] == (44, 156, 232)
    assert _click(view, position)
    assert chosen == ["stone_29"]
