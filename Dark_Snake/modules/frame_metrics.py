"""Opt-in timings from the SDL event dequeue to display submission."""

from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from math import ceil
from statistics import median
import time

import pygame


SLOW_FRAME_NS = 33_300_000


def summarize_ns(samples):
    ordered = sorted(samples)
    if not ordered:
        return None
    count = len(ordered)
    return count, *(value / 1_000_000 for value in (
        median(ordered), ordered[ceil(0.95 * count) - 1], ordered[-1],
    ))


@dataclass
class _Action:
    kind: str
    read_ns: int
    accepted_ns: int
    applied_ns: int | None = None


class FrameMetrics:
    PHASES = (
        ("interval", "Bildabstand"),
        ("events", "Eingabeverarbeitung"),
        ("update", "Spiel-Update"),
        ("draw", "Zeichnen"),
        ("present", "Bildausgabe"),
    )

    def __init__(self, capacity=600):
        self.enabled = False
        self.capacity = capacity
        self.samples = defaultdict(lambda: deque(maxlen=self.capacity))
        self.rejected = Counter()
        self.slow_frames = 0
        self._previous_present = None
        self._queued_turns = {}
        self._applied_turns = {}
        self._head_images = {}
        self._fire = {}
        self._drawn = []
        self._font = None
        self._panel = None
        self._refresh_at = 0

    def toggle(self):
        enabled = not self.enabled
        self.__init__(self.capacity)
        self.enabled = enabled
        return enabled

    def stamp(self):
        return time.perf_counter_ns() if self.enabled else None

    def record_phase(self, phase, start, end):
        if start is not None and end is not None:
            self.samples[phase].append(end - start)

    def reject(self, kind, reason):
        if self.enabled:
            self.rejected[kind, reason] += 1

    def _accept(self, kind, read_ns, accepted_ns):
        if not self.enabled or read_ns is None or accepted_ns is None:
            return None
        self.samples[kind, "accept"].append(accepted_ns - read_ns)
        return _Action(kind, read_ns, accepted_ns)

    def accept_direction(self, player, direction, read_ns):
        action = self._accept("direction", read_ns, self.stamp())
        if action is None:
            return
        if player in self._queued_turns:
            self.reject("direction", "überschrieben")
        self._queued_turns[player] = (direction, action)

    def apply_direction(self, player, direction):
        pending = self._queued_turns.pop(player, None)
        if pending is None:
            return
        intended_direction, action = pending
        if intended_direction != direction:
            self.reject("direction", "verworfen")
            return
        action.applied_ns = self.stamp()
        self.samples["direction", "wait"].append(action.applied_ns - action.accepted_ns)
        if player in self._applied_turns:
            self.reject("direction", "vor Bild ersetzt")
        self._applied_turns[player] = action

    def apply_fire(self, projectile, read_ns, accepted_ns):
        action = self._accept("fire", read_ns, accepted_ns)
        if action is None:
            return
        action.applied_ns = self.stamp()
        self.samples["fire", "apply"].append(action.applied_ns - accepted_ns)
        self._fire[projectile] = action

    def cancel_pending(self):
        for _ in range(len(self._queued_turns) + len(self._applied_turns)):
            self.reject("direction", "abgebrochen")
        for _ in self._fire:
            self.reject("fire", "abgebrochen")
        self._queued_turns.clear()
        self._applied_turns.clear()
        self._head_images.clear()
        self._fire.clear()

    def head_drawn(self, player, pos, angle):
        signature = (int(pos[0]), int(pos[1]), angle)
        previous = self._head_images.get(player)
        self._head_images[player] = signature
        if signature != previous:
            action = self._applied_turns.pop(player, None)
            if action is not None:
                self._drawn.append(action)

    def fire_drawn(self, projectile):
        action = self._fire.pop(projectile, None)
        if action is not None:
            self._drawn.append(action)

    def finish_frame(self, presented_ns):
        if presented_ns is None:
            return
        if self._previous_present is not None:
            interval = presented_ns - self._previous_present
            self.samples["interval"].append(interval)
            self.slow_frames += interval > SLOW_FRAME_NS
        self._previous_present = presented_ns
        for action in self._drawn:
            self.samples[action.kind, "visible"].append(presented_ns - action.read_ns)
            self.samples[action.kind, "present"].append(presented_ns - action.applied_ns)
        self._drawn.clear()
        for _ in self._fire:
            self.reject("fire", "vor Bild entfernt")
        self._fire.clear()

    def draw(self, screen):
        now = self.stamp()
        if self._panel is None or now >= self._refresh_at:
            self._rebuild_panel()
            self._refresh_at = now + 250_000_000
        screen.blit(self._panel, (screen.get_width() - self._panel.get_width() - 12, 45))

    def _rebuild_panel(self):
        if self._font is None:
            self._font = pygame.font.SysFont("Consolas", 14)
        intervals = self.samples["interval"]
        fps = 1_000_000_000 * len(intervals) / sum(intervals) if intervals else 0
        lines = [
            f"{fps:5.1f} FPS | Budget 16,67 ms | über 33,3 ms: {self.slow_frames}",
            f"{'Messstrecke (ms)':<24} {'n':>4} {'Median':>7} {'p95':>7} {'Max':>7}",
        ]
        rows = self.PHASES + (
            (("direction", "accept"), "Richtung: Event→Annahme"),
            (("direction", "wait"), "Wartezeit Rasterzug"),
            (("direction", "present"), "Richtung: Zug→Bild"),
            (("direction", "visible"), "Richtung: Event→Bild"),
            (("fire", "accept"), "Feuer: Event→Annahme"),
            (("fire", "apply"), "Feuer: Annahme→Anlage"),
            (("fire", "present"), "Feuer: Anlage→Bild"),
            (("fire", "visible"), "Feuer: Event→Bild"),
        )
        for key, label in rows:
            stats = summarize_ns(self.samples[key])
            if stats is None:
                lines.append(f"{label:<24} {'0':>4}")
            else:
                n, p50, p95, peak = stats
                lines.append(f"{label:<24} {n:4d} {p50:7.2f} {p95:7.2f} {peak:7.2f}")
        cooldown = self.rejected["fire", "cooldown"]
        rejected_turns = sum(count for (kind, _), count in self.rejected.items() if kind == "direction")
        rejected_fires = sum(count for (kind, _), count in self.rejected.items() if kind == "fire")
        lines.append(f"Verworfen: Richtung {rejected_turns} | Feuer {rejected_fires - cooldown} | Cooldown {cooldown}")
        lines.append("Interne Messung ab SDL-Auslesen, ohne Gerät und Monitor")
        rendered = [self._font.render(line, True, (240, 245, 255)) for line in lines]
        line_height = self._font.get_linesize()
        self._panel = pygame.Surface((max(line.get_width() for line in rendered) + 16,
                                      line_height * len(lines) + 16), pygame.SRCALPHA)
        self._panel.fill((9, 16, 29, 228))
        for i, line in enumerate(rendered):
            self._panel.blit(line, (8, 8 + i * line_height))
