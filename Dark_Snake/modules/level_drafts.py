"""Persistent, named drafts for the level editor."""

import json
import os
from itertools import count
from pathlib import Path, PureWindowsPath
from tempfile import NamedTemporaryFile

from config import GRID_HEIGHT, GRID_WIDTH
from modules.resources import custom_level_path, level_drafts_directory


LEVEL_FORMAT_VERSION = 1
COLLISION_TYPES = ("WALL", "BARRIER")
CollisionCells = dict[tuple[int, int], str]


def normalize_draft_name(name: str) -> str:
    """Accept a level name with or without its JSON suffix."""
    name = name.strip()
    if name.casefold().endswith(".json"):
        name = name[:-5].rstrip()
    if (not name or name.startswith(".") or name.endswith(".") or name.casefold().endswith(".json")
            or any(char in '<>:"/\\|?*' or ord(char) < 32 for char in name)
            or PureWindowsPath(f"{name}.json").is_reserved()):
        raise ValueError("Ungültiger Levelname. Bitte einen Dateinamen ohne Pfad verwenden.")
    return name


def _directory_entries(directory: Path) -> list[Path]:
    try:
        return list(directory.iterdir())
    except FileNotFoundError:
        return []


def list_drafts() -> list[str]:
    names = []
    for path in _directory_entries(level_drafts_directory()):
        if path.suffix.casefold() != ".json" or path.is_symlink() or not path.is_file():
            continue
        try:
            name = normalize_draft_name(path.name)
        except ValueError:
            continue
        if name == path.stem:
            names.append(name)
    return sorted(names, key=lambda name: (name.casefold(), name))


def suggest_draft_name() -> str:
    existing = {path.name.casefold() for path in _directory_entries(level_drafts_directory())}
    for number in count(1):
        name = f"Level_{number:03}"
        if f"{name}.json".casefold() not in existing:
            return name


def _matching_paths(directory: Path, name: str) -> list[Path]:
    filename = f"{name}.json".casefold()
    return [path for path in _directory_entries(directory) if path.name.casefold() == filename]


def _existing_draft(matches: list[Path], name: str) -> Path:
    if not matches:
        raise FileNotFoundError(f"Entwurf „{name}“ wurde nicht gefunden.")
    exact = [path for path in matches if path.stem == name]
    candidates = exact or matches
    if len(candidates) != 1:
        raise ValueError(f"Mehrere Entwürfe passen zum Namen „{name}“.")
    path = candidates[0]
    if path.is_symlink() or not path.is_file():
        raise OSError(f"„{path.name}“ ist keine reguläre Leveldatei.")
    return path


def _validate_map(level_map) -> None:
    if not isinstance(level_map, list) or len(level_map) != GRID_HEIGHT:
        raise ValueError("Ungültige Level-Höhe.")
    for row in level_map:
        if not isinstance(row, list) or len(row) != GRID_WIDTH:
            raise ValueError("Ungültige Level-Breite.")
        if any(tile is not None and not isinstance(tile, str) for tile in row):
            raise ValueError("Ungültige Level-Kachel.")


def _read_json(path: Path):
    with path.open(encoding="utf-8-sig") as file:
        try:
            return json.load(file)
        except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
            raise ValueError("Die Leveldatei enthält ungültiges JSON.") from error


def _validate_collision_cell(x, y, kind) -> None:
    if type(x) is not int or type(y) is not int or not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
        raise ValueError("Ungültige Koordinaten in der Kollisionsebene.")
    if kind not in COLLISION_TYPES:
        raise ValueError("Ungültiger Typ in der Kollisionsebene.")


def _decode_level(document) -> tuple[list, CollisionCells]:
    if isinstance(document, list):
        _validate_map(document)
        return document, {}
    if not isinstance(document, dict) or type(document.get("version")) is not int:
        raise ValueError("Ungültiges Level-Format.")
    if document["version"] != LEVEL_FORMAT_VERSION:
        raise ValueError("Diese Level-Formatversion wird nicht unterstützt.")
    if document.keys() != {"version", "graphics", "collision"} or not isinstance(document["collision"], list):
        raise ValueError("Ungültige Level-Ebenen.")

    graphics = document["graphics"]
    _validate_map(graphics)
    collision = {}
    for cell in document["collision"]:
        if not isinstance(cell, dict) or cell.keys() != {"x", "y", "type"}:
            raise ValueError("Ungültiger Eintrag in der Kollisionsebene.")
        x, y, kind = cell["x"], cell["y"], cell["type"]
        _validate_collision_cell(x, y, kind)
        if (x, y) in collision:
            raise ValueError("Doppelte Zelle in der Kollisionsebene.")
        collision[(x, y)] = kind
    return graphics, collision


def read_level(name: str) -> tuple[list, CollisionCells]:
    """Read a draft's graphics and collision cells, including graphics-only legacy files."""
    name = normalize_draft_name(name)
    matches = _matching_paths(level_drafts_directory(), name)
    return _decode_level(_read_json(_existing_draft(matches, name)))


def read_draft(name: str) -> list:
    return read_level(name)[0]


def legacy_map_exists() -> bool:
    return Path(custom_level_path()).is_file()


def read_legacy_map() -> list:
    graphics = _read_json(Path(custom_level_path()))
    _validate_map(graphics)
    return graphics


def _publish_new_draft(source: Path, destination: Path) -> None:
    """Publish a complete file without clobbering a concurrent first save."""
    if os.name == "nt":
        source.rename(destination)
    else:
        os.link(source, destination)


def _level_document(graphics: list, collision: CollisionCells) -> dict:
    if not isinstance(collision, dict):
        raise ValueError("Ungültige Kollisionsebene.")
    for position, kind in collision.items():
        if not isinstance(position, tuple) or len(position) != 2:
            raise ValueError("Ungültige Koordinaten in der Kollisionsebene.")
        _validate_collision_cell(*position, kind)
    return {
        "version": LEVEL_FORMAT_VERSION,
        "graphics": graphics,
        "collision": [{"x": x, "y": y, "type": collision[(x, y)]}
                      for x, y in sorted(collision, key=lambda cell: (cell[1], cell[0]))],
    }


def write_draft(name: str, level_map: list, *, collision: CollisionCells | None = None,
                replace: bool = False) -> str:
    """Save a draft atomically. A graphics-only update keeps existing collision cells."""
    name = normalize_draft_name(name)
    _validate_map(level_map)
    directory = level_drafts_directory()
    matches = _matching_paths(directory, name)
    if replace:
        path = _existing_draft(matches, name)
        previous = _read_json(path)
        _, previous_collision = _decode_level(previous)
        if collision is None and isinstance(previous, dict):
            collision = previous_collision
    else:
        if matches:
            raise FileExistsError(f"Ein Entwurf mit dem Namen „{name}“ existiert bereits.")
        path = directory / f"{name}.json"

    document = level_map if collision is None else _level_document(level_map, collision)
    if not replace:
        directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                prefix=".level-", suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            json.dump(document, file, ensure_ascii=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        if replace:
            temporary.replace(path)
        else:
            _publish_new_draft(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path.stem
