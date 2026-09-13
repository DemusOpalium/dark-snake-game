import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

from modules.crash_reporting import CrashReporter, LOG_FILENAME, MAX_RECENT_EVENTS
from modules.resources import logs_path


class FakeState:
    name = "GAME"


class FakeGame:
    game_state = FakeState()
    player_count = 2
    level = 7
    score = 1234
    snake = []
    snake1 = [(1, 1)]
    snake2 = [(2, 2)]
    items = [object(), object()]
    enemies = [object()]
    projectiles = []
    flame_projectiles = [object()]
    boss_flame_projectiles = []
    aoe_zones = [object(), object(), object()]
    explosions = []
    boss = object()


def test_unhandled_exception_writes_log_and_detailed_crash_report(tmp_path):
    reporter = CrashReporter(tmp_path)
    game = FakeGame()
    reporter.attach_game(game)
    reporter.record_event("Partie gestartet")

    try:
        raise RuntimeError("beabsichtigter Testfehler")
    except RuntimeError:
        reporter.handle_exception(*sys.exc_info())

    reports = list(tmp_path.glob("crash_report_*.txt"))
    assert len(reports) == 1
    report = reports[0].read_text(encoding="utf-8")
    assert "RuntimeError: beabsichtigter Testfehler" in report
    assert "GameState: GAME" in report
    assert "Spieleranzahl: 2" in report
    assert "Level: 7" in report and "Score: 1234" in report
    assert "items: 2" in report and "aoe_zones: 3" in report and "boss: 1" in report
    assert "Partie gestartet" in report
    assert (tmp_path / LOG_FILENAME).is_file()
    reporter.close()


def test_recent_events_are_bounded(tmp_path):
    reporter = CrashReporter(tmp_path)
    for index in range(MAX_RECENT_EVENTS + 5):
        reporter.record_event(f"Ereignis {index}")
    assert len(reporter.recent_events) == MAX_RECENT_EVENTS
    assert "Ereignis 5" in reporter.recent_events[0]
    reporter.close()


def test_read_only_log_location_does_not_raise(tmp_path):
    unavailable_directory = tmp_path / "not-a-directory"
    unavailable_directory.write_text("blockiert", encoding="utf-8")
    reporter = CrashReporter(unavailable_directory)
    reporter.record_event("bleibt sicher")
    reporter.handle_exception(RuntimeError, RuntimeError("Fehler"), None)
    reporter.close()


def test_default_log_location_is_in_the_user_data_directory():
    assert logs_path() == Path.home() / ".dark-snake" / "logs"
