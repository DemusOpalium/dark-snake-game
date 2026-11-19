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
    """Return two-cell *perpendicular* dodge, or None when no safe lane exists.

    Both intermediate footprints must be free and never pass through a
    current player head. If a projectile may still reach the final footprint,
    the shield remains the fallback. Never dodge along the incoming ray.
    """
    vx, vy = threat.velocity
    shots = tuple(shots) or (threat,)
    if vx == 0 and vy == 0:
        return None
    if abs(vx) >= abs(vy):
        directions = ((0, 1), (0, -1))
    else:
        directions = ((1, 0), (-1, 0))

    eligible = []
    for dx, dy in directions:
        mid = (position[0] + dx, position[1] + dy)
        dst = (position[0] + 2 * dx, position[1] + 2 * dy)
        if not (legal_boss_step(position, (dx, dy), size, blockers, grid_size)
                and legal_boss_step(mid, (dx, dy), size, blockers, grid_size)):
            continue
        # A visible side step must not run over any player head.
        if any(x <= head[0] < x + size and y <= head[1] < y + size
               for x, y in (mid, dst) for head in player_heads):
            continue
        # Check destination against each projectile's near-future path.
        # A single blocked/misaligned alternative is not a random teleport.
        if any(_shot_hits_footprint(shot, dst, size, t=t)
               for shot in shots
               for t in range(0, 11)):
            continue
        # During the 0.18 s swipe, shots can travel about two grid updates.
        # Sample intermediate positions to avoid swiping *into* a fast shot.
        if any(_shot_hits_footprint(
                    shot,
                    (position[0] + 2 * dx * fraction,
                     position[1] + 2 * dy * fraction),
                    size, t=2 * fraction,
                ) for shot in shots for fraction in (.25, .5, .75, 1.0)):
            continue
        # Prefer the lane furthest from the threatening projectile track.
        # Equal scores intentionally vary to keep the movement organic.
        score = min(
            hypot(dst[0] + size / 2 - (shot.position[0] + t * shot.velocity[0]),
                  dst[1] + size / 2 - (shot.position[1] + t * shot.velocity[1]))
            for shot in shots for t in (2, 4, 6, 8, 10)
        )
        eligible.append((score, dst))
    if not eligible:
        return None
    best = max(score for score, _ in eligible)
    candidates = [dest for score, dest in eligible if abs(score - best) < 1e-8]
    return (rng or random.choice)(candidates)


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

    def reset(self):
        self.__init__()

    def cancel(self):
        self.action = None
        self.candidate_id = None
        self.first_seen_at = None

    def active(self, now):
        return self.action is not None and self.action.active(now)

    def charges(self, now):
        return sum(now >= ready for ready in self.ready_at)

    def observe(self, position, start_visual, size, threats, shots,
                blockers, grid_size, player_heads, now):
        """Start a swipe only after two continuously-visible observations."""
        if self.active(now):
            return None
        if not threats or self.charges(now) == 0:
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
            return None
        if self.first_seen_at is None or now - self.first_seen_at < self.REACTION_SECONDS:
            return None
        target = choose_swipe(
            position, size, threat, shots, blockers, grid_size, player_heads,
        )
        if target is None:
            # Blocked or dangerous => let the existing shield handle the shot.
            return None
        slot = next(i for i, ready in enumerate(self.ready_at) if now >= ready)
        self.ready_at[slot] = now + self.RECHARGE_SECONDS
        self.candidate_id = None
        self.first_seen_at = None
        self.action = SwipeAction(tuple(start_visual), target, now,
                                  self.SWIPE_SECONDS)
        return self.action
