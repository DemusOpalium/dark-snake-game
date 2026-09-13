"""Failure-safe application logging and unhandled-exception reports."""

from collections import deque
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import threading
import traceback
import weakref

from modules.resources import logs_path


LOG_FILENAME = "dark_snake.log"
MAX_RECENT_EVENTS = 40
_active_reporter = None


class CrashReporter:
    """Own the application log, recent-event buffer, and exception hooks.

    Every public operation is best-effort: diagnostics must never become a
    second reason for the game to terminate.
    """

    def __init__(self, log_directory=None):
        self.log_directory = Path(log_directory) if log_directory else logs_path()
        self.recent_events = deque(maxlen=MAX_RECENT_EVENTS)
        self._game_ref = None
        self.logger = logging.getLogger(f"dark_snake.{id(self)}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self._configure_handler()

    def _configure_handler(self):
        try:
            self.log_directory.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                self.log_directory / LOG_FILENAME,
                maxBytes=1_000_000,
                backupCount=2,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(handler)
        except Exception:
            # A read-only/unavailable home directory must not prevent startup.
            self.logger.addHandler(logging.NullHandler())

    def attach_game(self, game):
        try:
            self._game_ref = weakref.ref(game)
        except Exception:
            self._game_ref = None

    def record_event(self, message):
        """Remember one deliberately selected event; never log per-frame data."""
        try:
            entry = f"{datetime.now().isoformat(timespec='seconds')} {str(message)[:300]}"
            self.recent_events.append(entry)
            self.logger.info("EVENT %s", str(message)[:300])
        except Exception:
            pass

    def _game_status(self):
        game = self._game_ref() if self._game_ref else None
        if game is None:
            return "Spielstatus: nicht verfügbar\n"
        try:
            state = getattr(game, "game_state", None)
            state_name = getattr(state, "name", str(state))
            lines = [
                f"GameState: {state_name}",
                f"Spieleranzahl: {getattr(game, 'player_count', 'unbekannt')}",
                f"Level: {getattr(game, 'level', 'unbekannt')}",
                f"Score: {getattr(game, 'score', 'unbekannt')}",
                "Objektanzahlen:",
            ]
            collections = (
                ("snake", "snake"), ("snake1", "snake1"), ("snake2", "snake2"),
                ("items", "items"), ("enemies", "enemies"),
                ("projectiles", "projectiles"), ("flame_projectiles", "flame_projectiles"),
                ("boss_flame_projectiles", "boss_flame_projectiles"),
                ("aoe_zones", "aoe_zones"), ("explosions", "explosions"),
            )
            for label, attribute in collections:
                value = getattr(game, attribute, ())
                try:
                    count = len(value)
                except Exception:
                    count = "unbekannt"
                lines.append(f"  {label}: {count}")
            lines.append(f"  boss: {int(getattr(game, 'boss', None) is not None)}")
            return "\n".join(lines) + "\n"
        except Exception:
            return "Spielstatus: konnte nicht ermittelt werden\n"

    def _report_text(self, exc_type, exc_value, exc_traceback):
        timestamp = datetime.now().isoformat(timespec="seconds")
        stacktrace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        events = "\n".join(self.recent_events) if self.recent_events else "Keine Ereignisse aufgezeichnet."
        return (
            "Dark Snake Crash-Report\n"
            f"Zeitpunkt: {timestamp}\n\n"
            f"{self._game_status()}\n"
            f"Letzte wichtige Ereignisse:\n{events}\n\n"
            f"Vollständiger Stacktrace:\n{stacktrace}"
        )

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Log and persist one unhandled exception without raising another."""
        try:
            report = self._report_text(exc_type, exc_value, exc_traceback)
        except Exception:
            report = "Dark Snake Crash-Report konnte nicht vollständig erzeugt werden.\n"
        try:
            self.logger.critical("Unhandled exception\n%s", report)
        except Exception:
            pass
        try:
            self.log_directory.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            (self.log_directory / f"crash_report_{stamp}.txt").write_text(report, encoding="utf-8")
        except Exception:
            pass

    def install_exception_hooks(self):
        try:
            sys.excepthook = self.handle_exception

            def thread_hook(args):
                self.handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

            threading.excepthook = thread_hook
        except Exception:
            pass

    def close(self):
        """Release file handles, primarily for orderly shutdown and tests."""
        try:
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
        except Exception:
            pass


def configure_crash_reporting(log_directory=None):
    global _active_reporter
    try:
        _active_reporter = CrashReporter(log_directory)
        _active_reporter.install_exception_hooks()
        _active_reporter.record_event("Logging initialisiert")
        return _active_reporter
    except Exception:
        return None


def record_event(message):
    try:
        if _active_reporter is not None:
            _active_reporter.record_event(message)
    except Exception:
        pass
