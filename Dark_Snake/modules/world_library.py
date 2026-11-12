"""Persistent World Tree metadata over the existing named level drafts."""

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import NAMESPACE_URL, uuid4, uuid5

from modules.level_drafts import list_drafts, normalize_draft_name
from modules.resources import world_library_path

SCHEMA_VERSION = 1
DRAFT_NAMESPACE = uuid5(NAMESPACE_URL, "https://github.com/DemusOpalium/dark-snake-game/drafts")


def _label(name: str) -> str:
    if not isinstance(name, str):
        raise ValueError("Der Name muss Text sein.")
    name = name.strip()
    if not name or any(ord(char) < 32 for char in name):
        raise ValueError("Bitte einen Namen ohne Zeilenumbrüche eingeben.")
    return name


@dataclass(frozen=True, slots=True)
class World:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Level:
    id: str
    draft_name: str
    name: str
    world_id: str | None
    available: bool = True


@contextmanager
def _catalog_lock(path: Path):
    """Serialize a read-modify-write without locking the file being replaced."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_name(".world-library.lock").open("a+b") as lock:
        lock.seek(0)
        try:
            if os.name == "nt":
                from msvcrt import LK_NBLCK, locking

                locking(lock.fileno(), LK_NBLCK, 1)
            else:
                from fcntl import LOCK_EX, LOCK_NB, flock

                flock(lock.fileno(), LOCK_EX | LOCK_NB)
        except OSError as error:
            raise OSError("Die Weltbibliothek wird bereits bearbeitet.") from error
        yield


class WorldLibrary:
    def __init__(self, worlds: dict[str, World], levels: dict[str, Level],
                 game_order: tuple[str, ...]):
        self.worlds = worlds
        self.levels = levels
        self.game_order = game_order

    @classmethod
    def load(cls):
        """Load the index and discover older drafts without writing either file."""
        return cls._load(world_library_path())

    @classmethod
    def _load(cls, path: Path):
        if path.is_symlink():
            raise OSError("Die Weltbibliothek muss eine reguläre Datei sein.")
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except FileNotFoundError:
            raw = None
        except UnicodeError as error:
            raise ValueError("Die Weltbibliothek ist keine gültige UTF-8-Datei.") from error
        drafts = set(list_drafts())
        if raw is None:
            library = cls({}, {}, ())
        else:
            library = cls._decode(raw, drafts)
        indexed = {level.draft_name for level in library.levels.values()}
        for name in sorted(drafts - indexed, key=lambda name: (name.casefold(), name)):
            level_id = uuid5(DRAFT_NAMESPACE, name).hex
            if level_id in library.levels:
                raise ValueError("Zwei Entwürfe verwenden dieselbe Level-ID.")
            library.levels[level_id] = Level(level_id, name, name, None)
        return library

    @classmethod
    def _decode(cls, raw: str, drafts: set[str]):
        try:
            data = json.loads(raw)
        except (ValueError, RecursionError) as error:
            raise ValueError("Die Weltbibliothek enthält ungültiges JSON.") from error
        if not isinstance(data, dict) or type(data.get("version")) is not int:
            raise ValueError("Die Weltbibliothek hat kein gültiges Format.")
        if data["version"] != SCHEMA_VERSION:
            raise ValueError("Diese Version der Weltbibliothek wird nicht unterstützt.")
        if (set(data) != {"version", "worlds", "levels", "game_order"}
                or any(not isinstance(data[key], list) for key in ("worlds", "levels", "game_order"))):
            raise ValueError("Die Weltbibliothek hat kein gültiges Format.")
        try:
            worlds = {}
            world_names = set()
            for record in data["worlds"]:
                world = World(**record)
                if (world.id != _label(world.id) or world.name != _label(world.name)
                        or world.id in worlds or world.name.casefold() in world_names):
                    raise ValueError("Ungültige oder doppelte Themenwelt.")
                worlds[world.id] = world
                world_names.add(world.name.casefold())

            levels = {}
            filenames = set()
            for record in data["levels"]:
                draft_name = record["draft_name"]
                level = Level(**record, available=draft_name in drafts)
                if (level.id != _label(level.id) or level.name != _label(level.name)
                        or normalize_draft_name(draft_name) != draft_name
                        or level.id in levels or draft_name in filenames
                        or level.world_id is not None and level.world_id not in worlds):
                    raise ValueError("Ungültiger oder doppelter Level-Eintrag.")
                levels[level.id] = level
                filenames.add(draft_name)

            order = tuple(data["game_order"])
            if len(set(order)) != len(order) or any(level_id not in levels for level_id in order):
                raise ValueError("Doppelte oder fehlende Level-ID in der Spielreihenfolge.")
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            raise ValueError("Die Weltbibliothek enthält ungültige Einträge.") from error
        return cls(worlds, levels, order)

    def _payload(self):
        return {
            "version": SCHEMA_VERSION,
            "worlds": [{"id": world.id, "name": world.name} for world in self.worlds.values()],
            "levels": [{"id": level.id, "draft_name": level.draft_name, "name": level.name,
                        "world_id": level.world_id} for level in self.levels.values()],
            "game_order": list(self.game_order),
        }

    @staticmethod
    def _save(path: Path, payload: dict):
        temporary = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                    prefix=".world-library-", suffix=".tmp", delete=False) as file:
                temporary = Path(file.name)
                json.dump(payload, file, ensure_ascii=False, indent=2)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            temporary.replace(path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _change(self, edit):
        path = world_library_path()
        with _catalog_lock(path):
            current = self._load(path)
            previous = current._payload()
            result = edit(current)
            payload = current._payload()
            if payload != previous:
                self._save(path, payload)
            self.worlds, self.levels, self.game_order = current.worlds, current.levels, current.game_order
        return result

    def level_for_draft(self, draft_name: str) -> Level | None:
        return next((level for level in self.levels.values() if level.draft_name == draft_name), None)

    def _require_level(self, level_id: str) -> Level:
        if level_id not in self.levels:
            raise ValueError("Der Level-Eintrag wurde nicht gefunden.")
        return self.levels[level_id]

    def _require_world(self, world_id: str) -> World:
        if world_id not in self.worlds:
            raise ValueError("Die Themenwelt wurde nicht gefunden.")
        return self.worlds[world_id]

    def _set_world(self, world_id: str, name: str):
        if any(world.id != world_id and world.name.casefold() == name.casefold()
               for world in self.worlds.values()):
            raise ValueError("Eine Themenwelt mit diesem Namen existiert bereits.")
        self.worlds[world_id] = World(world_id, name)

    def create_world(self, name: str) -> str:
        name = _label(name)
        world_id = uuid4().hex
        self._change(lambda library: library._set_world(world_id, name))
        return world_id

    def rename_world(self, world_id: str, name: str):
        name = _label(name)

        def edit(library):
            library._require_world(world_id)
            library._set_world(world_id, name)

        self._change(edit)

    def rename_level(self, level_id: str, name: str):
        name = _label(name)
        self._change(lambda library: library._set_level(level_id, name=name))

    def assign_level(self, level_id: str, world_id: str | None):
        def edit(library):
            if world_id is not None:
                library._require_world(world_id)
            library._set_level(level_id, world_id=world_id)

        self._change(edit)

    def _set_level(self, level_id: str, **fields):
        self.levels[level_id] = replace(self._require_level(level_id), **fields)

    def add_to_game_order(self, level_id: str):
        def edit(library):
            if not library._require_level(level_id).available:
                raise ValueError("Die Leveldatei fehlt.")
            if level_id not in library.game_order:
                library.game_order += (level_id,)

        self._change(edit)

    def remove_from_game_order(self, level_id: str):
        def edit(library):
            library.game_order = tuple(entry for entry in library.game_order if entry != level_id)

        self._change(edit)

    def move_in_game_order(self, level_id: str, offset: int):
        def edit(library):
            if level_id in library.game_order:
                order = list(library.game_order)
                current = order.index(level_id)
                destination = max(0, min(len(order) - 1, current + offset))
                order.insert(destination, order.pop(current))
                library.game_order = tuple(order)

        self._change(edit)
