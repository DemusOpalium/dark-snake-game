"""Thematic display metadata for existing tile keys."""

import json
from dataclasses import dataclass
from pathlib import Path

from modules import resources


THEMES = {
    "bones": ("Knochen", ("bone", "boneshard")),
    "frost": ("Frost", ("frosthauch", "frostskull", "frozen", "frozenbase")),
    "galaxy": ("Galaxie", ("galactic", "planetset", "rifts")),
    "dungeon": ("Verlies", ("altar", "altar2", "stone", "border", "summoncircle")),
    "nature": ("Natur", ("verdant", "grass", "flowers", "cannabis")),
    "poison": ("Gift und Säure", ("venom", "acid")),
    "fire": ("Feuer", ("hellground", "burnedground", "lava", "smokeoverlay")),
    "gothic": ("Gotik", ("cathedral", "chorus", "satanic", "ornament", "ornament2")),
    "other": ("Sonstige", ()),
}
GROUPS = {
    "single": "Einzelkacheln 1×1",
    "multi": "Mehrfeldgrafiken",
    "walls": "Wandgrafiken",
    "stamps": "Stempel",
}


@dataclass(frozen=True)
class TileEntry:
    key: str
    category: str
    group: str


def _automatic_category(key: str) -> str:
    name = key.casefold()
    for category, (_, prefixes) in THEMES.items():
        if any(name == prefix or name.startswith(f"{prefix}_") for prefix in prefixes):
            return category
    return "other"


def _read_overrides(path: Path) -> dict[str, dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict) or type(data.get("version")) is not int or data["version"] != 1:
        raise ValueError("Katalogversion 1 erwartet.")
    entries = data.get("overrides")
    if not isinstance(entries, dict):
        raise ValueError("Katalogzuordnungen fehlen.")
    allowed_values = {"category": THEMES, "group": GROUPS}
    overrides = {}
    for name, fields in entries.items():
        if (not name.strip() or not isinstance(fields, dict) or not fields
                or any(field not in allowed_values or not isinstance(value, str)
                       or value not in allowed_values[field] for field, value in fields.items())):
            raise ValueError(f"Ungültige Zuordnung für {name}.")
        overrides[name.casefold().removesuffix(".png")] = fields
    return overrides


def load_tile_catalog(keys) -> tuple[tuple[TileEntry, ...], tuple[str, ...]]:
    """Classify every key once, layering user corrections over bundled defaults."""
    overrides: dict[str, dict[str, str]] = {}
    warnings = []
    paths = (resources.find_asset("graphics", "tile_catalog.json"),
             resources.tile_catalog_override_path())
    for path in paths:
        try:
            for name, fields in _read_overrides(path).items():
                overrides.setdefault(name, {}).update(fields)
        except (OSError, ValueError, RecursionError) as error:
            warnings.append(f"Katalog {path.name} konnte nicht gelesen werden. {error}")
    entries = []
    for key in sorted(keys, key=str.casefold):
        fields = overrides.get(key.casefold(), {})
        entries.append(TileEntry(key, fields.get("category") or _automatic_category(key),
                                 fields.get("group", "single")))
    return tuple(entries), tuple(warnings)
