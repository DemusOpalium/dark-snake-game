import json
import os
from collections import Counter
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame
import pytest

from modules import resources
from modules.frostage_assets import frostage_assets, load_frostage_image


def test_frostage_catalogue_covers_the_original_artwork_and_corrected_footprints():
    assets = frostage_assets()

    assert len(assets) == 175
    assert Counter(asset.category for asset in assets.values()) == {
        "ground": 44, "walls": 24, "objects": 50, "roof": 8, "aoe": 11,
        "enemies": 8, "projectiles": 13, "items": 5, "menu": 12,
    }
    assert len({asset.sha256 for asset in assets.values()}) == 175
    assert sum(asset.transparent_pixels for asset in assets.values()) == 107
    assert all(asset.has_alpha and asset.path.is_file() for asset in assets.values())
    manifest = json.loads(resources.find_asset("graphics", "frostage", "catalog.json").read_text(encoding="utf-8"))
    assert {entry["source"] for entry in manifest["assets"]} == {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "GamePICs" / "Incoming" / "Frost_Tiles").rglob("*.png")
    }

    assert assets["frostage_10x1_001"].cells == (1, 10)
    assert assets["frostage_10x1_001"].orientation == "portrait"
    assert assets["frostage_1x10_001"].cells == (10, 1)
    assert assets["frostage_1x10_001"].orientation == "landscape"
    assert assets["frostage_2x1_011"].cells == (1, 2)
    assert assets["frostage_menu_statistics"].name == "Frostbuttons statisktic.png"


def test_frostage_image_uses_frozen_asset_path_and_preserves_source_alpha(tmp_path, monkeypatch):
    pygame.display.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1), pygame.HIDDEN)

    original = frostage_assets()["frostage_roof_005"]
    entry = {
        "id": original.id,
        "source": f"GamePICs/Incoming/Frost_Tiles/Dach/{original.name}",
        "file": original.path.name,
        "category": original.category,
        "width": original.width,
        "height": original.height,
        "orientation": original.orientation,
        "cells": list(original.cells),
        "has_alpha": original.has_alpha,
        "transparent_pixels": original.transparent_pixels,
        "sha256": original.sha256,
    }
    directory = tmp_path / "assets" / "graphics" / "frostage"
    directory.mkdir(parents=True)
    (directory / original.path.name).write_bytes(original.path.read_bytes())
    (directory / "catalog.json").write_text(json.dumps({"version": 1, "assets": [entry]}), encoding="utf-8")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    frostage_assets.cache_clear()
    try:
        bundled = frostage_assets()[original.id]
        image = load_frostage_image(original.id)
        assert bundled.path == directory / original.path.name
        assert image.get_size() == (original.width, original.height)
        assert pygame.mask.from_surface(image, 254).count() < original.width * original.height
        assert load_frostage_image(original.id) is image
        assert load_frostage_image("not-an-asset") is None
    finally:
        frostage_assets.cache_clear()
