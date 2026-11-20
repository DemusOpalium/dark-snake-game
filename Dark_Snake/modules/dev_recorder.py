"""Irians Auge A: opt-in, local-only developer telemetry for Classic rounds.

The game must remain playable if telemetry storage is unavailable.  No
per-frame disk IO, no network, no modifications to career/round journals.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
import time

from modules.resources import developer_report_directories

SCHEMA_VERSION = 1
SAMPLE_INTERVAL = 0.25
MAX_EVENTS = 3000
MAX_SAMPLES = 4000
MAX_REPORT_BYTES = 2_000_000
MAX_REPORTS = 20
SOURCE_GUIDE = {
    "combat": "Dark_Snake/modules/game.py::Game.log_combat_event",
    "boss_phases": "Dark_Snake/modules/boss_phases.py",
    "boss_teleport": "Dark_Snake/modules/boss_teleport.py",
    "boss_personality": "Dark_Snake/modules/boss_personality.py",
    "boss_items": "Dark_Snake/modules/game.py::Game.handle_item_pickup",
    "round_history": "Dark_Snake/modules/round_progress.py",
}


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe(value, depth=0):
    """Bound JSON values; never pickle runtime objects or dump internal paths."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:240]
    if depth < 3 and isinstance(value, (tuple, list)):
        return [_safe(entry, depth + 1) for entry in value[:40]]
    if depth < 3 and isinstance(value, dict):
        return {str(key)[:64]: _safe(entry, depth + 1)
                for key, entry in list(value.items())[:30]}
    return str(type(value).__name__)


class DeveloperRecorder:
    """Bounded event stream and position samples, persisted only at milestones."""

    def __init__(self, *, directory: Path | None = None, clock=None):
        self.enabled = False  # Explicitly opt-in, reset to OFF on every start.
        self.active = False
        self._directory = Path(directory) if directory is not None else None
        self.clock = clock or time.monotonic
        self.error = None
        self.last_report = None
        self._clear()

    def _clear(self):
        self.round_id = None
        self.start_mono = 0.0
        self.last_sample_mono = float("-inf")
        self.report = None
        self.events = deque(maxlen=MAX_EVENTS)
        self.positions = deque(maxlen=MAX_SAMPLES)
        self._event_count = 0
        self._sample_count = 0

    def configure(self, enabled: bool):
        """Only the main-menu UI should toggle this between new rounds."""
        if self.active:
            return False
        self.enabled = bool(enabled)
        return True

    def begin_round(self, token: dict, *, context: dict):
        if self.active:
            self.finish("replaced")
        self._clear()
        if not self.enabled:
            return False
        self.round_id = token["round_id"]
        self.start_mono = self.clock()
        self.report = {
            "schema_version": SCHEMA_VERSION,
            "tool": "Irians Auge",
            "round_id": self.round_id,
            "round": _safe(token),
            "context": _safe(context),
            "source_guide": SOURCE_GUIDE,
            "started_at": _utc(),
            "finished_at": None,
            "finish_reason": None,
            "checkpoint": "round_start",
            "events": [],
            "positions": [],
            "feedback": [],
            "dropped_events": 0,
            "dropped_samples": 0,
        }
        self.active = True
        self.event("round_start", players=token["players"])
        return True

    def elapsed_ms(self):
        return max(0, int(round((self.clock() - self.start_mono) * 1000)))

    def event(self, name: str, **details):
        if not self.active:
            return
        self._event_count += 1
        self.events.append({
            "ms": self.elapsed_ms(), "type": str(name)[:80],
            "data": _safe(details),
        })

    def sample(self, *, level, player_heads, boss, enemies, items, portal=None, world=None):
        if not self.active:
            return
        now = self.clock()
        if now - self.last_sample_mono < SAMPLE_INTERVAL:
            return
        self.last_sample_mono = now
        self._sample_count += 1
        self.positions.append({
            "ms": self.elapsed_ms(),
            "level": int(level),
            "heads": _safe(player_heads),
            "boss": _safe(boss),
            "enemies": int(enemies),
            "items": int(items),
            "portal": _safe(portal),
            "world": _safe(world),
        })

    def add_feedback(self, *, subject, prompt, rating, note="", item_verdict=None):
        """PR B uses this; do not infer sentiment from combat counters."""
        if not self.active:
            return False
        if rating is not None and (type(rating) is not int or not 0 <= rating <= 5):
            return False
        entry = {
            "ms": self.elapsed_ms(),
            "subject": str(subject)[:80],
            "prompt": str(prompt)[:200],
            "rating": rating,
            "note": str(note)[:300],
            "item_verdict": _safe(item_verdict),
        }
        if len(self.report["feedback"]) >= 40:
            return False
        self.report["feedback"].append(entry)
        self.event("player_feedback", subject=subject, rating=rating)
        return self.checkpoint("player_feedback")

    def _snapshot(self, checkpoint):
        result = dict(self.report)
        result["checkpoint"] = checkpoint
        result["events"] = list(self.events)
        result["positions"] = list(self.positions)
        result["dropped_events"] = max(0, self._event_count - len(self.events))
        result["dropped_samples"] = max(0, self._sample_count - len(self.positions))
        # Bound the final JSON, not only in-memory buffers.
        while True:
            payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
            if len(payload.encode("utf-8")) <= MAX_REPORT_BYTES:
                return payload
            if result["positions"]:
                removed = min(100, len(result["positions"]))
                del result["positions"][:removed]
                result["dropped_samples"] += removed
            elif result["events"]:
                removed = min(50, len(result["events"]))
                del result["events"][:removed]
                result["dropped_events"] += removed
            else:
                raise ValueError("Developer report metadata exceeds size limit")

    def checkpoint(self, reason="checkpoint"):
        """Atomic file replace; IO only on boss/round events or user feedback."""
        if not self.active:
            return False
        directories = ((self._directory,) if self._directory is not None
                       else developer_report_directories())
        try:
            payload = self._snapshot(str(reason)[:80])
            # UUID is generated by begin_round(), never from player text.
            filename = "dev-round-" + self.round_id + ".json"
            for directory in directories:
                temp = None
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    with NamedTemporaryFile("w", encoding="utf-8", dir=directory,
                                            prefix=".dev-report-", suffix=".tmp",
                                            delete=False) as handle:
                        temp = Path(handle.name)
                        handle.write(payload)
                        handle.flush()
                        os.fsync(handle.fileno())
                    target = directory / filename
                    os.replace(temp, target)
                    temp = None
                    self.last_report = target
                    self.error = None
                    self._prune(directory)
                    return True
                except OSError as exc:
                    self.error = str(exc)[:200]
                finally:
                    if temp is not None:
                        try:
                            temp.unlink(missing_ok=True)
                        except OSError:
                            pass
        except (OSError, TypeError, ValueError) as exc:
            self.error = str(exc)[:200]
        return False

    def _prune(self, directory):
        """Never touch game saves, only this tool's own report filenames."""
        try:
            reports = sorted(directory.glob("dev-round-*.json"),
                             key=lambda path: path.stat().st_mtime, reverse=True)
            for old in reports[MAX_REPORTS:]:
                old.unlink(missing_ok=True)
        except OSError:
            pass

    def finish(self, reason="round_end"):
        if not self.active:
            return False
        self.event("round_finished", reason=reason)
        self.report["finished_at"] = _utc()
        self.report["finish_reason"] = str(reason)[:80]
        ok = self.checkpoint("round_end")
        self.active = False
        return ok
