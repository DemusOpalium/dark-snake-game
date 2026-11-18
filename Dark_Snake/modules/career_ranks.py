"""40 persistent career ranks derived only from verified completed Classic rounds.

No in-frame XP, random rewards, achievements or cosmetic unlocks live here.
The rules are versioned: already-awarded XP is *never* recalculated if a later
release changes the formula. A separate ledger is reconciled after Game Over
and when a real game process starts, so a crash between the two saves is safe.
"""
from __future__ import annotations

import json
import os
from bisect import bisect_right
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from modules.resources import career_file_path
from modules.round_progress import RoundJournal, _journal_lock, validate_round


CAREER_SCHEMA_VERSION = 1
XP_RULES_VERSION = 1
MAX_CAREER_RANK = 40

# 40 reproducible rank thresholds. Rank 1 = 0 XP, Rank 2 = 500 XP,
# Rank 3 = 1,500 XP, ... Rank 40 = 390,000 XP.
RANK_MIN_XP = tuple(250 * (rank - 1) * rank
                    for rank in range(1, MAX_CAREER_RANK + 1))


def xp_for_round(record: dict) -> int:
    """Reward only real confirmed round facts from the immutable V1 journal.

    Score is recorded separately from kills and items intentionally; this is
    the *career* XP curve (not Classic's existing level/experience balance).
    No guessed survival time, boss identity, co-op bonus or daily login award.
    """
    validate_round(record)
    return (record["score"] // 10
            + 10 * record["enemies_defeated"]
            + 200 * record["bosses_defeated"]
            + 5 * record["items_collected"])


def career_rank(xp: int) -> int:
    if type(xp) is not int or xp < 0:
        raise ValueError("Career XP must be a nonnegative integer.")
    return min(MAX_CAREER_RANK, bisect_right(RANK_MIN_XP, xp))


def career_rank_id(rank: int) -> str:
    if type(rank) is not int or not (1 <= rank <= MAX_CAREER_RANK):
        raise ValueError("Career rank must be between 1 and 40.")
    return f"rank_{rank:02d}"


def _state(awards: list[dict]) -> dict:
    total = sum(award["xp"] for award in awards)
    return {
        "schema_version": CAREER_SCHEMA_VERSION,
        "rules_version": XP_RULES_VERSION,
        "awards": awards,
        "total_xp": total,
        "rank": career_rank(total),
    }


def _validate_state(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != {
        "schema_version", "rules_version", "awards", "total_xp", "rank"
    }:
        raise ValueError("Invalid career ledger structure; not overwritten.")
    if (type(data["schema_version"]) is not int
            or data["schema_version"] != CAREER_SCHEMA_VERSION):
        raise ValueError("Unknown career schema version; not overwritten.")
    if (type(data["rules_version"]) is not int
            or data["rules_version"] != XP_RULES_VERSION):
        raise ValueError("Unknown career XP rules version; migration required.")
    awards = data["awards"]
    if not isinstance(awards, list):
        raise ValueError("Career awards must be a list.")
    seen = set()
    for entry in awards:
        if not isinstance(entry, dict) or set(entry) != {
            "round_id", "xp", "rules_version"
        }:
            raise ValueError("Invalid career award.")
        try:
            uid = UUID(entry["round_id"])
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("Invalid career award round ID.") from exc
        if uid.version != 4 or uid.hex != entry["round_id"]:
            raise ValueError("Invalid canonical career round ID.")
        if entry["round_id"] in seen:
            raise ValueError("Duplicate career award round ID.")
        seen.add(entry["round_id"])
        if (type(entry["xp"]) is not int or entry["xp"] < 0
                or type(entry["rules_version"]) is not int
                or entry["rules_version"] != XP_RULES_VERSION):
            raise ValueError("Invalid career award XP or rule version.")
    expected = _state(awards)
    if (type(data["total_xp"]) is not int or type(data["rank"]) is not int
            or data["total_xp"] != expected["total_xp"]
            or data["rank"] != expected["rank"]):
        raise ValueError("Career totals/rank differ from recorded awards.")


class CareerLedger:
    """Crash-reconcilable career XP ledger, independent of UI and skins.

    Reconciliation is idempotent by round UUID, and performed off the game
    frame loop. Concurrent instances serialize their commits with the same
    operating-system lock mechanism used by the round journal.
    """

    def __init__(self, path: Path | None = None):
        self._explicit_path = Path(path) if path is not None else None

    @property
    def path(self) -> Path:
        return self._explicit_path if self._explicit_path is not None else career_file_path()

    def read(self) -> dict:
        try:
            with self.path.open(encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return _state([])
        _validate_state(data)
        return data

    def sync(self, journal: RoundJournal) -> dict:
        """Import any confirmed but not yet awarded round, once per UUID.

        Recovery: if the round was saved but this ledger was not, the next
        startup or Game Over adds its XP. Existing awards are never changed.
        The committed journal is the only trusted source of round events.
        """
        records = journal.read()["rounds"]
        # Validate before any writes: no partial import from corrupt history.
        for record in records:
            validate_round(record)

        with _journal_lock(self.path):
            current = self.read()
            seen = {award["round_id"] for award in current["awards"]}
            new_awards = [
                {
                    "round_id": record["round_id"],
                    "xp": xp_for_round(record),
                    "rules_version": XP_RULES_VERSION,
                }
                for record in records if record["round_id"] not in seen
            ]
            if not new_awards:
                return current

            # Never mutate existing awards; write a new validated snapshot.
            updated = _state([*current["awards"], *new_awards])
            _validate_state(updated)
            temp = None
            try:
                with NamedTemporaryFile(
                    "w", encoding="utf-8", dir=self.path.parent,
                    prefix=".career-progress-", suffix=".tmp", delete=False
                ) as handle:
                    temp = Path(handle.name)
                    json.dump(updated, handle, ensure_ascii=False, indent=2)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp, self.path)
                temp = None
            finally:
                if temp is not None:
                    temp.unlink(missing_ok=True)
            return updated
