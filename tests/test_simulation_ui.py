import os
import queue
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame

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


def test_start_creates_background_process():
    menu, context = make_menu()
    menu.start()
    assert context.last_process.started
    assert menu.running and menu.status == "Läuft"


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
                       "traceback": "Traceback\n"})
    menu.poll()
    assert menu.status == "Worker-Fehler" and menu.last_error == "ValueError: kaputt"
    assert context.last_process.terminated and not menu.running


def test_cancel_terminates_worker():
    menu, context = make_menu()
    menu.start()
    menu.cancel()
    assert context.last_process.terminated and menu.status == "Abgebrochen"


def test_escape_cancels_and_returns_to_main_menu():
    menu, context = make_menu()
    menu.start()
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert context.last_process.terminated
    assert menu.game.state is GameState.INTRO and menu.status == "Bereit"


def test_finished_status_requires_a_complete_report():
    menu, _ = make_menu()
    menu.start()
    menu.messages.put({"type": "finished", "cancelled": False, "report": {
        "completion": {"planned_runs": 1, "completed_runs": 0, "complete": False},
        "runs": [], "failure_groups": {},
    }})

    menu.poll()

    assert menu.status == "Fehler"
    assert "nicht alle" in menu.last_error.lower()
