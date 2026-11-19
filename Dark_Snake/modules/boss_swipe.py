"""Medusa Swipe D: two charged, non-teleporting lateral projectile dodges.

Pure, bounded geometry; only a *real visible projectile* can prime a swipe.
The existing collision grid stays authoritative except during the short swipe,
when the boss rectangle follows its visual interpolation frame-for-frame.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot
import random

from modules.boss_medusa import legal_boss_step


@dataclass(frozen=True)
class SwipeAction:
    start: tuple[float, float]
    destination: tuple[int, int]
    began_at: float
    duration: float = .18

    def active(self, now: float) -> bool:
        return self.began_at <= now < self.began_at + self.duration

    def position(self, now: float) -> tuple[float, float]:
        progress = min(1.0, max(0.0, (now - self.began_at) / self.duration))
        # No teleport/snap: ease through the intermediate cells smoothly.
        progress = progress * progress * (3 - 2 * progress)
        return (self.start[0] + (self.destination[0] - self.start[0]) * progress,
                self.start[1] + (self.destination[1] - self.start[1]) * progress)


def _shot_hits_footprint(shot, top_left, size, *, t):
    """Predict collision with a full boss footprint (plus projectile thickness).

    Shots are already filtered by real Vision LOS in MedusaDefense.
    This is only geometry over a bounded forward trajectory, not new sight.
    """
    sx = shot.position[0] + t * shot.velocity[0]
    sy = shot.position[1] + t * shot.velocity[1]
    # Existing grid shots use a one-cell hitbox. The wider player fireball
    # swept rect is handled by the *actual* collision check in Game.
    half_projectile = shot.radius_cells
    x, y = top_left
    return (x - half_projectile < sx < x + size + half_projectile
            and y - half_projectile < sy < y + size + half_projectile)


def choose_swipe(position, size, threat, shots, blockers, grid_size,
                 player_heads=(), *, rng=None):
    """Dodge *perpendicular* to the observed ray; never through solid cells.

    Two tiles for normal bosses. A four-tile-wide boss may require a third
    tile to clear the projectile's full width; use it only if two are unsafe.
    Predict the whole move and end lane, or fall back to the existing shield.
    """
    vx, vy = threat.velocity
    shots = tuple(shots) or (threat,)
    if vx == 0 and vy == 0:
        return None
    directions = (((0, 1), (0, -1)) if abs(vx) >= abs(vy)
                  else ((1, 0), (-1, 0)))

    for stride in ((2, 3) if size >= 4 else (2,)):
        eligible = []
        for dx, dy in directions:
            path = [(position[0] + i * dx, position[1] + i * dy)
                    for i in range(1, stride + 1)]
            current = position
            if any(not legal_boss_step(
                    previous, (dx, dy), size, blockers, grid_size)
                   for previous in [current, *path[:-1]]):
                continue
            # A visible side step must never run over either player head.
            if any(x <= head[0] < x + size and y <= head[1] < y + size
                   for x, y in path for head in player_heads):
                continue
            dst = path[-1]
            if any(_shot_hits_footprint(shot, dst, size, t=t)
                   for shot in shots for t in range(0, 11)):
                continue
            # During the 0.18 s swipe, projectiles travel ~2 grid ticks.
            # Sample intermediate boss rectangles; no invulnerable teleport.
            if any(_shot_hits_footprint(
                    shot,
                    (position[0] + stride * dx * fraction,
                     position[1] + stride * dy * fraction),
                    size, t=2 * fraction,
                ) for shot in shots for fraction in (.25, .5, .75, 1.0)):
                continue
            score = min(
                hypot(dst[0] + size / 2 - (shot.position[0] + t * shot.velocity[0]),
                      dst[1] + size / 2 - (shot.position[1] + t * shot.velocity[1]))
                for shot in shots for t in (2, 4, 6, 8, 10)
            )
            eligible.append((score, dst))
        if eligible:
            best = max(score for score, _ in eligible)
            candidates = [dest for score, dest in eligible if abs(score - best) < 1e-8]
            return (rng or random.choice)(candidates)
    return None

class MedusaSwipe:
    """Two independent charges, each restoring after 12 seconds."""

    REACTION_SECONDS = .06
    SWIPE_SECONDS = .18
    RECHARGE_SECONDS = 12.
    MAX_CHARGES = 2

    def __init__(self):
        self.ready_at = [float("-inf")] * self.MAX_CHARGES
        self.action: SwipeAction | None = None
        self.candidate_id: int | None = None
        self.first_seen_at: float | None = None
        # Diagnostic only: never changes AI decisions.
        self.last_reason = "IDLE"

    def reset(self):
        self.__init__()

    def cancel(self):
        self.action = None
        self.candidate_id = None
        self.first_seen_at = None
        self.last_reason = "CANCELLED"

    def active(self, now):
        return self.action is not None and self.action.active(now)

    def charges(self, now):
        return sum(now >= ready for ready in self.ready_at)

    def observe(self, position, start_visual, size, threats, shots,
                blockers, grid_size, player_heads, now):
        """Start a swipe only after two continuously-visible observations."""
        if self.active(now):
            self.last_reason = "SWIPING"
            return None
        if not threats or self.charges(now) == 0:
            self.last_reason = "NO_THREAT" if not threats else "NO_CHARGE"
            self.candidate_id = None
            self.first_seen_at = None
            return None
        center = (position[0] + size / 2, position[1] + size / 2)
        threat = min(threats, key=lambda shot: (
            hypot(shot.position[0] - center[0],
                  shot.position[1] - center[1]), shot.identity,
        ))
        if threat.identity != self.candidate_id:
            self.candidate_id = threat.identity
            self.first_seen_at = now
            self.last_reason = "ACQUIRING"
            return None
        if self.first_seen_at is None or now - self.first_seen_at < self.REACTION_SECONDS:
            self.last_reason = "REACTION"
            return None
        target = choose_swipe(
            position, size, threat, shots, blockers, grid_size, player_heads,
        )
        if target is None:
            # Blocked or dangerous => let the existing shield handle the shot.
            self.last_reason = "NO_SAFE_LANE"
            return None
        slot = next(i for i, ready in enumerate(self.ready_at) if now >= ready)
        self.ready_at[slot] = now + self.RECHARGE_SECONDS
        self.candidate_id = None
        self.first_seen_at = None
        self.action = SwipeAction(tuple(start_visual), target, now,
                                  self.SWIPE_SECONDS)
        self.last_reason = "SWIPE"
        return self.action
