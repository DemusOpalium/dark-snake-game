"""In-game controls for the headless developer simulation."""

from __future__ import annotations

import json
import threading

import pygame

from config import DARK_GREY, ORANGE, PURPLE, RED, WHITE, WINDOW_HEIGHT, WINDOW_WIDTH
from developer_simulator import SimulationControl, format_text_report, run_simulation
from modules.resources import user_data_path
from modules.ui import Button


class SimulationMenu:
    """Small non-blocking front end; the pygame event loop stays on the main thread."""

    SCENARIOS = ("1p", "2p", "boss", "portal", "aoe", "projectiles", "bolbu",
                 "restart", "game_over")
    SPEEDS = (0.25, 1.0, 5.0, 20.0)

    def __init__(self, game):
        self.game = game
        self.scenario_index = 0
        self.rounds = 3
        self.speed_index = 2
        self.control = None
        self.thread = None
        self.report = None
        self.status = "Bereit"
        self.focus = 0
        x, y, w, h = WINDOW_WIDTH // 2 - 260, 260, 155, 42
        actions = (self.start, self.pause, self.cancel, self.save_text, self.save_json,
                   lambda: game.set_state(game.intro_state()))
        labels = ("Start", "Pause", "Abbrechen", "TXT speichern", "JSON speichern", "Zurück")
        self.buttons = [Button(x + (i % 3) * (w + 25), y + (i // 3) * 58, w, h,
                               labels[i], color=RED if i == 2 else PURPLE, action=actions[i])
                        for i in range(len(labels))]

    @property
    def running(self):
        return bool(self.thread and self.thread.is_alive())

    def start(self):
        if self.running:
            return
        self.report = None
        self.control = SimulationControl()
        self.status = "Simulation läuft …"
        scenario = self.SCENARIOS[self.scenario_index]

        def worker():
            self.report = run_simulation(self.rounds, steps=120,
                                         step_seconds=self.SPEEDS[self.speed_index],
                                         scenarios=(scenario,), control=self.control)
            self.status = "Abgebrochen" if self.control.cancelled else "Abgeschlossen"

        self.thread = threading.Thread(target=worker, name="DarkSnakeSimulation", daemon=True)
        self.thread.start()

    def pause(self):
        if self.control and self.running:
            self.control.toggle_pause()
            self.status = "Pausiert" if self.control.paused else "Simulation läuft …"

    def cancel(self):
        if self.control:
            self.control.cancel()
            self.status = "Abbruch wird ausgeführt …"

    def _save(self, kind):
        if not self.report:
            self.status = "Noch kein Bericht vorhanden"
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
        if event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.check_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.focus = i
                    button.check_hover(event.pos)
                    button.handle_event(event)
            # Clickable selectors, placed above the action buttons.
            if 225 <= event.pos[1] <= 250:
                if event.pos[0] < WINDOW_WIDTH // 2:
                    self.scenario_index = (self.scenario_index + 1) % len(self.SCENARIOS)
                elif event.pos[0] < WINDOW_WIDTH // 2 + 150:
                    self.rounds = 1 if self.rounds >= 99 else self.rounds + 1
                else:
                    self.speed_index = (self.speed_index + 1) % len(self.SPEEDS)
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_RIGHT): self.focus = (self.focus + 1) % len(self.buttons)
            elif event.key == pygame.K_LEFT: self.focus = (self.focus - 1) % len(self.buttons)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE): self.buttons[self.focus].action()
            elif event.key == pygame.K_s: self.scenario_index = (self.scenario_index + 1) % len(self.SCENARIOS)
            elif event.key in (pygame.K_PLUS, pygame.K_KP_PLUS): self.rounds = min(99, self.rounds + 1)
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS): self.rounds = max(1, self.rounds - 1)
            elif event.key == pygame.K_g: self.speed_index = (self.speed_index + 1) % len(self.SPEEDS)

    def draw(self, screen):
        screen.fill((18, 18, 22))
        title = pygame.font.SysFont("Arial", 38, bold=True).render("Entwickler-Simulation", True, ORANGE)
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 70)))
        font = pygame.font.SysFont("Arial", 22)
        info = (f"Szenario [S]: {self.SCENARIOS[self.scenario_index].upper()}     "
                f"Runden [+/-]: {self.rounds}     Geschwindigkeit [G]: {self.SPEEDS[self.speed_index]}×")
        screen.blit(font.render(info, True, WHITE), (WINDOW_WIDTH // 2 - 350, 150))
        runs = len(self.report["runs"]) if self.report else (self.control.completed if self.control else 0)
        total = self.rounds
        errors = (sum(len(v) for v in self.report["failure_groups"].values()) if self.report else
                  (self.control.errors if self.control else 0))
        progress = min(1.0, runs / max(1, total))
        pygame.draw.rect(screen, DARK_GREY, (WINDOW_WIDTH // 2 - 300, 195, 600, 20))
        pygame.draw.rect(screen, ORANGE, (WINDOW_WIDTH // 2 - 300, 195, int(600 * progress), 20))
        screen.blit(font.render(f"Fortschritt: {runs}/{total}   Fehler: {errors}", True, WHITE),
                    (WINDOW_WIDTH // 2 - 300, 220))
        for i, button in enumerate(self.buttons):
            button.is_hovered = button.is_hovered or i == self.focus
            button.draw(screen)
            if i != self.focus: button.is_hovered = False
        last = self.control.last_error if self.control else None
        lines = [self.status, "Letzter Fehler: " + (last or "–")]
        for i, line in enumerate(lines):
            screen.blit(font.render(line[:100], True, WHITE), (WINDOW_WIDTH // 2 - 300, 405 + i * 32))
