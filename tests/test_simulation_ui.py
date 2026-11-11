import os
import queue
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame
import pytest

from developer_simulator import failed_simulation_report, save_report
from modules import simulation_ui
from modules.enums import GameState
from modules.simulation_ui import SimulationMenu


class FakeEvent:
    def __init__(self):
        self.value = False

    def set(self): self.value = True
    def clear(self): self.value = False
    def is_set(self): return self.value


class FakeQueue(queue.Queue):
    def close(self): pass


class FakeProcess:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.alive = False
        self.started = self.terminated = False

    def start(self): self.started = self.alive = True
    def is_alive(self): return self.alive
    def terminate(self): self.terminated = True; self.alive = False
    def join(self, timeout=None): pass


class FakeContext:
    def __init__(self): self.last_process = None
    def Queue(self): return FakeQueue()
    def Event(self): return FakeEvent()
    def Process(self, **kwargs):
        self.last_process = FakeProcess(**kwargs)
        return self.last_process


class FakeGame:
    def __init__(self): self.state = GameState.SIMULATION
    def intro_state(self): return GameState.INTRO
    def set_state(self, state): self.state = state


def make_menu():
    context = FakeContext()
    return SimulationMenu(FakeGame(), process_context=context), context


@pytest.fixture(autouse=True)
def reports_in_test_folder(monkeypatch, tmp_path):
    folder = tmp_path / "Entwicklerberichte"
    monkeypatch.setattr(simulation_ui, "latest_report", lambda: None)
    monkeypatch.setattr(simulation_ui, "report_directory", lambda: folder)
    monkeypatch.setattr(simulation_ui, "save_report",
                        lambda report, scenario: save_report(report, folder, scenario))
    return folder


def batch_report(status="completed", scenarios=("boss",)):
    complete = status == "completed"
    return {
        "configuration": {"base_seed": 11, "scenarios": scenarios},
        "completion": {"planned_runs": 1, "completed_runs": int(complete), "complete": complete},
        "outcome": {"status": status, "reason": "Nicht alle Szenarien vollständig"},
        "summary": {
            "technical_exceptions": 0, "rule_checks_passed": 1,
            "rule_checks_failed": int(status == "rule_failed"), "rule_checks_not_run": 2,
            "timeouts": int(status == "timeout"), "cancelled": int(status == "cancelled"),
        },
        "runs": [], "failure_groups": {},
    }


def finish_write(menu):
    menu._report_write.result(timeout=5)
    menu.poll()


def test_start_creates_background_process():
    menu, context = make_menu()
    menu.start()
    assert context.last_process.started
    assert menu.running and menu.status == "Läuft"


def test_importing_worker_entry_point_does_not_load_graphics_before_sdl():
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; from modules.simulation_ui import simulation_worker; "
         "assert 'modules.graphics' not in sys.modules"],
        cwd=ROOT / "Dark_Snake", capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr[-2000:]


def test_progress_message_updates_visible_state():
    menu, _ = make_menu()
    menu.start()
    menu.messages.put({"type": "progress", "scenario": "boss", "round": 2,
                       "completed": 1, "total": 3, "errors": 1,
                       "last_error": "kaputt"})
    menu.poll()
    assert (menu.current_scenario, menu.current_round, menu.completed) == ("boss", 2, 1)
    assert menu.errors == 1 and menu.last_error == "kaputt"


def test_worker_error_is_reported_and_stopped():
    menu, context = make_menu()
    menu.start()
    menu.messages.put({"type": "fatal", "error": "ValueError: kaputt",
                       "report": failed_simulation_report(ValueError("kaputt"), ("boss",), 11)})
    menu.poll()
    assert menu.status == "Worker-Fehler" and menu.last_error == "ValueError: kaputt"
    assert context.last_process.terminated and not menu.running
    finish_write(menu)
    assert "ValueError: kaputt" in menu.last_report_paths[0].read_text(encoding="utf-8")


def test_cancel_preserves_partial_report_from_worker():
    menu, context = make_menu()
    menu.start()
    menu.pause()
    menu.cancel()
    assert menu.cancel_event.is_set() and menu.resume_event.is_set()
    assert not context.last_process.terminated and menu.status == "Abbruch läuft"
    menu.messages.put({"type": "finished", "report": batch_report("cancelled")})
    menu.poll()
    finish_write(menu)
    assert menu.status == "Abgebrochen" and menu.last_report_paths[1].is_file()


def test_escape_requests_cancellation_and_returns_after_report(monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    from modules.game import Game

    game = Game(headless=True)
    context = FakeContext()
    menu = game.simulation_menu = SimulationMenu(game, process_context=context)
    game.set_state(GameState.SIMULATION)
    menu.start()
    monkeypatch.setattr(pygame.event, "get", lambda: [
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    ])
    game.handle_events()
    assert menu.cancel_event.is_set() and not context.last_process.terminated
    assert game.game_state is GameState.SIMULATION
    menu.messages.put({"type": "finished", "report": batch_report("cancelled")})
    menu.poll()
    finish_write(menu)
    assert game.game_state is GameState.INTRO and menu.status == "Bereit"
    assert menu.last_report_paths[0].is_file()


def test_finished_status_requires_a_complete_report():
    menu, _ = make_menu()
    menu.start()
    menu.messages.put({"type": "finished", "report": batch_report("incomplete")})

    menu.poll()
    finish_write(menu)

    assert menu.status == "Fehler"
    assert "nicht alle" in menu.last_error.lower()


@pytest.mark.parametrize(("cancel", "status", "reason"), [
    (False, "Timeout", "timeout"),
    (True, "Abgebrochen", "cancelled"),
])
def test_unresponsive_worker_saves_timeout_or_cancel_report(cancel, status, reason):
    menu, context = make_menu()
    now = [100.0]
    menu._monotonic = lambda: now[0]
    menu.start()
    if cancel:
        menu.cancel()
    now[0] += menu.TIMEOUT_SECONDS + 1
    menu.poll()
    finish_write(menu)
    assert context.last_process.terminated
    assert menu.status == status
    assert menu.report["outcome"]["status"] == reason
    assert menu.errors == 0


def test_menu_shows_report_directory_and_empty_state_before_first_batch(reports_in_test_folder):
    menu, _ = make_menu()
    assert menu.report_directory is None
    menu._load_report_location()
    lines = list(menu._report_lines())
    assert f"Berichtsordner: {reports_in_test_folder}" in lines
    assert "Letzter Bericht: –" in lines
    menu.save_report_files()
    assert menu.report_notice == "Noch kein Bericht vorhanden."


def test_finished_batch_autosaves_once_in_actual_directory(monkeypatch, reports_in_test_folder):
    menu, _ = make_menu()
    menu.start()
    menu.scenario_index = menu.SCENARIOS.index("aoe")
    menu.messages.put({"type": "finished", "report": batch_report("rule_failed")})
    menu.poll()
    finish_write(menu)

    txt, json_path = menu.last_report_paths
    assert txt.is_file() and json_path.is_file()
    assert menu.report_directory == reports_in_test_folder
    assert txt.name.startswith("simulation-report-boss-")
    assert menu.status == "Regelprüfung fehlgeschlagen" and menu.errors == 0
    assert f"Letzter Bericht: {txt.stem} (.txt und .json)" in list(menu._report_lines())
    menu.save_report_files()
    assert set(reports_in_test_folder.iterdir()) == {txt, json_path}

    opened = []
    monkeypatch.setattr(simulation_ui.os, "startfile", opened.append, raising=False)
    menu.back()
    menu.open_report_directory()
    assert opened == [txt.parent]
    assert menu.last_report_paths == (txt, json_path)


def test_menu_opens_the_folder_of_a_report_from_an_earlier_session(monkeypatch, tmp_path):
    menu, _ = make_menu()
    actual_directory = tmp_path / "anderer Ordner"
    paths = save_report(batch_report(), actual_directory, "boss")
    monkeypatch.setattr(simulation_ui, "latest_report", lambda: paths)
    opened = []
    monkeypatch.setattr(simulation_ui.os, "startfile", opened.append, raising=False)
    menu.open_report_directory()
    assert opened == [actual_directory]
    assert menu.report_directory == actual_directory and menu.last_report_paths == paths


def test_open_reports_handles_unsupported_system_and_windows_error(monkeypatch):
    menu, _ = make_menu()
    monkeypatch.delattr(simulation_ui.os, "startfile", raising=False)
    menu.open_report_directory()
    assert "angezeigten Pfad" in menu.report_notice

    def fail(_directory):
        raise OSError("Dateimanager nicht verfügbar")

    monkeypatch.setattr(simulation_ui.os, "startfile", fail, raising=False)
    menu.open_report_directory()
    assert "konnte nicht geöffnet werden" in menu.report_notice


def test_save_error_leaves_result_available_for_manual_retry(monkeypatch, reports_in_test_folder):
    menu, _ = make_menu()
    writer = simulation_ui.save_report

    def fail(_report, scenario):
        raise PermissionError("Ordner ist schreibgeschützt")

    monkeypatch.setattr(simulation_ui, "save_report", fail)
    menu.start()
    menu.messages.put({"type": "finished", "report": batch_report()})
    menu.poll()
    with pytest.raises(PermissionError):
        menu._report_write.result(timeout=5)
    menu.poll()
    assert menu.status == "Fertig" and menu.report_paths is None
    assert "konnte nicht gespeichert werden" in menu.report_notice

    monkeypatch.setattr(simulation_ui, "save_report", writer)
    menu.save_report_files()
    finish_write(menu)
    assert menu.report_paths[0].parent == reports_in_test_folder
