"""Persistent, named drafts for the level editor."""

import json
import os
from itertools import count
from pathlib import Path, PureWindowsPath
from tempfile import NamedTemporaryFile

from config import GRID_HEIGHT, GRID_WIDTH
from modules.resources import custom_level_path, level_drafts_directory


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


def _read_map(path: Path) -> list:
    with path.open(encoding="utf-8-sig") as file:
        try:
            level_map = json.load(file)
        except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
            raise ValueError("Die Leveldatei enthält ungültiges JSON.") from error
    _validate_map(level_map)
    return level_map


def read_draft(name: str) -> list:
    name = normalize_draft_name(name)
    matches = _matching_paths(level_drafts_directory(), name)
    return _read_map(_existing_draft(matches, name))


def legacy_map_exists() -> bool:
    return Path(custom_level_path()).is_file()


def read_legacy_map() -> list:
    return _read_map(Path(custom_level_path()))


def _publish_new_draft(source: Path, destination: Path) -> None:
    """Publish a complete file without clobbering a concurrent first save."""
    if os.name == "nt":
        source.rename(destination)
    else:
        os.link(source, destination)


def write_draft(name: str, level_map: list, *, replace: bool = False) -> str:
    """Save a new draft or explicitly replace an existing draft of that name."""
    name = normalize_draft_name(name)
    _validate_map(level_map)
    directory = level_drafts_directory()
    matches = _matching_paths(directory, name)
    if replace:
        path = _existing_draft(matches, name)
    else:
        if matches:
            raise FileExistsError(f"Ein Entwurf mit dem Namen „{name}“ existiert bereits.")
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{name}.json"

    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                prefix=".level-", suffix=".tmp", delete=False) as file:
            temporary = Path(file.name)
            json.dump(level_map, file, ensure_ascii=False)
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
