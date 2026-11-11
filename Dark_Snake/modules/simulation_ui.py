"""Responsive in-game controls for the developer simulation."""

from __future__ import annotations

import multiprocessing
import os
import queue
import random
import time
from bisect import bisect_right
from concurrent.futures import ThreadPoolExecutor

import pygame

from config import DARK_GREY, ORANGE, PURPLE, RED, WHITE, WINDOW_HEIGHT, WINDOW_WIDTH
from developer_simulator import (SCENARIOS, SIMULATION_PROFILES, SimulationControl,
                                 failed_simulation_report, run_simulation, save_report)
from modules.simulation_reports import latest_report, report_directory


def simulation_worker(messages, resume_event, cancel_event, options):
    """Process entry point; run_simulation owns its hidden dummy display."""
    control = SimulationControl(resume_event, cancel_event)
    started_at = time.monotonic()
    try:
        messages.put({"type": "started"})
        report = run_simulation(control=control, progress=messages.put, **options)
        messages.put({"type": "finished", "report": report})
    except BaseException as exc:
        scenarios = options["scenarios"]
        report = failed_simulation_report(
            exc, scenarios, options["base_seed"],
            planned_runs=options["rounds"] * len(scenarios),
            duration_seconds=time.monotonic() - started_at,
        )
        messages.put({"type": "fatal", "error": f"{type(exc).__name__}: {exc}",
                      "report": report})


class SimulationMenu:
    """Non-blocking front end; pygame remains exclusively on the main thread."""

    SCENARIOS = ("all",) + SCENARIOS
    SPEEDS = (0.25, 1.0, 5.0, 20.0)
    PROFILES = ("smoke", "normal", "stress")
    TIMEOUT_SECONDS = 10.0

    def __init__(self, game, process_context=None, monotonic=time.monotonic):
        # A spawned simulation imports this module before its SDL display exists.
        from modules.ui import Button

        self.game = game
        self._context = process_context or multiprocessing.get_context("spawn")
        self._monotonic = monotonic
        self.scenario_index = 0
        self.rounds = 3
        self.speed_index = 2
        self.profile_index = 1
        self.process = self.messages = self.resume_event = self.cancel_event = None
        self.report = None
        self.report_paths = None
        self.last_report_paths = None
        self.report_directory = None
        self.report_notice = None
        self._report_location_loaded = False
        self._report_write = None
        self._leave_after_run = False
        self._started_at = None
        self._selected_scenarios = ()
        self.status = "Bereit"
        self.current_scenario = "–"
        self.current_round = self.completed = self.errors = 0
        self.total = self.rounds
        self.last_error = None
        self.bot_action = "–"
        self.current_game_state = "–"
        self.last_message_at = None
        self.base_seed = None
        self.focus = 0

        scale = WINDOW_HEIGHT / 620
        w, h, gap = int(360 * scale), int(40 * scale), int(8 * scale)
        x, y = WINDOW_WIDTH // 2 - w - gap // 2, int(190 * scale)
        controls = (
            ("Start", self.start), ("Pause", self.pause),
            ("Abbrechen", self.cancel), ("Bericht speichern", self.save_report_files),
            ("Berichtsordner öffnen", self.open_report_directory), ("Zurück", self.back),
        )
        self.buttons = []
        for i, (label, action) in enumerate(controls):
            row, column = divmod(i, 2)
            self.buttons.append(Button(x + column * (w + gap), y + row * (h + gap),
                                       w, h, label, color=RED if i == 2 else PURPLE,
                                       action=action))

    @property
    def running(self):
        return bool(self.process and self.process.is_alive())

    def start(self):
        self.poll()
        if self.running or self._report_write is not None:
            return
        self._dispose_worker()
        self.report = self.report_paths = self.report_notice = None
        self.status = "Läuft"
        self.current_scenario = self.SCENARIOS[self.scenario_index]
        self.current_round = self.completed = self.errors = 0
        chosen = self.SCENARIOS[self.scenario_index]
        selected = SCENARIOS if chosen == "all" else (chosen,)
        self._selected_scenarios = selected
        self.total = self.rounds * len(selected)
        self.last_error = None
        self.messages = self._context.Queue()
        self.resume_event = self._context.Event()
        self.resume_event.set()
        self.cancel_event = self._context.Event()
        self.base_seed = random.SystemRandom().randrange(2**32)
        options = {"rounds": self.rounds, "steps": 120,
                   "step_seconds": self.SPEEDS[self.speed_index],
                   "scenarios": selected, "base_seed": self.base_seed,
                   "profile": self.PROFILES[self.profile_index]}
        self.process = self._context.Process(
            target=simulation_worker,
            args=(self.messages, self.resume_event, self.cancel_event, options),
            name="DarkSnakeSimulation", daemon=True)
        self._started_at = self.last_message_at = self._monotonic()
        self.process.start()

    def pause(self):
        if not self.running or self.cancel_event.is_set():
            return
        if self.resume_event.is_set():
            self.resume_event.clear()
            self.status = "Pausiert"
        else:
            self.resume_event.set()
            self.status = "Läuft"
            self.last_message_at = self._monotonic()

    def cancel(self):
        self.poll()
        if not self.running or self.cancel_event.is_set():
            return
        self.cancel_event.set()
        self.resume_event.set()
        self.last_message_at = self._monotonic()
        self.status = "Abbruch läuft"

    def back(self):
        if self.process:
            self._leave_after_run = True
            self.cancel()
        else:
            self._return_to_menu()

    def _return_to_menu(self):
        self._leave_after_run = False
        self._reset_run_state()
        self.game.set_state(self.game.intro_state())

    def poll(self):
        """Consume worker messages; call once per UI frame."""
        self._poll_report_write()
        worker_exited = self.process is not None and not self.process.is_alive()
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
                    self.bot_action = message.get("bot_action", self.bot_action)
                    self.current_game_state = message.get("game_state", self.current_game_state)
                elif kind == "heartbeat":
                    self.current_scenario = message["scenario"]
                    self.current_round = message["round"]
                    self.bot_action = message.get("bot_action", "–")
                    self.current_game_state = message.get("game_state", "–")
                elif kind == "fatal":
                    self._stop_worker()
                    self._finish_run(message["report"], "Worker-Fehler", message["error"])
                    return
                elif kind == "finished":
                    self._dispose_worker()
                    self._finish_run(message["report"])
                    return

        paused = self.resume_event is not None and not self.resume_event.is_set()
        if (self.running and not paused and self.last_message_at is not None and
                self._monotonic() - self.last_message_at > self.TIMEOUT_SECONDS):
            cancelling = self.cancel_event.is_set()
            self._stop_worker()
            if cancelling:
                self._record_worker_failure("Abgebrochen", "Worker hat den Abbruch nicht bestätigt.",
                                            reason="cancelled")
            else:
                self._record_worker_failure("Timeout", "Worker lieferte keinen Heartbeat.",
                                            reason="timeout")
        elif worker_exited:
            exitcode = getattr(self.process, "exitcode", "unbekannt")
            self._dispose_worker()
            self._record_worker_failure("Worker-Fehler",
                                        f"Worker unerwartet beendet (Exitcode {exitcode})")

    def _record_worker_failure(self, status, cause, *, reason="exception"):
        report = failed_simulation_report(
            RuntimeError(cause) if reason == "exception" else cause,
            self._selected_scenarios, self.base_seed, reason=reason,
            planned_runs=self.total, duration_seconds=self._monotonic() - self._started_at,
        )
        self._finish_run(report, status, cause)

    def _finish_run(self, report, status=None, cause=None):
        self.report = report
        outcome = report["outcome"]
        labels = {
            "completed": "Fertig",
            "incomplete": "Fehler",
            "rule_failed": "Regelprüfung fehlgeschlagen",
            "exception": "Fehler",
            "timeout": "Timeout",
            "cancelled": "Abgebrochen",
        }
        self.status = status or labels[outcome["status"]]
        self.errors = report["summary"]["technical_exceptions"]
        self.last_error = cause or (
            outcome["reason"] if outcome["status"] not in ("completed", "cancelled") else None
        )
        self.save_report_files()
        if self._leave_after_run:
            self._return_to_menu()

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
        self.report = self.report_paths = None
        self.status = "Bereit"
        self.current_scenario = "–"
        self.current_round = self.completed = self.errors = 0
        self.total = self.rounds
        self.last_error = None
        self.bot_action = self.current_game_state = "–"

    def save_report_files(self):
        if self._report_write is not None:
            return
        if not self.report:
            self.report_notice = "Noch kein Bericht vorhanden."
            return
        if self.report_paths is not None:
            self.report_notice = "Dieser Bericht ist bereits gespeichert."
            return
        scenarios = self.report["configuration"]["scenarios"]
        scenario = scenarios[0] if len(scenarios) == 1 else "all"
        self.report_notice = "Bericht wird gespeichert …"
        writer = ThreadPoolExecutor(max_workers=1, thread_name_prefix="SnakeReport")
        self._report_write = writer.submit(save_report, self.report, scenario=scenario)
        writer.shutdown(wait=False)

    def _poll_report_write(self):
        future = self._report_write
        if future is None or not future.done():
            return
        self._report_write = None
        try:
            paths = future.result()
        except Exception as error:
            self.report_notice = f"Bericht konnte nicht gespeichert werden. {error}"
            return
        if self.report is not None:
            self.report_paths = paths
        self.last_report_paths = paths
        self.report_directory = paths[0].parent
        self._report_location_loaded = True
        self.report_notice = "TXT und JSON gespeichert."

    def _load_report_location(self):
        if self._report_location_loaded:
            return
        self._report_location_loaded = True
        try:
            self.last_report_paths = latest_report()
            self.report_directory = (self.last_report_paths[0].parent if self.last_report_paths
                                     else report_directory())
        except OSError as error:
            self.report_notice = f"Berichtsordner nicht verfügbar. {error}"

    def open_report_directory(self):
        self._poll_report_write()
        self._load_report_location()
        if self.report_directory is None:
            return
        startfile = getattr(os, "startfile", None)
        if startfile is None:
            self.report_notice = "Berichtsordner bitte über den angezeigten Pfad öffnen."
            return
        try:
            startfile(self.report_directory)
        except OSError as error:
            self.report_notice = f"Berichtsordner konnte nicht geöffnet werden. {error}"

    def save_text(self): self.save_report_files()
    def save_json(self): self.save_report_files()

    def _report_lines(self):
        yield f"Status: {self.status}"
        if self.last_error:
            yield f"Letzter Fehler: {self.last_error}"
        if self.report:
            summary = self.report["summary"]
            yield (
                f"Regelprüfungen: {summary['rule_checks_passed']} bestanden, "
                f"{summary['rule_checks_failed']} fehlgeschlagen, "
                f"{summary['rule_checks_not_run']} nicht ausgeführt"
            )
            yield f"Zeitüberschreitungen: {summary['timeouts']}   Abbrüche: {summary['cancelled']}"
        yield f"Berichtsordner: {self.report_directory or '–'}"
        latest = f"{self.last_report_paths[0].stem} (.txt und .json)" if self.last_report_paths else "–"
        yield f"Letzter Bericht: {latest}"
        if self.report_notice:
            yield self.report_notice

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
            elif event.key == pygame.K_p: self.profile_index = (self.profile_index + 1) % len(self.PROFILES)

    def draw(self, screen):
        self.poll()
        self._load_report_location()
        scale = WINDOW_HEIGHT / 620
        screen.fill((18, 18, 22))
        title_font = pygame.font.SysFont("Arial", int(32 * scale), bold=True)
        font = pygame.font.SysFont("Arial", int(18 * scale))
        title = title_font.render("Entwickler-Simulation", True, ORANGE)
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, int(42 * scale))))
        scenario_label = ("ALLE SZENARIEN" if self.SCENARIOS[self.scenario_index] == "all"
                          else self.SCENARIOS[self.scenario_index].upper())
        profile_label = self.PROFILES[self.profile_index].capitalize()
        seconds = SIMULATION_PROFILES[self.PROFILES[self.profile_index]]
        info = (f"Profil [P]: {profile_label} ({seconds}s)   Szenario [S]: {scenario_label}   "
                f"Runden [+/-]: {self.rounds}   Fast-Forward [G]: {self.SPEEDS[self.speed_index]}×")
        screen.blit(font.render(info, True, WHITE), (int(90 * scale), int(82 * scale)))
        progress = min(1.0, self.completed / max(1, self.total))
        bar = pygame.Rect(int(150 * scale), int(116 * scale), int(600 * scale), int(18 * scale))
        pygame.draw.rect(screen, DARK_GREY, bar)
        pygame.draw.rect(screen, ORANGE, (bar.x, bar.y, int(bar.width * progress), bar.height))
        detail = (f"Fortschritt: {self.completed}/{self.total}   Szenario: {self.current_scenario}   "
                  f"Runde: {self.current_round}   Technische Ausnahmen: {self.errors}")
        screen.blit(font.render(detail, True, WHITE), (int(150 * scale), int(140 * scale)))
        live = f"Bot: {self.bot_action}   GameState: {self.current_game_state}"
        screen.blit(font.render(live, True, WHITE), (int(150 * scale), int(164 * scale)))
        for i, button in enumerate(self.buttons):
            button.is_hovered = button.is_hovered or i == self.focus
            button.draw(screen)
            if i != self.focus:
                button.is_hovered = False
        x, y = int(40 * scale), int(350 * scale)
        width = screen.get_width() - 2 * x
        line_height = font.get_linesize()
        for detail in self._report_lines():
            for line in detail.splitlines():
                while line and y + line_height <= screen.get_height():
                    end = bisect_right(range(1, len(line) + 1), width,
                                       key=lambda length: font.size(line[:length])[0])
                    end = max(1, end)
                    screen.blit(font.render(line[:end], True, WHITE), (x, y))
                    y += line_height
                    line = line[end:]
            y += int(4 * scale)
