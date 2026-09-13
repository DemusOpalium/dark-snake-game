"""Lightweight runtime diagnostics for unexpected game crashes."""

from __future__ import annotations

import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path


REPORT_PATH = Path(tempfile.gettempdir()) / "dark-snake-crash.log"


def record_event(message: str) -> None:
    """Append a timestamped diagnostic event without disrupting the game."""
    try:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with REPORT_PATH.open("a", encoding="utf-8") as report:
            report.write(f"[{timestamp}] {message}\n")
    except OSError:
        # Reporting must never turn a recoverable game problem into a crash.
        pass


def report_exception(exc_type, exc_value, exc_traceback) -> None:
    """Persist an uncaught exception and then delegate to Python's hook."""
    try:
        with REPORT_PATH.open("a", encoding="utf-8") as report:
            report.write("Unbehandelter Absturz:\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=report)
    except OSError:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def install_crash_reporting() -> None:
    """Install the process-wide uncaught-exception reporter."""
    sys.excepthook = report_exception
