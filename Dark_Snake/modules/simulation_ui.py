"""Responsive in-game controls for the developer simulation."""

from __future__ import annotations

import json
import multiprocessing
import queue
import random
import time
import traceback

import pygame

from config import DARK_GREY, ORANGE, PURPLE, RED, WHITE, WINDOW_HEIGHT, WINDOW_WIDTH
from developer_simulator import SimulationControl, format_text_report, run_simulation
from modules.resources import user_data_path
from modules.ui import Button


def simulation_worker(messages, resume_event, cancel_event, options):
    """Process entry point; run_simulation owns its hidden dummy display."""
    control = SimulationControl(resume_event, cancel_event)
    try:
        messages.put({"type": "started"})
        report = run_simulation(control=control, progress=messages.put, **options)
        messages.put({"type": "finished", "report": report,
                      "cancelled": control.cancelled})
    except BaseException as exc:
        messages.put({"type": "fatal", "error": f"{type(exc).__name__}: {exc}",
                      "traceback": "".join(traceback.format_exception(exc))})


class SimulationMenu:
    """Non-blocking front end; pygame remains exclusively on the main thread."""

    SCENARIOS = ("1p", "2p", "boss", "portal", "aoe", "projectiles", "bolbu",
                 "restart", "game_over")
    SPEEDS = (0.25, 1.0, 5.0, 20.0)
    TIMEOUT_SECONDS = 10.0

    def __init__(self, game, process_context=None, monotonic=time.monotonic):
        self.game = game
        self._context = process_context or multiprocessing.get_context("spawn")
        self._monotonic = monotonic
        self.scenario_index = 0
        self.rounds = 3
        self.speed_index = 2
        self.process = self.messages = self.resume_event = self.cancel_event = None
        self.report = None
        self.status = "Bereit"
        self.current_scenario = "–"
        self.current_round = self.completed = self.errors = 0
        self.total = self.rounds
        self.last_error = None
        self.last_message_at = None
        self.base_seed = None
        self.focus = 0

        scale = WINDOW_HEIGHT / 620
        w, h, gap = int(260 * scale), int(40 * scale), int(8 * scale)
        x, y = WINDOW_WIDTH // 2 - w // 2, int(190 * scale)
        actions = (self.start, self.pause, self.cancel, self.save_text, self.save_json,
                   self.back)
        labels = ("Start", "Pause", "Abbrechen", "TXT speichern", "JSON speichern", "Zurück")
        self.buttons = [Button(x, y + i * (h + gap), w, h, label,
                               color=RED if i == 2 else PURPLE, action=action)
                        for i, (label, action) in enumerate(zip(labels, actions))]

    @property
    def running(self):
        return bool(self.process and self.process.is_alive())

    def start(self):
        self.poll()
        if self.running:
            return
        self._dispose_worker()
        self.report = None
        self.status = "Läuft"
        self.current_scenario = self.SCENARIOS[self.scenario_index]
        self.current_round = self.completed = self.errors = 0
        self.total = self.rounds
        self.last_error = None
        self.messages = self._context.Queue()
        self.resume_event = self._context.Event()
        self.resume_event.set()
        self.cancel_event = self._context.Event()
        self.base_seed = random.SystemRandom().randrange(2**32)
        options = {"rounds": self.rounds, "steps": 120,
                   "step_seconds": self.SPEEDS[self.speed_index],
                   "scenarios": (self.current_scenario,), "base_seed": self.base_seed}
        self.process = self._context.Process(
            target=simulation_worker,
            args=(self.messages, self.resume_event, self.cancel_event, options),
            name="DarkSnakeSimulation", daemon=True)
        self.last_message_at = self._monotonic()
        self.process.start()

    def pause(self):
        if not self.running or not self.resume_event:
            return
        if self.resume_event.is_set():
            self.resume_event.clear()
            self.status = "Pausiert"
        else:
            self.resume_event.set()
            self.status = "Läuft"
            self.last_message_at = self._monotonic()

    def cancel(self):
        if not self.process:
            return
        if self.cancel_event:
            self.cancel_event.set()
        if self.resume_event:
            self.resume_event.set()
        self.status = "Abgebrochen"
        self._stop_worker()

    def back(self):
        self.cancel()
        self._reset_run_state()
        self.game.set_state(self.game.intro_state())

    def poll(self):
        """Consume worker messages; call once per UI frame."""
        if self.messages:
            while True:
                try:
                    message = self.messages.get_nowait()
                except queue.Empty:
                    break
                self.last_message_at = self._monotonic()
                kind = message.get("type")
                if kind == "progress":
                    self.current_scenario = message["scenario"]
                    self.current_round = message["round"]
                    self.completed = message["completed"]
                    self.total = message["total"]
                    self.errors = message["errors"]
                    self.last_error = message.get("last_error")
                elif kind == "fatal":
                    self._record_worker_failure("Worker-Fehler", message["error"],
                                                message["traceback"])
                    self._stop_worker()
                    return
                elif kind == "finished":
                    self.report = message["report"]
                    complete = self.report.get("completion", {}).get("complete", False)
                    if message["cancelled"]:
                        self.status = "Abgebrochen"
                    elif complete:
                        self.status = "Fertig"
                    else:
                        self.status = "Fehler"
                        self.last_error = (
                            "Nicht alle ausgewählten Szenarien wurden vollständig "
                            "ausgeführt"
                        )
                    self._dispose_worker()
                    return

        paused = self.resume_event is not None and not self.resume_event.is_set()
        if (self.running and not paused and self.last_message_at is not None and
                self._monotonic() - self.last_message_at > self.TIMEOUT_SECONDS):
            self._record_worker_failure("Timeout", "Simulation antwortet nicht",
                                        "Timeout: Worker lieferte keinen Heartbeat.\n")
            self._stop_worker()
        elif self.process and not self.process.is_alive() and self.report is None:
            exitcode = getattr(self.process, "exitcode", "unbekannt")
            self._record_worker_failure(
                "Worker-Fehler", f"Worker unerwartet beendet (Exitcode {exitcode})",
                f"Worker beendet; Exitcode={exitcode}\n")
            self._dispose_worker()

    def _record_worker_failure(self, status, cause, stacktrace):
        """Keep fatal/timeout details exportable instead of discarding a run."""
        self.status = status
        self.errors += 1
        self.last_error = cause
        seed = self.base_seed if self.base_seed is not None else 0
        failure = {"seed": seed, "scenario": self.current_scenario,
                   "round": self.current_round, "status": status, "cause": cause,
                   "game_time": 0.0, "game_state": "not_initialized",
                   "level": 0, "score": 0, "exception": status,
                   "code_line": "simulation_worker", "stacktrace": stacktrace}
        key = f"{status}@simulation_worker"
        self.report = {"configuration": {"base_seed": seed}, "runs": [failure],
                       "failure_groups": {key: [failure]}}
        with open(user_data_path("simulation-traceback.txt"), "a", encoding="utf-8") as output:
            output.write(stacktrace)

    def _stop_worker(self):
        process = self.process
        if process and process.is_alive():
            process.terminate()
            process.join(timeout=1)
        self._dispose_worker()

    def _dispose_worker(self):
        if self.process and not self.process.is_alive():
            self.process.join(timeout=0)
        if self.messages:
            self.messages.close()
        self.process = self.messages = self.resume_event = self.cancel_event = None
        self.last_message_at = None

    def _reset_run_state(self):
        self.report = None
        self.status = "Bereit"
        self.current_scenario = "–"
        self.current_round = self.completed = self.errors = 0
        self.total = self.rounds
        self.last_error = None

    def _save(self, kind):
        if not self.report:
            self.status = "Fehler"
            self.last_error = "Noch kein Bericht vorhanden"
            return
        path = user_data_path(f"simulation-report.{kind}")
        content = (format_text_report(self.report) if kind == "txt" else
                   json.dumps(self.report, ensure_ascii=False, indent=2))
        with open(path, "w", encoding="utf-8") as output:
            output.write(content)
        self.status = f"Gespeichert: {path}"

    def save_text(self): self._save("txt")
    def save_json(self): self._save("json")

    def handle_event(self, event):
        self.poll()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.back()
            return
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.check_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.focus = i
                    button.check_hover(event.pos)
                    button.handle_event(event)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_DOWN): self.focus = (self.focus + 1) % len(self.buttons)
            elif event.key == pygame.K_UP: self.focus = (self.focus - 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE): self.buttons[self.focus].action()
            elif event.key == pygame.K_s: self.scenario_index = (self.scenario_index + 1) % len(self.SCENARIOS)
            elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS): self.rounds = min(99, self.rounds + 1)
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS): self.rounds = max(1, self.rounds - 1)
            elif event.key == pygame.K_g: self.speed_index = (self.speed_index + 1) % len(self.SPEEDS)

    def draw(self, screen):
        self.poll()
        scale = WINDOW_HEIGHT / 620
        screen.fill((18, 18, 22))
        title_font = pygame.font.SysFont("Arial", int(32 * scale), bold=True)
        font = pygame.font.SysFont("Arial", int(18 * scale))
        title = title_font.render("Entwickler-Simulation", True, ORANGE)
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, int(42 * scale))))
        info = (f"Szenario [S]: {self.SCENARIOS[self.scenario_index].upper()}   "
                f"Runden [+/-]: {self.rounds}   Tempo [G]: {self.SPEEDS[self.speed_index]}×")
        screen.blit(font.render(info, True, WHITE), (int(90 * scale), int(82 * scale)))
        progress = min(1.0, self.completed / max(1, self.total))
        bar = pygame.Rect(int(150 * scale), int(116 * scale), int(600 * scale), int(18 * scale))
        pygame.draw.rect(screen, DARK_GREY, bar)
        pygame.draw.rect(screen, ORANGE, (bar.x, bar.y, int(bar.width * progress), bar.height))
        detail = (f"Fortschritt: {self.completed}/{self.total}   Szenario: {self.current_scenario}   "
                  f"Runde: {self.current_round}   Fehler: {self.errors}")
        screen.blit(font.render(detail, True, WHITE), (int(150 * scale), int(140 * scale)))
        for i, button in enumerate(self.buttons):
            button.is_hovered = button.is_hovered or i == self.focus
            button.draw(screen)
            if i != self.focus:
                button.is_hovered = False
        screen.blit(font.render(f"Status: {self.status}", True, WHITE),
                    (int(150 * scale), int(500 * scale)))
        error = "Letzter Fehler: " + (self.last_error or "–")
        screen.blit(font.render(error[:100], True, WHITE),
                    (int(150 * scale), int(530 * scale)))
