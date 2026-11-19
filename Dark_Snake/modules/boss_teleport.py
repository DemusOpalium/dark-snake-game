"""Boss Teleport A: deterministic safe relocation and reusable transition states.

All calculations are in grid cells. This module never moves a snake, changes
damage, reads unobserved player locations as tactical targets, or creates
projectiles. The game's AI-Test gate is the only way to enable it.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot

# A generous, readable destination warning, then a visual sink/emerge.
WARNING_SECONDS = 1.10
SINK_SECONDS = .38
EMERGE_SECONDS = .35
RECOVERY_SECONDS = .65
REUSE_COOLDOWN_SECONDS = 10.0
ABORT_RETRY_SECONDS = 3.0
MIN_JUMP_CELLS = 5.0
MIN_PLAYER_CLEARANCE_CELLS = 3.0

# Fixed personality -> fixed presentation/positioning, no random art roulette.
TELEPORT_STYLES = {
    "hunter": ("leap", 4.8),
    "guardian": ("tunnel", 8.0),
    "medusa": ("portal", 6.5),
}


@dataclass(frozen=True)
class TeleportAction:
    origin: tuple[int, int]
    destination: tuple[int, int]
    began_at: float
    stage: int
    style: str

    def phase(self, now: float) -> str:
        elapsed = now - self.began_at
        # Seconds are floating-point: e.g. (100 + 1.1) - 100 may be
        # 1.099999999999994. A tiny tolerance gives exact stage boundaries
        # without an accidental extra 'warning' frame.
        epsilon = 1e-9
        if elapsed + epsilon < WARNING_SECONDS:
            return "warning"
        if elapsed + epsilon < WARNING_SECONDS + SINK_SECONDS:
            return "sink"
        if elapsed + epsilon < WARNING_SECONDS + SINK_SECONDS + EMERGE_SECONDS:
            return "emerge"
        if elapsed + epsilon < WARNING_SECONDS + SINK_SECONDS + EMERGE_SECONDS + RECOVERY_SECONDS:
            return "recovery"
        return "done"

    def progress(self, now: float) -> float:
        phase = self.phase(now)
        if phase == "sink":
            return max(0.0, min(1.0, (now - self.began_at - WARNING_SECONDS) / SINK_SECONDS))
        if phase == "emerge":
            return max(0.0, min(
                1.0, (now - self.began_at - WARNING_SECONDS - SINK_SECONDS)
                / EMERGE_SECONDS,
            ))
        return 1.0

    @property
    def landing_time(self) -> float:
        return self.began_at + WARNING_SECONDS + SINK_SECONDS


def destination_is_safe(cell, size, grid_size, blocked_cells, player_heads):
    """Check the entire boss footprint and a 3-cell gap to *both* heads."""
    x, y = cell
    width, height = grid_size
    if x < 0 or y < 0 or x + size > width or y + size > height:
        return False
    if any((i, j) in blocked_cells
           for i in range(x, x + size) for j in range(y, y + size)):
        return False
    for hx, hy in player_heads:
        # Nearest point on the full boss footprint, not just its centre.
        gap_x = max(x - hx, 0, hx - (x + size - 1))
        gap_y = max(y - hy, 0, hy - (y + size - 1))
        if hypot(gap_x, gap_y) < MIN_PLAYER_CLEARANCE_CELLS:
            return False
    return True


def choose_destination(origin, size, grid_size, blocked_cells, player_heads,
                       observed_target, profile_key):
    """Find a deterministic *free* landing cell near the observed target.

    The target must come from the boss sensor (VISIBLE/RELAY/SEARCHING),
    never from real unobserved player coordinates. Real bodies/heads may be
    consulted only as a collision *safety* mask.
    """
    if observed_target is None:
        return None
    preferred = TELEPORT_STYLES[profile_key][1]
    candidates = []
    for y in range(grid_size[1] - size + 1):
        for x in range(grid_size[0] - size + 1):
            if hypot(x - origin[0], y - origin[1]) < MIN_JUMP_CELLS:
                continue
            cell = (x, y)
            if not destination_is_safe(
                    cell, size, grid_size, blocked_cells, player_heads):
                continue
            dist = hypot(x + size / 2 - observed_target[0],
                         y + size / 2 - observed_target[1])
            # Favour meaningful movement and personality-specific ranges.
            score = (abs(dist - preferred),
                     -min(hypot(x - origin[0], y - origin[1]), 12.),
                     y, x)
            candidates.append((score, cell))
    return min(candidates)[1] if candidates else None


class BossTeleport:
    """At most one relocation per HP phase; two visits per boss fight."""

    def __init__(self, profile_key: str):
        self.style = TELEPORT_STYLES[profile_key][0]
        self.reset()

    def reset(self):
        self.action: TeleportAction | None = None
        self.landed = False
        self.used_stages: set[int] = set()
        self.next_ready_at = float("-inf")

    def ready(self, stage: int, now: float) -> bool:
        return (stage in (2, 3) and stage not in self.used_stages
                and self.action is None and now >= self.next_ready_at)

    def begin(self, origin, destination, stage: int, now: float):
        if not self.ready(stage, now):
            return False
        self.action = TeleportAction(
            tuple(origin), tuple(destination), now, stage, self.style,
        )
        self.landed = False
        return True

    def waiting(self, now: float) -> bool:
        return self.action is not None and self.action.phase(now) != "done"

    def hidden(self, now: float) -> bool:
        return self.action is not None and self.action.phase(now) in ("sink", "emerge")

    def needs_landing(self, now: float) -> bool:
        return (self.action is not None and not self.landed
                and now >= self.action.landing_time)

    def arrive(self, now: float) -> None:
        assert self.action is not None and not self.landed
        self.landed = True
        self.used_stages.add(self.action.stage)
        self.next_ready_at = now + REUSE_COOLDOWN_SECONDS

    def cancel(self, now: float) -> None:
        if self.action is not None and not self.landed:
            self.next_ready_at = max(self.next_ready_at, now + ABORT_RETRY_SECONDS)
        self.action = None
        self.landed = False

    def finish(self, now: float) -> bool:
        if self.action is not None and self.action.phase(now) == "done":
            self.action = None
            self.landed = False
            return True
        return False
