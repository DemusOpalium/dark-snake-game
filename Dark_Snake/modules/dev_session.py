"""Irians Auge E: one opt-in local session across menu visits and rounds.

An append-only *logical* activity timeline (bounded RAM) plus atomic snapshot
files. Existing per-round JSON/HTML remain authoritative; this file contains
only round links and UI/debug context. No remote SDK or user input logging.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
import time
from uuid import uuid4

from modules.resources import developer_report_directories

SCHEMA = 1
MAX_EVENTS = 1200
MAX_ROUNDS = 40
MAX_SESSIONS = 20
MAX_BYTES = 500_000
AUTO_SAVE_SECONDS = 90
# Fixed public taxonomy: do not inadvertently serialize menu text or keys.
EVENTS = {
    "session_started", "session_finished", "navigation", "studio_toggle",
    "settings_saved", "round_started", "round_finished", "feedback_dismissed",
    "tester_marker", "session_warning",
}


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe(value, depth=0):
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, str):
            return value[:120]
        return value
    if depth < 2 and isinstance(value, (list, tuple)):
        return [_safe(v, depth + 1) for v in value[:20]]
    if depth < 2 and isinstance(value, dict):
        return {str(k)[:48]: _safe(v, depth + 1)
                for k, v in list(value.items())[:12]}
    return None


class DeveloperSession:
    def __init__(self, *, directory=None, clock=None):
        self.directory = Path(directory) if directory is not None else None
        self.clock = clock or time.monotonic
        self.active = False
        self.session_id = None
        self.started = None
        self._started_mono = None
        self.events = deque(maxlen=MAX_EVENTS)
        self.rounds = []
        self.dirty = False
        self.has_data = False
        self.error = None
        self.last_saved_at = None
        self.last_report = None
        self._next_auto = 0
        self.dropped = 0

    def start(self):
        if self.active:
            return False
        self.session_id = uuid4().hex
        self.started = _utc()
        self._started_mono = self.clock()
        self.events.clear()
        self.rounds = []
        self.error = None
        self.last_saved_at = None
        self.last_report = None
        self.dirty = False
        self.has_data = False
        self.dropped = 0
        self.active = True
        self._next_auto = self.clock() + AUTO_SAVE_SECONDS
        self.event("session_started")
        # Crash recovery includes even a newly activated, otherwise empty session.
        self.checkpoint("session_start")
        return True

    def event(self, kind, **details):
        if not self.active or kind not in EVENTS:
            return False
        if len(self.events) == MAX_EVENTS:
            self.dropped += 1
        self.events.append({
            "ms": max(0, round((self.clock() - self._started_mono) * 1000)),
            "type": kind,
            "data": _safe(details),
        })
        if kind != "session_started":
            self.has_data = True
        self.dirty = True
        return True

    def round_start(self, token):
        if not self.active or not token:
            return
        name = str(token["round_id"])
        self.rounds.append({
            "round_id": name, "players": token.get("players"),
            "started_at": token.get("started_at"),
            "finished_at": None, "finish_reason": None,
            "json": "dev-round-" + name + ".json",
            "html": "dev-round-" + name + ".html",
        })
        self.rounds = self.rounds[-MAX_ROUNDS:]
        self.event("round_started", round_id=name, players=token.get("players"))
        self.checkpoint("round_started")

    def round_end(self, token, reason, *, report_saved=False):
        if not self.active or not token:
            return
        name = str(token["round_id"])
        for item in reversed(self.rounds):
            if item["round_id"] == name:
                item["finished_at"] = _utc()
                item["finish_reason"] = str(reason)[:70]
                item["report_saved"] = bool(report_saved)
                break
        self.event("round_finished", round_id=name,
                   reason=str(reason)[:70], report_saved=bool(report_saved))
        self.checkpoint("round_finished")

    def _payload(self, reason):
        output = {
            "schema_version": SCHEMA,
            "tool": "Irians Auge / Developer Session",
            "session_id": self.session_id,
            "started_at": self.started,
            "last_checkpoint": str(reason)[:80],
            "saved_at": _utc(),
            "active": self.active,
            "rounds": self.rounds,
            "events": list(self.events),
            "dropped_events": self.dropped,
            "privacy": "Opt-in local-only, no raw user inputs or network",
        }
        while True:
            payload = json.dumps(output, ensure_ascii=False, indent=2,
                                 allow_nan=False)
            if len(payload.encode("utf-8")) <= MAX_BYTES:
                return payload
            if output["events"]:
                del output["events"][:min(80, len(output["events"]))]
                output["dropped_events"] += 80
            else:
                raise ValueError("session report too large")

    def checkpoint(self, reason="manual"):
        """Save atomically and return True only after a successful replace."""
        if not self.active or not self.session_id:
            return False
        directories = ((self.directory,) if self.directory is not None
                       else developer_report_directories())
        try:
            payload = self._payload(reason)
            for folder in directories:
                temp = None
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    with NamedTemporaryFile(mode="w", encoding="utf-8",
                                            prefix=".dev-session-", suffix=".tmp",
                                            dir=folder, delete=False) as handle:
                        temp = Path(handle.name)
                        handle.write(payload)
                        handle.flush()
                        os.fsync(handle.fileno())
                    final = folder / ("dev-session-" + self.session_id + ".json")
                    os.replace(temp, final)
                    temp = None
                    self.last_report = final
                    self.last_saved_at = _utc()
                    self.error = None
                    self.dirty = False
                    self._next_auto = self.clock() + AUTO_SAVE_SECONDS
                    self._prune(folder)
                    return True
                except (OSError, ValueError) as exc:
                    self.error = str(exc)[:160]
                finally:
                    if temp is not None:
                        try:
                            temp.unlink(missing_ok=True)
                        except OSError:
                            pass
        except (OSError, TypeError, ValueError) as exc:
            self.error = str(exc)[:160]
        return False

    def maybe_autosave(self):
        if self.active and self.dirty and self.clock() >= self._next_auto:
            # Even a failing disk must not cause 60 retries per second.
            self._next_auto = self.clock() + AUTO_SAVE_SECONDS
            return self.checkpoint("periodic")
        return False

    def end(self, reason="disabled"):
        if not self.active:
            return False
        self.event("session_finished", reason=str(reason)[:70])
        result = self.checkpoint(reason)
        self.active = False
        return result

    @staticmethod
    def _prune(folder):
        try:
            paths = sorted(folder.glob("dev-session-*.json"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            for old in paths[MAX_SESSIONS:]:
                old.unlink(missing_ok=True)
        except OSError:
            pass
