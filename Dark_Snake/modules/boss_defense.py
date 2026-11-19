"""Medusa Defense C: deliberately limited projectile awareness and one-hit shield.

Does not move the boss, alter collision geometry or read hidden projectiles.
The existing KI-Test is the only runtime opt-in; Classic remains untouched.
Pure Python, independent of Pygame, so perception and cooldowns can be tested.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from modules.enemy_vision import VisionProfile, can_see

_SHIELD_SIGHT = VisionProfile(
    radius_cells=8, fov_degrees=220, memory_seconds=0,
    scan_interval=0.05,
)


@dataclass(frozen=True)
class IncomingShot:
    """Observed player projectile in grid units (not pixels)."""
    identity: int
    position: tuple[float, float]
    velocity: tuple[float, float]


class MedusaDefense:
    """React to a *continuously seen* approaching shot, not every damage event.

    One clearly visible, short shield blocks exactly one projectile hit.
    Activation takes time, sight is blocked by authored walls, and cooldown
    prevents permanent invulnerability.
    """

    REACTION_SECONDS = 0.06
    SHIELD_SECONDS = 0.8
    COOLDOWN_SECONDS = 7.0
    MAX_FRAMES_AHEAD = 10

    def __init__(self):
        self.candidate_id: int | None = None
        self.first_seen_at: float | None = None
        self.shield_until = float("-inf")
        self.next_ready_at = float("-inf")

    def reset(self):
        self.__init__()

    def cancel(self):
        """Pausing/respawning must not carry a live defensive shield."""
        self.candidate_id = None
        self.first_seen_at = None
        self.shield_until = float("-inf")

    def active(self, now):
        return now < self.shield_until

    def consume(self, now):
        if not self.active(now):
            return False
        self.shield_until = float("-inf")
        return True

    @staticmethod
    def _is_approaching(shot: IncomingShot, boss_center, boss_size):
        px, py = shot.position
        vx, vy = shot.velocity
        speed_sq = vx * vx + vy * vy
        if speed_sq <= 1e-10:
            return False
        off_x = boss_center[0] - px
        off_y = boss_center[1] - py
        ahead = (off_x * vx + off_y * vy) / speed_sq
        if not 0 <= ahead <= MedusaDefense.MAX_FRAMES_AHEAD:
            return False
        closest_x = px + ahead * vx
        closest_y = py + ahead * vy
        # The boss occupies a full footprint, not merely its center tile.
        half = boss_size / 2 + 0.6
        return (abs(closest_x - boss_center[0]) <= half
                and abs(closest_y - boss_center[1]) <= half)

    def visible_threats(self, boss_center, facing, boss_size, shots, blockers):
        """Real, unoccluded threats shared by the shield and lateral swipe."""
        threats = []
        for shot in shots:
            px, py = shot.position
            cell = (round(px), round(py))
            # No 360° omniscience: real view cone and line of sight required.
            if not can_see((round(boss_center[0]), round(boss_center[1])),
                           facing, cell, _SHIELD_SIGHT, blockers):
                continue
            if self._is_approaching(shot, boss_center, boss_size):
                threats.append(shot)
        return threats

    def observe(self, boss_center, facing, boss_size, shots,
                blockers, now):
        """Report whether a shield was *newly* activated on this frame."""
        if now < self.next_ready_at or self.active(now):
            return False
        threats = self.visible_threats(
            boss_center, facing, boss_size, shots, blockers,
        )
        if not threats:
            self.candidate_id = None
            self.first_seen_at = None
            return False
        shot = min(threats, key=lambda s: (
            hypot(s.position[0] - boss_center[0],
                  s.position[1] - boss_center[1]), s.identity,
        ))
        if self.candidate_id != shot.identity:
            self.candidate_id = shot.identity
            self.first_seen_at = now
            return False
        if self.first_seen_at is None or now - self.first_seen_at < self.REACTION_SECONDS:
            return False
        self.candidate_id = None
        self.first_seen_at = None
        self.shield_until = now + self.SHIELD_SECONDS
        self.next_ready_at = now + self.COOLDOWN_SECONDS
        return True
