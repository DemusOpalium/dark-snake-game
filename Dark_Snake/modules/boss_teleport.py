"""Boss Teleport A: deterministic safe relocation and reusable transition states.

All calculations are in grid cells. This module never moves a snake,
changes damage or creates projectiles. Normal tactical targeting remains bound
to Medusa Eyes. The explicit Guardian Phase III world scan is the *only*
exception: it can acquire a live head anywhere after a visible 1.45 s pulse,
and only for a separately telegraphed, collision-safe tunnel relocation.
The game's AI-Test gate is the only way to enable it.
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
# Guardian's Phase III *magical* map scan is a deliberately special
# mechanic. It does not alter the normal boss/Medusa Eyes visibility.
WORLD_SCAN_SECONDS = 1.45
ABORT_VISUAL_SECONDS = .55
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


def world_scan_target(origin, size, player_heads):
    """Choose one currently living head anywhere on the board (1P/2P).

    Only a visible Phase III guardian scan may call this. A late snapshot,
    rather than tracking through every obstacle on every frame, avoids
    global omniscient targeting for the other bosses or attacks.
    """
    if not player_heads:
        return None
    cx, cy = origin[0] + size / 2, origin[1] + size / 2
    return min(tuple(player_heads), key=lambda h: (
        hypot(h[0] - cx, h[1] - cy), h[1], h[0],
    ))


def choose_destination(origin, size, grid_size, blocked_cells, player_heads,
                       observed_target, profile_key):
    """Find a deterministic *free* landing cell near the observed target.

    The target normally comes from boss sensors (VISIBLE/RELAY/SEARCHING).
    Only a finished guardian Phase III world scan can supply a globally
    detected player head. Bodies/heads also act as a collision *safety* mask.
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
        self.search_started_at: float | None = None
        self.abort_visual: tuple[TeleportAction, float] | None = None
        self.landed = False
        self.used_stages: set[int] = set()
        self.next_ready_at = float("-inf")

    def ready(self, stage: int, now: float) -> bool:
        return (stage in (2, 3) and stage not in self.used_stages
                and self.action is None and self.search_started_at is None
                and now >= self.next_ready_at)

    def begin_search(self, stage: int, now: float) -> bool:
        """A single full-board pulse exclusive to guardian, HP Phase III."""
        if self.style != "tunnel" or stage != 3 or not self.ready(stage, now):
            return False
        self.search_started_at = now
        self.abort_visual = None
        return True

    def scanning(self) -> bool:
        return self.search_started_at is not None

    def scan_complete(self, now: float) -> bool:
        return (self.scanning()
                and now + 1e-9 >= self.search_started_at + WORLD_SCAN_SECONDS)

    def end_search(self) -> None:
        self.search_started_at = None

    def begin(self, origin, destination, stage: int, now: float):
        if not self.ready(stage, now):
            return False
        self.action = TeleportAction(
            tuple(origin), tuple(destination), now, stage, self.style,
        )
        self.abort_visual = None
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

    def cancel(self, now: float, *, show_abort=False) -> None:
        if show_abort and self.action is not None and not self.landed:
            # The collapsing rift remains visible for a few frames instead
            # of snapping away. It is purely decorative, with no hitbox.
            self.abort_visual = (self.action, now)
        else:
            self.abort_visual = None
        if self.action is not None and not self.landed:
            self.next_ready_at = max(self.next_ready_at, now + ABORT_RETRY_SECONDS)
        if self.search_started_at is not None:
            self.next_ready_at = max(self.next_ready_at, now + ABORT_RETRY_SECONDS)
        self.action = None
        self.search_started_at = None
        self.landed = False

    def finish(self, now: float) -> bool:
        if self.action is not None and self.action.phase(now) == "done":
            self.action = None
            self.landed = False
            return True
        return False
