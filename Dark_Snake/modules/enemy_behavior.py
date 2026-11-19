"""Small, testable reaction layer on top of Enemy Vision A.

Sight reports facts. Behaviour chooses a *movement intention*. The existing
NormalEnemy update owns movement cadence, collision and sprite interpolation.
No new damage, teleport, projectile, spawn or attack logic lives here.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import dist

from modules.enemy_vision import VisionResult

Cell = tuple[int, int]
MOVE_ACTIONS = frozenset(("CHASE", "RETREAT", "GUARD"))


@dataclass(frozen=True, slots=True)
class BehaviorProfile:
    """An opponent's response, separate from its vision/graphics/age profile."""
    visible_action: str = "CHASE"
    chase_speed: float = 1.0
    retreat_distance: float = 2.0
    search_speed: float = 1.0
    patrol_speed: float = 1.0

    def __post_init__(self):
        if self.visible_action not in MOVE_ACTIONS:
            raise ValueError("Unbekannte sichtbasierte Gegnerreaktion.")
        if not 0.5 <= self.chase_speed <= 2.0:
            raise ValueError("Ungültiger Bewegungsfaktor.")
        if self.retreat_distance < 0:
            raise ValueError("Fluchtabstand muss positiv sein.")
        if not 0.25 <= self.search_speed <= 2:
            raise ValueError("Ungültiger Suchtempo-Faktor.")
        if not 0.25 <= self.patrol_speed <= 2:
            raise ValueError("Ungültiger Patrouillentempo-Faktor.")


# Future FrostAge candidates only. These do not register or spawn opponents.
FROST_PROTOTYPE_BEHAVIORS = {
    "frostage_eisskelett": BehaviorProfile(
        "CHASE", chase_speed=1.35, search_speed=.75),
    "frostage_frostwisp": BehaviorProfile(
        "RETREAT", chase_speed=1.15, retreat_distance=2.5, patrol_speed=1.1),
    "frostage_frosttitan": BehaviorProfile("GUARD", patrol_speed=.6),
}


def reaction_state(result: VisionResult, position: Cell,
                   profile: BehaviorProfile) -> str:
    """PATROL → CHASE/GUARD/RETREAT → SEARCH → PATROL, based on *real* sight."""
    if result.kind == "VISIBLE" and result.last_known_cell is not None:
        if profile.visible_action == "RETREAT":
            if dist(position, result.last_known_cell) <= profile.retreat_distance:
                return "RETREAT"
            return "GUARD"
        return profile.visible_action
    if result.kind == "SEARCHING" and result.last_known_cell is not None:
        return "SEARCH"
    return "PATROL"


def permitted_step(position: Cell, step: Cell, blockers, grid_size: Cell) -> bool:
    dx, dy = step
    if abs(dx) > 1 or abs(dy) > 1:
        return False
    nx, ny = position[0] + dx, position[1] + dy
    if not (0 <= nx < grid_size[0] and 0 <= ny < grid_size[1]):
        return False
    if (nx, ny) in blockers:
        return False
    # No squeezing through a diagonally touching pair of wall corners.
    if dx and dy and ((position[0] + dx, position[1]) in blockers
                     or (position[0], position[1] + dy) in blockers):
        return False
    return True


STEPS = (
    (-1, 0), (0, -1), (1, 0), (0, 1),
    (-1, -1), (1, -1), (1, 1), (-1, 1),
)


def movement_intention(position: Cell, target: Cell, state: str, blockers,
                       grid_size: Cell) -> Cell:
    """Choose a safe local move; never assume the enemy can pass through a wall.

    A cheap 8-neighbour step instead of a heavyweight per-frame pathfinder.
    If the player is beyond a barrier, wait/search rather than phase through.
    """
    if state not in ("CHASE", "SEARCH", "RETREAT"):
        return (0, 0)
    current_distance = ((position[0] - target[0]) ** 2
                        + (position[1] - target[1]) ** 2)
    choices = []
    for dx, dy in STEPS:
        if not permitted_step(position, (dx, dy), blockers, grid_size):
            continue
        next_distance = ((position[0] + dx - target[0]) ** 2
                         + (position[1] + dy - target[1]) ** 2)
        # A target reached is not a reason to jitter away from it.
        improvement = (current_distance - next_distance
                       if state != "RETREAT" else next_distance - current_distance)
        if improvement > 0:
            # deterministic tie-break avoids random zig-zag animations
            choices.append((-improvement, abs(dx) + abs(dy), STEPS.index((dx, dy)),
                            (dx, dy)))
    if not choices:
        return (0, 0)
    return min(choices)[-1]
