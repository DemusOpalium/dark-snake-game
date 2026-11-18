"""Persistent, versioned Classic round journal for later ranks and unlocks.

A journal entry is an immutable summary of *confirmed* gameplay counters.
No achievement or reward is awarded here.  Disk reads and writes happen only
when a round ends, never in update(), draw() or an individual enemy hit.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID, uuid4

from modules.resources import progress_file_path


SCHEMA_VERSION = 1
COUNT_FIELDS = (
    "score", "enemies_defeated", "bosses_defeated",
    "items_collected", "lives_lost",
)
ROUND_FIELDS = frozenset((
    "round_id", "mode", "players", "started_at", "finished_at",
    "finished_reason", "score", "level", "enemies_defeated",
    "bosses_defeated", "items_collected", "lives_lost",
))
REASONS = frozenset(("life_depleted", "self_stall"))


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def begin_round(players: int) -> dict:
    """Create the unique, in-memory identity of a real Classic 1P/2P round."""
    if type(players) is not int or players not in (1, 2):
        raise ValueError("A Classic round must have one or two players.")
    return {
        "round_id": uuid4().hex,
        "mode": "classic",
        "players": players,
        "started_at": _timestamp(),
    }


def completed_round(token: dict, *, reason: str, score: int, level: int,
                    enemies: int, bosses: int, items: int, lives_lost: int) -> dict:
    """Freeze existing confirmed game counters; do not infer other achievements."""
    record = {
        **token,
        "finished_at": _timestamp(),
        "finished_reason": reason,
        "score": score,
        "level": level,
        "enemies_defeated": enemies,
        "bosses_defeated": bosses,
        "items_collected": items,
        "lives_lost": lives_lost,
    }
    validate_round(record)
    return record


def validate_round(record: dict) -> None:
    """Reject ambiguous, partial and negative records before persistent storage."""
    if not isinstance(record, dict) or set(record) != ROUND_FIELDS:
        raise ValueError("Round record has unexpected or missing fields.")
    try:
        uid = UUID(record["round_id"])
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("Round ID must be a valid UUID.") from exc
    if uid.version != 4 or uid.hex != record["round_id"]:
        raise ValueError("Round ID must be a canonical UUID4 hex string.")
    if record["mode"] != "classic":
        raise ValueError("Unsupported round mode.")
    if type(record["players"]) is not int or record["players"] not in (1, 2):
        raise ValueError("Invalid number of players.")
    if record["finished_reason"] not in REASONS:
        raise ValueError("An ended round needs a confirmed final reason.")
    for field in (*COUNT_FIELDS, "level"):
        value = record[field]
        if type(value) is not int or value < (1 if field == "level" else 0):
            raise ValueError(f"Invalid round counter: {field}")
    if record["lives_lost"] < 1:
        raise ValueError("A completed Classic round must have lost a life.")
    for field in ("started_at", "finished_at"):
        value = record[field]
        if not isinstance(value, str):
            raise ValueError("Round timestamps must be ISO-8601 UTC strings.")
        try:
            when = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Invalid round timestamp.") from exc
        if when.utcoffset() is None or when.utcoffset().total_seconds() != 0:
            raise ValueError("Round timestamps must be UTC.")


def _totals(rounds: list[dict]) -> dict:
    result = {"rounds_completed": len(rounds)}
    result.update({name: 0 for name in COUNT_FIELDS})
    for record in rounds:
        for name in COUNT_FIELDS:
            result[name] += record[name]
    return result


def _empty_progress() -> dict:
    return {"schema_version": SCHEMA_VERSION, "rounds": [],
            "totals": _totals([])}


class RoundJournal:
    """Single-process, crash-safe JSON journal with replay protection.

    The format is deliberately independent of settings.json and leaderboard.txt.
    Future XP, ranks, titles and rewards must be added through explicit schema
    migrations; do not reinterpret these confirmed historical counters.
    """

    def __init__(self, path: Path | None = None):
        self._explicit_path = Path(path) if path is not None else None

    @property
    def path(self) -> Path:
        return self._explicit_path if self._explicit_path is not None else progress_file_path()

    def read(self) -> dict:
        try:
            with self.path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return _empty_progress()
        if not isinstance(data, dict) or set(data) != {"schema_version", "rounds", "totals"}:
            raise ValueError("Invalid progress journal structure; file not overwritten.")
        if type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
            raise ValueError("Unsupported progress version; file not overwritten.")
        rounds = data["rounds"]
        if not isinstance(rounds, list):
            raise ValueError("Progress rounds must be a list.")
        seen = set()
        for record in rounds:
            validate_round(record)
            uid = record["round_id"]
            if uid in seen:
                raise ValueError("Duplicate round ID in progress journal.")
            seen.add(uid)
        if data["totals"] != _totals(rounds):
            raise ValueError("Progress totals do not match recorded rounds.")
        return data

    def append(self, record: dict) -> bool:
        """Persist one final round atomically; False means exact replay already exists.

        Raises on an invalid/unsupported journal instead of deleting the past.
        An already-used UUID with different contents is never silently accepted.
        """
        validate_round(record)
        old = self.read()
        for previous in old["rounds"]:
            if previous["round_id"] == record["round_id"]:
                if previous == record:
                    return False
                raise ValueError("A completed round ID cannot be rewritten.")

        rounds = [*old["rounds"], dict(record)]
        data = {"schema_version": SCHEMA_VERSION,
                "rounds": rounds, "totals": _totals(rounds)}
        path = self.path
        temp = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                    prefix=".round-progress-", suffix=".tmp",
                                    delete=False) as handle:
                temp = Path(handle.name)
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
            temp = None
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        return True
