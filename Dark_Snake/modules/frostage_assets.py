"""Resolve the bundled FrostAge catalogue and load artwork on demand."""

from dataclasses import dataclass
from functools import lru_cache
import json
import logging
from pathlib import Path, PurePosixPath

import pygame

from modules.resources import find_asset


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class FrostAgeAsset:
    id: str
    name: str
    category: str
    width: int
    height: int
    cells: tuple[int, int]
    orientation: str
    has_alpha: bool
    transparent_pixels: bool
    sha256: str
    path: Path


@lru_cache(maxsize=1)
def frostage_assets() -> dict[str, FrostAgeAsset]:
    """Load the generated metadata from the game assets, without decoding PNGs."""
    catalog = find_asset("graphics", "frostage", "catalog.json")
    try:
        data = json.loads(catalog.read_text(encoding="utf-8"))
        if data["version"] != 1:
            raise ValueError("Unbekannte FrostAge-Katalogversion.")
        return {
            entry["id"]: FrostAgeAsset(
                id=entry["id"],
                name=PurePosixPath(entry["source"]).name,
                category=entry["category"],
                width=entry["width"],
                height=entry["height"],
                cells=tuple(entry["cells"]),
                orientation=entry["orientation"],
                has_alpha=entry["has_alpha"],
                transparent_pixels=entry["transparent_pixels"],
                sha256=entry["sha256"],
                path=catalog.parent / entry["file"],
            )
            for entry in data["assets"]
        }
    except (OSError, ValueError, KeyError, TypeError) as error:
        LOGGER.error("FrostAge-Katalog konnte nicht geladen werden: %s (%s)", catalog, error)
        return {}


@lru_cache(maxsize=16)
def _load_frostage_image(path: Path) -> pygame.Surface | None:
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except (OSError, pygame.error) as error:
        LOGGER.error("FrostAge-Grafik konnte nicht geladen werden: %s (%s)", path, error)
        return None


def load_frostage_image(asset_id: str) -> pygame.Surface | None:
    """Get the unscaled artwork after display initialization."""
    asset = frostage_assets().get(asset_id)
    if asset is None or pygame.display.get_surface() is None:
        return None
    return _load_frostage_image(asset.path)
