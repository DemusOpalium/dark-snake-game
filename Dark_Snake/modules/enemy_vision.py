"""Shared, deterministic grid eyesight for Classic/FrostAge/Mycelium enemies.

Pure perception: this module NEVER moves an enemy, deals damage or emits loot.
Detection is based on a grid-aligned view cone, *supercover* line-of-sight
and an optional short memory of the last visible player head. No Pygame needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, hypot, radians
from typing import Iterable

Cell = tuple[int, int]
Target = tuple[int, Cell]


@dataclass(frozen=True, slots=True)
class VisionProfile:
    radius_cells: float = 5.0
    fov_degrees: float = 100.0
    memory_seconds: float = 1.5
    scan_interval: float = 0.15

    def __post_init__(self):
        if not 0 < self.radius_cells <= 100:
            raise ValueError("Sichtweite muss zwischen 0 und 100 Feldern liegen.")
        if not 0 < self.fov_degrees <= 360:
            raise ValueError("Sichtwinkel muss zwischen 0 und 360 Grad liegen.")
        if not 0 <= self.memory_seconds <= 60:
            raise ValueError("Erinnerungszeit muss zwischen 0 und 60 Sekunden liegen.")
        if not 0.02 <= self.scan_interval <= 2:
            raise ValueError("Sichtprüfintervall muss zwischen 0,02 und 2 Sekunden liegen.")


@dataclass(frozen=True, slots=True)
class VisionResult:
    """The current observation, not a command to attack.

    kind: UNAWARE, VISIBLE or SEARCHING. During SEARCHING the last confirmed
    player position remains available, but the target is NOT visible.
    """
    kind: str = "UNAWARE"
    target_player: int | None = None
    last_known_cell: Cell | None = None
    last_seen_at: float | None = None

    @property
    def visible(self) -> bool:
        return self.kind == "VISIBLE"


def supercover_cells(start: Cell, end: Cell):
    """Visit every grid cell a centre-to-centre ray touches.

    A ray exactly through a tile corner touches *both* adjacent cells:
    conservative cover prevents corner-peeking through diagonal walls.
    """
    x, y = start
    tx, ty = end
    dx, dy = tx - x, ty - y
    nx, ny = abs(dx), abs(dy)
    sx = (dx > 0) - (dx < 0)
    sy = (dy > 0) - (dy < 0)
    ix = iy = 0
    yield x, y
    while ix < nx or iy < ny:
        comparison = (1 + 2 * ix) * ny - (1 + 2 * iy) * nx
        if comparison == 0:
            # A corner crossing touches its two orthogonal neighbours too.
            yield x + sx, y
            yield x, y + sy
            x += sx
            y += sy
            ix += 1
            iy += 1
        elif comparison < 0:
            x += sx
            ix += 1
        else:
            y += sy
            iy += 1
        yield x, y


def has_line_of_sight(start: Cell, end: Cell, blockers) -> bool:
    """Treat author-defined WALL/BARRIER cells as opaque; art alone isn't a wall."""
    return not any(cell != start and cell in blockers
                   for cell in supercover_cells(start, end))


def can_see(origin: Cell, facing: Cell, target: Cell,
            profile: VisionProfile, blockers=frozenset()) -> bool:
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    distance_sq = dx * dx + dy * dy
    if distance_sq > profile.radius_cells * profile.radius_cells:
        return False
    if distance_sq and profile.fov_degrees < 360:
        fx, fy = facing
        face_size = hypot(fx, fy)
        if face_size == 0:
            return False
        # Avoid acos and angle wraparound, correct in every quadrant.
        dot = dx * fx + dy * fy
        limit = hypot(dx, dy) * face_size * cos(radians(profile.fov_degrees / 2))
        if dot < limit - 1e-10:
            return False
    return has_line_of_sight(origin, target, blockers)


class VisionSensor:
    """One sensor per opponent. A timed reading, zero side effects on combat."""

    def __init__(self, profile: VisionProfile):
        self.profile = profile
        self.result = VisionResult()
        self.next_scan_at = float("-inf")

    def observe(self, origin: Cell, facing: Cell, targets: Iterable[Target],
                blockers, now: float) -> VisionResult:
        # Only check geometry about 6-7 times/second, not once per frame.
        # Future calls keep the same observation until this sensor's next tick.
        if now < self.next_scan_at:
            return self.result
        self.next_scan_at = now + self.profile.scan_interval
        visible = []
        for player, cell in targets:
            if can_see(origin, facing, cell, self.profile, blockers):
                dist = (cell[0] - origin[0]) ** 2 + (cell[1] - origin[1]) ** 2
                visible.append((dist, player, cell))
        if visible:
            # Always deterministic for equidistant 1P/2P targets.
            _, player, cell = min(visible)
            self.result = VisionResult("VISIBLE", player, cell, now)
        elif (self.result.last_seen_at is not None
              and now - self.result.last_seen_at <= self.profile.memory_seconds):
            self.result = VisionResult(
                "SEARCHING", self.result.target_player,
                self.result.last_known_cell, self.result.last_seen_at
            )
        else:
            self.result = VisionResult()
        return self.result

    def reset(self):
        self.result = VisionResult()
        self.next_scan_at = float("-inf")
