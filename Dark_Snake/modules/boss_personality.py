"""Boss Personality A: immutable archetype -> fixed art and combat identity.

Real game spawns follow a predictable level rotation. There is no random
image/behavior lottery: the same archetype ALWAYS has the same image,
sensor limits, movement preference and special ability selection.
Only the existing optional KI-Test activates new tactical decision rules.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.boss_medusa import legal_boss_step


@dataclass(frozen=True)
class BossProfile:
    key: str
    name: str
    sprite: str
    frame_folder: str | None
    frame_count: int
    larger_boss: bool
    movement_interval: float
    aoe_interval: float
    projectile_interval: float
    remote_eye_limit: int
    heavy_vision: bool
    frost_throw: bool
    shield: bool
    swipe: bool
    movement_style: str


PROFILES = {
    "hunter": BossProfile(
        "hunter", "Jäger", "Boss-AlexG60.png", None, 0,
        False, .32, 7.0, 2.3, 0, False, False, False, True, "hunt",
    ),
    "guardian": BossProfile(
        "guardian", "Wächter", "Boss-SkullPurPurG60.png", None, 0,
        True, .48, 3.8, 5.0, 0, True, False, True, False, "guard",
    ),
    "medusa": BossProfile(
        "medusa", "Medusa", "Boss-RingG60.png", "Boss002", 15,
        False, .46, 5.0, 3.0, 2, True, True, True, True, "tactical",
    ),
}

# The opening fight remains Medusa, preserving existing prototype tests.
# Repeated fights at the same level retain the same visual/abilities.
LEVEL_ROTATION = ("medusa", "hunter", "guardian")


def profile_for_level(level: int) -> BossProfile:
    return PROFILES[LEVEL_ROTATION[(max(1, level) - 1) % len(LEVEL_ROTATION)]]


def profile_by_key(key: str) -> BossProfile:
    return PROFILES[key]


def guardian_step(position, size, target, blockers, grid_size,
                  *, preferred_distance=5.0):
    """Hold a ring around the last *observed* target; no omniscient pursuit.

    Full footprint, authored walls and diagonal corner cutting are enforced
    as for Medusa's existing approach movement. Near the target retreat,
    far away approach, in the comfortable distance band stand ground.
    """
    if target is None:
        return None
    cx = position[0] + size / 2
    cy = position[1] + size / 2
    current_sq = (cx - target[0]) ** 2 + (cy - target[1]) ** 2
    if (preferred_distance - 1.0) ** 2 <= current_sq <= (preferred_distance + 1.0) ** 2:
        return (0, 0)

    retreat = current_sq < (preferred_distance - 1.0) ** 2
    options = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                   (1, 1), (1, -1), (-1, 1), (-1, -1)):
        if not legal_boss_step(position, (dx, dy), size, blockers, grid_size):
            continue
        if dx and dy and not (
            legal_boss_step(position, (dx, 0), size, blockers, grid_size)
            and legal_boss_step(position, (0, dy), size, blockers, grid_size)
        ):
            continue
        nx, ny = cx + dx, cy + dy
        dist_sq = (nx - target[0]) ** 2 + (ny - target[1]) ** 2
        if retreat and dist_sq <= current_sq:
            continue
        if not retreat and dist_sq >= current_sq:
            continue
        # Prefer cardinal movement over diagonal if improvements are equal.
        options.append((dist_sq if retreat else -dist_sq,
                        -(abs(dx) + abs(dy)), dx, dy))
    if not options:
        return (0, 0)
    winner = max(options)
    return winner[2], winner[3]
