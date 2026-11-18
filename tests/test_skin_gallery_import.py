"""Head/Body archive import: exact bytes, real menu and 1P/2P behavior.

Only visual/manual suitability remains an explicit Windows review task.
"""
import hashlib
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
from modules.game import Game
from modules.resources import find_asset

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "Dark_Snake/assets/graphics/skins_catalog.json"
CATALOG = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
IMPORTED = [entry for entry in CATALOG["candidates"]
            if entry["import_status"] == "imported"]


def _git_sha(data):
    """Git SHA, deliberately not SHA-256."""
    return hashlib.sha1(f"blob {len(data)}".encode("ascii") + bytes([0]) + data).hexdigest()


def test_skin_catalog_explains_all_staged_candidates():
    assert CATALOG["schema_version"] == 1
    assert CATALOG["unlock_system"].startswith("PLANNED")
    entries = CATALOG["candidates"]
    assert len(entries) == 68
    assert len(IMPORTED) == 53
    assert len([e for e in entries if e["type"] == "head"]) == 53
    assert len([e for e in entries if e["type"] == "body"]) == 15
    assert len({e["id"] for e in entries}) == len(entries)
    assert sum(e["import_status"] == "already_present" for e in entries) == 11
    assert sum(e["import_status"] == "manual_review_required" for e in entries) == 4
    for entry in entries:
        assert entry["unlock_rule"] is None
        assert entry["source_path"].startswith("GamePICs/")
        assert (ROOT / entry["source_path"]).is_file()
        if entry["import_status"] == "manual_review_required":
            assert entry["runtime_asset"] is None
            continue
        assert entry["runtime_asset"].startswith("graphics/")
        assert find_asset(*entry["runtime_asset"].split("/")).is_file()


@pytest.mark.parametrize("entry", IMPORTED, ids=lambda entry: entry["id"])
def test_imported_skin_keeps_original_binary_and_is_drawable(entry):
    source = (ROOT / entry["source_path"]).read_bytes()
    runtime_path = find_asset(*entry["runtime_asset"].split("/"))
    runtime = runtime_path.read_bytes()
    assert source == runtime
    assert len(runtime) == entry["bytes"]
    assert _git_sha(runtime) == entry["git_blob_sha"]
    image = pygame.image.load(str(runtime_path)).convert_alpha()
    assert min(image.get_size()) >= 8
    assert image.get_bounding_rect(min_alpha=8).width > 0
    assert image.get_bounding_rect(min_alpha=8).height > 0
    for size in (30, 60):
        preview = pygame.transform.smoothscale(image, (size, size))
        assert preview.get_size() == (size, size)
        assert preview.get_bounding_rect(min_alpha=8).width > 0


@pytest.mark.parametrize("players", [1, 2])
def test_new_head_and_body_are_selectable_saved_and_render_in_game(players, tmp_path, monkeypatch):
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path)
    head = next(e for e in IMPORTED if e["type"] == "head")
    body = next(e for e in IMPORTED if e["type"] == "body")
    head_filename = Path(head["runtime_asset"]).name
    body_filename = Path(body["runtime_asset"]).name

    game = Game(headless=True)
    menu = game.options_menu
    for player in range(1, players + 1):
        head_entry = next((item for item in menu.head_options if item[0] == head_filename), None)
        body_entry = next((item for item in menu.body_options if item[0] == body_filename), None)
        assert head_entry is not None and body_entry is not None
        menu.current_tab = "Heads"
        menu.current_selected_img = head_entry
        menu.assign_image(player)
        menu.current_tab = "Bodies"
        menu.current_selected_img = body_entry
        menu.assign_image(player)
    menu.save()
    assert game.settings["custom_head_p1"] == head_filename
    assert game.settings["custom_body_p1"] == body_filename
    if players == 2:
        assert game.settings["custom_head_p2"] == head_filename
        assert game.settings["custom_body_p2"] == body_filename

    # A headless Game intentionally bypasses load_settings(); reload with the
    # real GUI initialization, still using SDL's dummy Windows CI display.
    restored = Game()
    assert restored.settings["custom_head_p1"] == head_filename
    assert restored.settings["custom_body_p1"] == body_filename
    selected_head = restored.options_menu.get_skin_image("Heads", head_filename)
    selected_body = restored.options_menu.get_skin_image("Bodies", body_filename)
    assert selected_head is not None and selected_body is not None
    restored.start_game(players)
    restored.draw()
    assert restored.game_state is not None
    # Both previews must resolve real bundled images, not the staged source paths.
    restored.options_menu.draw(restored.screen)
    assert selected_head.get_bounding_rect(min_alpha=8).width > 0
    assert selected_body.get_bounding_rect(min_alpha=8).width > 0


def test_full_new_gallery_clamps_scroll_to_last_head_and_body():
    game = Game(headless=True)
    menu = game.options_menu
    surface = pygame.Surface((1350, 930))
    menu.draw(surface)
    for tab, options in (("Heads", menu.head_options),
                         ("Bodies", menu.body_options)):
        menu.current_tab = tab
        menu.inventory_scroll_offset = -999999
        menu.draw(surface)
        assert len(options) > 13
        assert -999999 < menu.inventory_scroll_offset <= 0
        last_row = (len(options) - 1) // 4
        width = (menu.inventory_grid_rect.width - 5 * 10) // 4
        y = menu.inventory_grid_rect.y + 10 + last_row * (width + 10) + menu.inventory_scroll_offset
        assert menu.inventory_grid_rect.top <= y < menu.inventory_grid_rect.bottom


def test_gallery_sprites_are_reused_across_games_without_redecoding():
    from modules.options_menu import _cached_skin_options

    first = Game(headless=True)
    previous = _cached_skin_options.cache_info()
    second = Game(headless=True)
    current = _cached_skin_options.cache_info()
    assert current.hits >= previous.hits + 2
    assert first.options_menu.head_options[0][2] is second.options_menu.head_options[0][2]
    assert first.options_menu.body_options[0][2] is second.options_menu.body_options[0][2]
