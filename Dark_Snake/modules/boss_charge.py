"""Medusa Roll/Charge A: one observable, locked and bounded dash.

Pure grid geometry and timing; does not modify health, gameplay objects,
pygame surfaces or other boss attacks. Intended for the existing KI-Test
pilot, never silently enabled in legacy Classic.
"""
from __future__ import annotations

from dataclasses import dataclass, field


Cell = tuple[int, int]
Point = tuple[float, float]
# B tuning from Demus' 20 Nov Windows playtest:
# Double peak reach, a quicker but still visible tell, then longer downtime.
WARNING_SECONDS = .65
CHARGE_SECONDS = .22
RECOVERY_SECONDS = 1.35
COOLDOWN_SECONDS = 7.0
MAX_CELLS = 8
PREFERRED_MIN_CELLS = 4


def swept_footprint(a: Point, b: Point, size: int, cell: Cell) -> bool:
    """Axis-aligned continuous sweep; no tunneling at low frame rates."""
    return (min(a[0], b[0]) < cell[0] + 1
            and max(a[0], b[0]) + size > cell[0]
            and min(a[1], b[1]) < cell[1] + 1
            and max(a[1], b[1]) + size > cell[1])


def _footprint_clear(position: Cell, size: int, blocked: set[Cell],
                     grid: Cell) -> bool:
    x, y = position
    if not (0 <= x <= grid[0] - size and 0 <= y <= grid[1] - size):
        return False
    return all((cx, cy) not in blocked
               for cx in range(x, x + size) for cy in range(y, y + size))


def choose_charge(start: Cell, size: int, observed_target: Cell,
                  walls, grid: Cell, bodies=()) -> Cell | None:
    """Pick a cardinal 4–8 cell lane (2–3 if constrained) from observed aim.

    Check every intermediate FULL boss footprint against authored walls and
    both snakes' non-head bodies. Heads are hit targets, not path blockers.
    No current player state is consulted for aiming.
    """
    if observed_target is None or size < 1:
        return None
    walls = set(walls)
    bodies = set(bodies)
    cx, cy = start[0] + size / 2, start[1] + size / 2
    tx, ty = observed_target[0] + .5, observed_target[1] + .5
    dx, dy = tx - cx, ty - cy
    if abs(dx) >= abs(dy):
        direction = (1 if dx > 0 else -1, 0)
        along, side = abs(dx), abs(dy)
    else:
        direction = (0, 1 if dy > 0 else -1)
        along, side = abs(dy), abs(dx)
    # A charge is not an omnidirectional lunge across the board.
    if along < size / 2 + 1.0 or side > size / 2 + 1.0:
        return None
    stride = min(MAX_CELLS, max(PREFERRED_MIN_CELLS, round(along - size / 2)))
    for distance in range(stride, 1, -1):
        if all(_footprint_clear(
            (start[0] + step * direction[0],
             start[1] + step * direction[1]),
            size, walls | bodies, grid,
        ) for step in range(1, distance + 1)):
            return (start[0] + distance * direction[0],
                    start[1] + distance * direction[1])
    return None


@dataclass
class ChargeAction:
    start: Cell
    destination: Cell
    target: Cell
    began_at: float
    hit_players: set[str] = field(default_factory=set)
    last_position: Point | None = None
    started: bool = False
    finished_motion: bool = False

    def __post_init__(self):
        self.last_position = self.start

    @property
    def charge_at(self):
        return self.began_at + WARNING_SECONDS

    @property
    def impact_end(self):
        return self.charge_at + CHARGE_SECONDS

    @property
    def ends_at(self):
        return self.impact_end + RECOVERY_SECONDS

    def phase(self, now: float) -> str:
        if now < self.began_at or now >= self.ends_at:
            return "done"
        if now < self.charge_at:
            return "warning"
        if now < self.impact_end:
            return "charge"
        return "recovery"

    def position(self, now: float) -> Point:
        # Return exact grid endpoints, not 8.999999999999936 from rounding.
        if now <= self.charge_at:
            return self.start
        if now >= self.impact_end:
            return self.destination
        p = (now - self.charge_at) / CHARGE_SECONDS
        return (self.start[0] + (self.destination[0] - self.start[0]) * p,
                self.start[1] + (self.destination[1] - self.start[1]) * p)

    @property
    def direction(self) -> Cell:
        return (0 if self.destination[0] == self.start[0]
                else 1 if self.destination[0] > self.start[0] else -1,
                0 if self.destination[1] == self.start[1]
                else 1 if self.destination[1] > self.start[1] else -1)


class MedusaCharge:
    def __init__(self):
        self.reset()

    def reset(self):
        self.action: ChargeAction | None = None
        self.next_ready_at = float("-inf")

    def waiting(self, now: float) -> bool:
        return self.action is not None and self.action.phase(now) != "done"

    def ready(self, now: float) -> bool:
        return self.action is None and now >= self.next_ready_at

    def begin(self, start: Cell, size: int, observed_target: Cell,
              walls, grid: Cell, bodies, now: float) -> ChargeAction | None:
        if not self.ready(now):
            return None
        destination = choose_charge(
            start, size, observed_target, walls, grid, bodies,
        )
        if destination is None:
            return None
        self.action = ChargeAction(start, destination, observed_target, now)
        self.next_ready_at = now + COOLDOWN_SECONDS
        return self.action

    def tick(self, now: float) -> tuple[Point, Point, bool, bool, bool] | None:
        """Return swept interval and one-shot phase transitions.

        Even if the update jumps across the entire short charge motion,
        its full sweep is returned once, including its endpoint.
        """
        a = self.action
        if a is None:
            return None
        began = not a.started and now >= a.charge_at
        if began:
            a.started = True
        before = a.last_position
        after = a.position(now) if a.started else a.start
        a.last_position = after
        finished_motion = a.started and not a.finished_motion and now >= a.impact_end
        if finished_motion:
            a.finished_motion = True
        done = now >= a.ends_at
        return before, after, began, finished_motion, done

    def finish(self):
        self.action = None

    def cancel(self, now: float):
        """Abort the dash; don't rewind cooldown or leave a ghost action."""
        previous = self.action
        self.action = None
        if previous is not None:
            self.next_ready_at = max(self.next_ready_at, now + 2.0)
        return previous
