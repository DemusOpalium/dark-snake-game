"""Persistent, named drafts for the level editor."""

import json
import os
from dataclasses import asdict, dataclass, field
from itertools import count
from pathlib import Path, PureWindowsPath
from tempfile import NamedTemporaryFile

from config import GRID_HEIGHT, GRID_WIDTH
from modules.graphic_objects import GraphicObject, GraphicObjects, place_graphic_object
from modules.level_effects import CellEffects, DamageField, EffectCells, SlowField
from modules.resources import custom_level_path, level_drafts_directory
from modules.roof_settings import RoofVisibility


COLLISION_FORMAT_VERSION = 1
EFFECT_FORMAT_VERSION = 2
LEVEL_FORMAT_VERSION = 3
COLLISION_TYPES = ("WALL", "BARRIER")
CollisionCells = dict[tuple[int, int], str]
ROOF_FIELDS = {"roofs", "roof_visibility"}


@dataclass(frozen=True, slots=True)
class LevelDocument:
    graphics: list
    collision: CollisionCells = field(default_factory=dict)
    effects: EffectCells = field(default_factory=dict)
    objects: GraphicObjects = field(default_factory=dict)
    roofs: GraphicObjects = field(default_factory=dict)
    roof_visibility: RoofVisibility = field(default_factory=RoofVisibility)


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


def _validate_position(x, y, layer: str) -> None:
    if type(x) is not int or type(y) is not int or not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
        raise ValueError(f"Ungültige Koordinaten in der {layer}.")


def _validate_collision_cell(x, y, kind) -> None:
    _validate_position(x, y, "Kollisionsebene")
    if kind not in COLLISION_TYPES:
        raise ValueError("Ungültiger Typ in der Kollisionsebene.")


def _decode_effects(records) -> EffectCells:
    if not isinstance(records, list):
        raise ValueError("Ungültige Effektebene.")
    effects = {}
    for record in records:
        if (not isinstance(record, dict) or not {"x", "y"} <= record.keys()
                or record.keys() - {"x", "y", "damage", "slow"}
                or record.keys().isdisjoint(("damage", "slow"))):
            raise ValueError("Ungültiger Eintrag in der Effektebene.")
        x, y = record["x"], record["y"]
        _validate_position(x, y, "Effektebene")
        if (x, y) in effects:
            raise ValueError("Doppelte Zelle in der Effektebene.")
        damage, slow = None, None
        if "damage" in record:
            fields = record["damage"]
            if (not isinstance(fields, dict) or not {"amount", "interval"} <= fields.keys()
                    or fields.keys() - {"amount", "interval", "duration"}):
                raise ValueError("Ungültige Einstellungen für ein Schadensfeld.")
            damage = DamageField(**fields)
        if "slow" in record:
            fields = record["slow"]
            if not isinstance(fields, dict) or fields.keys() != {"percent"}:
                raise ValueError("Ungültige Einstellungen für ein Verlangsamungsfeld.")
            slow = SlowField(**fields)
        effects[(x, y)] = CellEffects(damage, slow)
    return effects


def _decode_objects(records, layer="Grafikobjektebene") -> GraphicObjects:
    if not isinstance(records, list):
        raise ValueError(f"Ungültige {layer}.")
    objects = {}
    for record in records:
        if not isinstance(record, dict) or record.keys() != {"x", "y", "asset_id", "width", "height"}:
            raise ValueError(f"Ungültiger Eintrag in der {layer}.")
        x, y = record["x"], record["y"]
        _validate_position(x, y, layer)
        item = GraphicObject(record["asset_id"], record["width"], record["height"])
        if not place_graphic_object(objects, (x, y), item):
            raise ValueError(f"Objekte in der {layer} überlappen sich oder reichen aus der Karte.")
    return objects


def _decode_roof_visibility(settings) -> RoofVisibility:
    if not isinstance(settings, dict) or settings.keys() != {"enabled", "radius", "transparency", "softness"}:
        raise ValueError("Ungültige Einstellungen für das Dach-Sichtfenster.")
    return RoofVisibility(**settings)


def _decode_level(document) -> LevelDocument:
    if isinstance(document, list):
        _validate_map(document)
        return LevelDocument(document)
    if not isinstance(document, dict) or type(document.get("version")) is not int:
        raise ValueError("Ungültiges Level-Format.")
    version = document["version"]
    if version not in (COLLISION_FORMAT_VERSION, EFFECT_FORMAT_VERSION, LEVEL_FORMAT_VERSION):
        raise ValueError("Diese Level-Formatversion wird nicht unterstützt.")
    fields = {"version", "graphics", "collision"}
    if version >= EFFECT_FORMAT_VERSION:
        fields.add("effects")
    if version == LEVEL_FORMAT_VERSION:
        fields.add("objects")
    allowed = fields | ROOF_FIELDS if version == LEVEL_FORMAT_VERSION else fields
    if not fields <= document.keys() <= allowed or not isinstance(document["collision"], list):
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
    return LevelDocument(
        graphics, collision, _decode_effects(document.get("effects", [])),
        _decode_objects(document.get("objects", [])),
        _decode_objects(document.get("roofs", []), "Dachebene"),
        _decode_roof_visibility(document["roof_visibility"]) if "roof_visibility" in document else RoofVisibility(),
    )


def read_level_file(path: Path) -> LevelDocument:
    """Read a versioned level document from a draft or bundled resource."""
    return _decode_level(_read_json(path))


def load_level_document(name: str) -> LevelDocument:
    """Read all layers and settings of a named draft."""
    name = normalize_draft_name(name)
    matches = _matching_paths(level_drafts_directory(), name)
    return read_level_file(_existing_draft(matches, name))


def read_level_document(name: str) -> tuple[list, CollisionCells, EffectCells, GraphicObjects]:
    """Read the original four layers of a named draft."""
    document = load_level_document(name)
    return document.graphics, document.collision, document.effects, document.objects


def read_level_layers(name: str) -> tuple[list, CollisionCells, EffectCells]:
    graphics, collision, effects, _ = read_level_document(name)
    return graphics, collision, effects


def read_level(name: str) -> tuple[list, CollisionCells]:
    """Read a draft's graphics and collision cells, including graphics-only legacy files."""
    graphics, collision, _ = read_level_layers(name)
    return graphics, collision


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


def _effect_records(effects: EffectCells) -> list[dict]:
    if not isinstance(effects, dict):
        raise ValueError("Ungültige Effektebene.")
    records = []
    for position, cell in effects.items():
        if not isinstance(position, tuple) or len(position) != 2:
            raise ValueError("Ungültige Koordinaten in der Effektebene.")
        x, y = position
        _validate_position(x, y, "Effektebene")
        if not isinstance(cell, CellEffects) or (cell.damage is None and cell.slow is None):
            raise ValueError("Ungültiger Eintrag in der Effektebene.")
        record = {"x": x, "y": y}
        if cell.damage is not None:
            record["damage"] = {
                "amount": cell.damage.amount,
                "interval": cell.damage.interval,
                "duration": cell.damage.duration,
            }
        if cell.slow is not None:
            record["slow"] = {"percent": cell.slow.percent}
        records.append(record)
    return sorted(records, key=lambda record: (record["y"], record["x"]))


def _object_records(objects: GraphicObjects, layer="Grafikobjektebene") -> list[dict]:
    if not isinstance(objects, dict):
        raise ValueError(f"Ungültige {layer}.")
    records = []
    for position, item in objects.items():
        if not isinstance(position, tuple) or len(position) != 2 or not isinstance(item, GraphicObject):
            raise ValueError(f"Ungültiger Eintrag in der {layer}.")
        x, y = position
        _validate_position(x, y, layer)
        records.append({"x": x, "y": y, "asset_id": item.asset_id, "width": item.width, "height": item.height})
    _decode_objects(records, layer)
    return sorted(records, key=lambda record: (record["y"], record["x"]))


def _level_document(graphics: list, collision: CollisionCells, effects: EffectCells | None,
                    objects: GraphicObjects | None, roofs: GraphicObjects | None,
                    roof_visibility: RoofVisibility | None) -> dict:
    if not isinstance(collision, dict):
        raise ValueError("Ungültige Kollisionsebene.")
    for position, kind in collision.items():
        if not isinstance(position, tuple) or len(position) != 2:
            raise ValueError("Ungültige Koordinaten in der Kollisionsebene.")
        _validate_collision_cell(*position, kind)
    document = {
        "version": COLLISION_FORMAT_VERSION,
        "graphics": graphics,
        "collision": [{"x": x, "y": y, "type": collision[(x, y)]}
                      for x, y in sorted(collision, key=lambda cell: (cell[1], cell[0]))],
    }
    if effects is not None:
        document["version"] = EFFECT_FORMAT_VERSION
        document["effects"] = _effect_records(effects)
    if objects is not None or roofs is not None or roof_visibility is not None:
        document["version"] = LEVEL_FORMAT_VERSION
        document.setdefault("effects", [])
        document["objects"] = _object_records(objects) if objects is not None else []
    if roofs is not None:
        document["roofs"] = _object_records(roofs, "Dachebene")
    if roof_visibility is not None:
        if not isinstance(roof_visibility, RoofVisibility):
            raise ValueError("Ungültige Einstellungen für das Dach-Sichtfenster.")
        document["roof_visibility"] = asdict(roof_visibility)
    return document


def write_draft(name: str, level_map: list, *, collision: CollisionCells | None = None,
                effects: EffectCells | None = None,
                objects: GraphicObjects | None = None,
                roofs: GraphicObjects | None = None,
                roof_visibility: RoofVisibility | None = None,
                replace: bool = False) -> str:
    """Save a draft atomically, retaining existing layers omitted by the caller."""
    name = normalize_draft_name(name)
    _validate_map(level_map)
    directory = level_drafts_directory()
    matches = _matching_paths(directory, name)
    if replace:
        path = _existing_draft(matches, name)
        previous = _read_json(path)
        previous_level = _decode_level(previous)
        if isinstance(previous, dict):
            if collision is None:
                collision = previous_level.collision
            if effects is None and previous["version"] >= EFFECT_FORMAT_VERSION:
                effects = previous_level.effects
            if objects is None and previous["version"] == LEVEL_FORMAT_VERSION:
                objects = previous_level.objects
            if roofs is None and "roofs" in previous:
                roofs = previous_level.roofs
            if roof_visibility is None and "roof_visibility" in previous:
                roof_visibility = previous_level.roof_visibility
    else:
        if matches:
            raise FileExistsError(f"Ein Entwurf mit dem Namen „{name}“ existiert bereits.")
        path = directory / f"{name}.json"

    document = (
        level_map if all(layer is None for layer in (collision, effects, objects, roofs, roof_visibility))
        else _level_document(level_map, {} if collision is None else collision, effects, objects, roofs, roof_visibility)
    )
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
