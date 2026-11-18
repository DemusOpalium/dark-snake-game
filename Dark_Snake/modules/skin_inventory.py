"""Persistent cosmetic Snake inventory (Classic, version 1).

This module does not change game balance. All unlocks are based exclusively on
confirmed career awards, which themselves come from committed round records.
At most ONE cosmetic is granted per completed round, including backlogged
rank rewards. Reward eligibility for achievements, bosses and chests remains
reserved until those event types are actually implemented.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from modules.career_ranks import _validate_state as validate_career_state, career_rank
from modules.resources import (
    find_asset, find_asset_directory, skin_inventory_file_path,
)
from modules.round_progress import _journal_lock


SKIN_REGISTRY_VERSION = 1
INVENTORY_SCHEMA_VERSION = 1
GROUPS = frozenset({"starter", "career", "achievement", "boss", "reserve"})
SKIN_TYPE = {"Heads": "head", "Bodies": "body"}


def _uuid_ok(value):
    if not isinstance(value, str):
        return False
    try:
        uid = UUID(value)
    except (ValueError, TypeError, AttributeError):
        return False
    return uid.version == 4 and uid.hex == value


class SkinRegistry:
    """Stable IDs for *all* existing runtime PNGs; the registry is read once."""

    def __init__(self, data):
        if (not isinstance(data, dict) or data.get("schema_version") != SKIN_REGISTRY_VERSION
                or not isinstance(data.get("skins"), list) or not data["skins"]):
            raise ValueError("Unsupported Snake skin registry.")
        entries = data["skins"]
        ids = set()
        names = set()
        starters = set()
        by_id = {}
        by_filename = {}
        ranks = set()
        career = []
        for item in entries:
            if not isinstance(item, dict) or set(item) != {
                "id", "type", "filename", "group", "required_rank"
            }:
                raise ValueError("Malformed Snake registry row.")
            skin_id, typ, filename = item["id"], item["type"], item["filename"]
            if (not isinstance(skin_id, str) or not skin_id.startswith(typ + "_")
                    or typ not in ("head", "body")
                    or not isinstance(filename, str)
                    or not filename.lower().endswith(".png")
                    or filename != Path(filename).name
                    or item["group"] not in GROUPS):
                raise ValueError("Invalid skin ID, type or filename.")
            key = (typ, filename)
            if skin_id in ids or key in names:
                raise ValueError("Duplicate Snake ID or image filename.")
            ids.add(skin_id)
            names.add(key)
            folder = "SnakeHeadsbibliothek" if typ == "head" else "SnakeBodysBibliothek"
            if not (find_asset_directory("graphics", folder) / filename).is_file():
                raise ValueError(f"Missing packaged Snake image: {filename}")
            rank = item["required_rank"]
            if item["group"] == "career":
                if type(rank) is not int or not 2 <= rank <= 40 or rank in ranks:
                    raise ValueError("Rank skin needs a unique valid career rank.")
                ranks.add(rank)
                career.append(item)
            elif rank is not None:
                raise ValueError("Unimplemented unlock groups must not have rank triggers.")
            if item["group"] == "starter":
                starters.add(skin_id)
            by_id[skin_id] = item
            by_filename[key] = skin_id
        if (sum(x["type"] == "head" for x in entries if x["group"] == "starter") != 4
                or sum(x["type"] == "body" for x in entries if x["group"] == "starter") != 2):
            raise ValueError("Expected four free Heads and two free Bodies.")
        self.entries = tuple(entries)
        self.by_id = by_id
        self.by_filename = by_filename
        self.starters = frozenset(starters)
        self.career = tuple(sorted(career, key=lambda skin: skin["required_rank"]))

    def skin_id(self, tab, filename):
        return self.by_filename.get((SKIN_TYPE.get(tab), filename))

    def is_unlocked(self, snapshot, tab, filename):
        skin_id = self.skin_id(tab, filename)
        return bool(skin_id and (skin_id in self.starters or
                                  skin_id in snapshot["unlocked"]))

    def status(self, snapshot, tab, filename):
        skin_id = self.skin_id(tab, filename)
        if skin_id is None:
            return "Unbekanntes Bild"
        if self.is_unlocked(snapshot, tab, filename):
            return "Freigeschaltet"
        skin = self.by_id[skin_id]
        if skin["group"] == "career":
            return f"Gesperrt · Karriererang {skin['required_rank']}"
        return {
            "achievement": "Gesperrt · Achievement folgt",
            "boss": "Gesperrt · Bossbelohnung folgt",
            "reserve": "Gesperrt · Für spätere Inhalte",
        }[skin["group"]]


@lru_cache(maxsize=1)
def skin_registry():
    with find_asset("graphics", "skin_registry.json").open(encoding="utf-8") as file:
        return SkinRegistry(json.load(file))


def _inventory_state(registry, legacy, processed, grants):
    unlocked = sorted(registry.starters.union(legacy).union(
        grant["skin_id"] for grant in grants
    ))
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "registry_version": SKIN_REGISTRY_VERSION,
        "legacy_unlocked": sorted(legacy),
        "processed_rounds": list(processed),
        "grants": list(grants),
        "unlocked": unlocked,
    }


def _validate_inventory(data, registry):
    if (not isinstance(data, dict) or set(data) != {
        "schema_version", "registry_version", "legacy_unlocked",
        "processed_rounds", "grants", "unlocked"
    }):
        raise ValueError("Invalid Snake inventory structure; not overwritten.")
    if (type(data["schema_version"]) is not int
            or data["schema_version"] != INVENTORY_SCHEMA_VERSION
            or type(data["registry_version"]) is not int
            or data["registry_version"] != SKIN_REGISTRY_VERSION):
        raise ValueError("Unknown Snake inventory version; not overwritten.")
    legacy, processed, grants = (data[key] for key in (
        "legacy_unlocked", "processed_rounds", "grants"
    ))
    if (not isinstance(legacy, list) or not isinstance(processed, list)
            or not isinstance(grants, list) or not isinstance(data["unlocked"], list)
            or any(not isinstance(i, str) or i not in registry.by_id for i in legacy)
            or len(legacy) != len(set(legacy))
            or any(not _uuid_ok(uid) for uid in processed)
            or len(processed) != len(set(processed))):
        raise ValueError("Invalid Snake inventory IDs.")
    grant_ids = set()
    grant_rounds = set()
    for grant in grants:
        if (not isinstance(grant, dict) or set(grant) != {
            "round_id", "skin_id", "required_rank"
        }):
            raise ValueError("Malformed Snake reward.")
        uid, skin_id, rank = (grant[k] for k in (
            "round_id", "skin_id", "required_rank"
        ))
        item = registry.by_id.get(skin_id)
        if (not _uuid_ok(uid) or uid not in processed or uid in grant_rounds
                or skin_id in grant_ids or skin_id in legacy
                or not item or item["group"] != "career"
                or type(rank) is not int or rank != item["required_rank"]):
            raise ValueError("Forged or duplicate Snake reward entry.")
        grant_rounds.add(uid)
        grant_ids.add(skin_id)
    expected = _inventory_state(registry, legacy, processed, grants)
    if data["unlocked"] != expected["unlocked"]:
        raise ValueError("Snake inventory owned items do not match reward entries.")


class SkinInventory:
    """Atomic, replay-safe, crash-recoverable Snake cosmetics store.

    The very first inventory creation preserves any valid head/body filenames
    already saved in settings.json. After that, settings cannot be used to
    mint further items; only the verified career award stream may unlock skins.
    """

    def __init__(self, path: Path | None = None):
        self._explicit_path = Path(path) if path is not None else None

    @property
    def path(self):
        return self._explicit_path if self._explicit_path is not None else skin_inventory_file_path()

    def read(self, registry):
        try:
            with self.path.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return _inventory_state(registry, [], [], [])
        _validate_inventory(data, registry)
        return data

    def sync(self, career, registry, *, existing_settings=None):
        """Reconcile completed award IDs; grant at most one cosmetic per run.

        Any pending rank threshold automatically remains eligible for a later
        completed round. One-time legacy preservation is only performed when
        this inventory file does not exist yet.
        """
        validate_career_state(career)
        path = self.path
        with _journal_lock(path):
            first_install = not path.is_file()
            current = self.read(registry)
            source_ids = [award["round_id"] for award in career["awards"]]
            recorded = current["processed_rounds"]
            # Two concurrently running games may have older, shorter career
            # snapshots. They must NOT truncate already processed newer rounds.
            shared = min(len(source_ids), len(recorded))
            if recorded[:shared] != source_ids[:shared]:
                raise ValueError("Snake inventory history diverged from career.")
            if len(source_ids) < len(recorded):
                return current

            legacy = set(current["legacy_unlocked"])
            if first_install:
                for tab, setting_names in (
                    ("Heads", ("custom_head_p1", "custom_head_p2")),
                    ("Bodies", ("custom_body_p1", "custom_body_p2")),
                ):
                    for setting in setting_names:
                        filename = (existing_settings or {}).get(setting)
                        skin_id = registry.skin_id(tab, filename)
                        if skin_id:
                            legacy.add(skin_id)

            processed = list(recorded)
            grants = list(current["grants"])
            unlocked = set(registry.starters) | legacy | {
                item["skin_id"] for item in grants
            }
            total = sum(award["xp"] for award in career["awards"][:len(processed)])
            for award in career["awards"][len(processed):]:
                total += award["xp"]
                eligible_rank = career_rank(total)
                # A fixed ordered pool, not RNG. Unassigned eligible ranks
                # remain pending rather than issuing multiple items this round.
                skin = next((
                    item for item in registry.career
                    if item["required_rank"] <= eligible_rank
                    and item["id"] not in unlocked
                ), None)
                if skin is not None:
                    grants.append({
                        "round_id": award["round_id"],
                        "skin_id": skin["id"],
                        "required_rank": skin["required_rank"],
                    })
                    unlocked.add(skin["id"])
                processed.append(award["round_id"])

            updated = _inventory_state(registry, legacy, processed, grants)
            _validate_inventory(updated, registry)
            if not first_install and updated == current:
                return current
            temp = None
            try:
                with NamedTemporaryFile(
                    "w", encoding="utf-8", dir=path.parent,
                    prefix=".skin-inventory-", suffix=".tmp", delete=False
                ) as handle:
                    temp = Path(handle.name)
                    json.dump(updated, handle, ensure_ascii=False, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp, path)
                temp = None
            finally:
                if temp is not None:
                    temp.unlink(missing_ok=True)
            return updated
