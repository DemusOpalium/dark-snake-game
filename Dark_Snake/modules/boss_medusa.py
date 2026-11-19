"""Medusa Eyes A: opt-in boss perception, remote eyes and bounded prediction.

Pure grid logic: no pygame, graphics, damage, teleports or projectile spawning.
Only the existing admin KI-Test switch activates this pilot in Classic.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from modules.enemy_vision import VisionProfile, VisionResult, VisionSensor

BOSS_SIGHT = VisionProfile(
    radius_cells=9, fov_degrees=220, alert_radius_cells=14,
    memory_seconds=4, scan_interval=.05, reaction_seconds=.10,
)
BOSS2_SIGHT = VisionProfile(
    radius_cells=11, fov_degrees=300, alert_radius_cells=17,
    memory_seconds=5, scan_interval=.05, reaction_seconds=.08,
)
EYE_SIGHT = VisionProfile(
    radius_cells=4, fov_degrees=360, memory_seconds=0,
    scan_interval=.05,
)


@dataclass(frozen=True)
class MedusaReading:
    kind: str = "UNAWARE"  # VISIBLE / RELAY / SEARCHING / UNAWARE
    target_player: int | None = None
    last_known_cell: tuple[int, int] | None = None
    predicted_cell: tuple[int, int] | None = None
    source: str = "none"

    @property
    def actionable(self):
        return self.kind in ("VISIBLE", "RELAY", "SEARCHING")


@dataclass
class RemoteEye:
    cell: tuple[int, int]
    expires_at: float
    vision: VisionSensor


def legal_boss_step(position, move, size, blockers, grid_size):
    """Prevent any part of a size-by-size boss crossing authored walls."""
    dx, dy = move
    if max(abs(dx), abs(dy)) > 1:
        return False
    x, y = position[0] + dx, position[1] + dy
    if not (0 <= x <= grid_size[0] - size
            and 0 <= y <= grid_size[1] - size):
        return False
    return all((bx, by) not in blockers
               for bx in range(x, x + size) for by in range(y, y + size))


def medusa_step(position, size, target, blockers, grid_size):
    """Deterministic approach using the boss footprint; no teleport or speedup."""
    if target is None:
        return None
    # Compare distances from the true footprint center, not its upper-left.
    def distance(x, y):
        return (x + size / 2 - target[0]) ** 2 + (y + size / 2 - target[1]) ** 2

    current = distance(*position)
    options = []
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1),
                   (1, 1), (-1, 1), (-1, -1), (1, -1)):
        if not legal_boss_step(position, (dx, dy), size, blockers, grid_size):
            continue
        if dx and dy and not (
            legal_boss_step(position, (dx, 0), size, blockers, grid_size)
            and legal_boss_step(position, (0, dy), size, blockers, grid_size)
        ):
            continue
        score = distance(position[0] + dx, position[1] + dy)
        if score < current:
            options.append((score, abs(dx) + abs(dy), dx, dy))
    return min(options)[-2:] if options else (0, 0)


class MedusaEyes:
    """Boss eye + two persistent remote sensors, opt-in and resettable.

    The boss never reads players through walls. Remote eyes also need real
    line-of-sight. Prediction uses two *observed* cells, capped at two tiles.
    """

    MAX_EYES = 2
    EYE_DURATION = 9.
    EYE_COOLDOWN = 9.

    def __init__(self, *, heavy=False):
        self.profile = BOSS2_SIGHT if heavy else BOSS_SIGHT
        self.direct = VisionSensor(self.profile)
        self.remote: list[RemoteEye] = []
        self.next_eye_at = float("-inf")
        self.last_seen = None  # (player, position, observed_time)
        self.last_known_at = float("-inf")
        self.reading = MedusaReading()

    def reset(self):
        self.direct.reset()
        self.remote.clear()
        self.next_eye_at = float("-inf")
        self.last_seen = None
        self.last_known_at = float("-inf")
        self.reading = MedusaReading()

    def observe(self, origin, facing, targets, blockers, now, grid_size):
        # All sensors use the same real, current player positions.
        targets = tuple(targets)
        self.remote = [eye for eye in self.remote if now < eye.expires_at]
        primary = self.direct.observe(origin, facing, targets, blockers, now)
        result = primary if primary.visible else None
        source = "direct" if primary.visible else "none"
        if result is None:
            for eye in self.remote:
                seen = eye.vision.observe(
                    eye.cell, (1, 0), targets, blockers, now,
                )
                if seen.visible:
                    result = seen
                    source = "relay"
                    break

        if result is not None:
            player = result.target_player
            cell = result.last_known_cell
            previous = self.last_seen
            predicted = cell
            if (previous is not None and previous[0] == player
                    and previous[1] != cell
                    and .02 <= now - previous[2] <= 2):
                dt = now - previous[2]
                # A short, imperfect lead; not an omniscient projectile target.
                lead_x = round(max(-2, min(2, (cell[0] - previous[1][0]) * .35 / dt)))
                lead_y = round(max(-2, min(2, (cell[1] - previous[1][1]) * .35 / dt)))
                predicted = (
                    max(0, min(grid_size[0] - 1, cell[0] + lead_x)),
                    max(0, min(grid_size[1] - 1, cell[1] + lead_y)),
                )
            if previous is None or previous[0] != player or previous[1] != cell:
                self.last_seen = (player, cell, now)
            self.last_known_at = now
            self.reading = MedusaReading(
                "VISIBLE" if source == "direct" else "RELAY",
                player, cell, predicted, source,
            )
            # Placed at the old boss position: it still watches after boss moves.
            if (source == "direct" and now >= self.next_eye_at
                    and len(self.remote) < self.MAX_EYES
                    and all(eye.cell != origin for eye in self.remote)):
                self.remote.append(RemoteEye(
                    origin, now + self.EYE_DURATION, VisionSensor(EYE_SIGHT),
                ))
                self.next_eye_at = now + self.EYE_COOLDOWN
        elif (self.reading.last_known_cell is not None
              and now - self.last_known_at <= self.profile.memory_seconds):
            self.reading = MedusaReading(
                "SEARCHING", self.reading.target_player,
                self.reading.last_known_cell, self.reading.last_known_cell,
                "memory",
            )
        else:
            self.reading = MedusaReading()
            self.last_seen = None
        return self.reading
