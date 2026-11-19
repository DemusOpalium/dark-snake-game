"""Boss Phases A — clear HP-gated, non-random combat transitions.

Boss identity and artwork remain unchanged. Only the optional KI-Test
enables phase-based tuning. This pure module deliberately creates no shots,
zones, extra damage, invulnerability, teleports or global class mutations.
"""
from __future__ import annotations

from dataclasses import dataclass


PHASE_2_HP = 0.70
PHASE_3_HP = 0.35
WARNING_SECONDS = 1.2
RECOVERY_SECONDS = 0.65


@dataclass(frozen=True)
class PhaseTuning:
    """Multipliers of a boss's fixed personality baseline.

    All intervals have a floor in Boss.apply_phase_tuning. Lower factors
    increase frequency a little but never change collision or damage.
    """
    move: float = 1.0
    projectile: float = 1.0
    aoe: float = 1.0
    frost: float = 1.0
    shield: float = 1.0
    swipe: float = 1.0
    eye: float = 1.0


# Explicit profile identities, not weighted random changes.
# Stage I = personality baseline; II = pressure; III = controlled climax.
PHASE_TUNINGS = {
    "hunter": (
        PhaseTuning(),
        PhaseTuning(move=.94, projectile=.90, swipe=.93),
        PhaseTuning(move=.86, projectile=.82, swipe=.85),
    ),
    "guardian": (
        PhaseTuning(),
        PhaseTuning(move=.97, aoe=.92, shield=.90),
        PhaseTuning(move=.93, projectile=.90, aoe=.84, shield=.80),
    ),
    "medusa": (
        PhaseTuning(),
        PhaseTuning(move=.95, frost=.92, eye=.92),
        PhaseTuning(move=.90, projectile=.94, frost=.84,
                    shield=.93, swipe=.90, eye=.85),
    ),
}

# Small, recognizable labels in the same fixed art identity.
PHASE_NAMES = {
    "hunter": ("Jagd", "Hetzjagd", "Endspurt"),
    "guardian": ("Wache", "Bollwerk", "Letzte Bastion"),
    "medusa": ("Blick", "Frostnetz", "Frostorkan"),
}

PHASE_COLORS = {
    "hunter": (252, 153, 106),
    "guardian": (116, 207, 252),
    "medusa": (202, 150, 255),
}


def hp_stage(health, max_health):
    """Exact threshold calculation independent of current level/HP scaling."""
    if max_health <= 0 or health <= 0:
        return 1 if max_health <= 0 else 3
    ratio = health / max_health
    if ratio <= PHASE_3_HP:
        return 3
    if ratio <= PHASE_2_HP:
        return 2
    return 1


class BossPhases:
    """One-time ordered transitions, with a readable warning and recovery.

    A large hit crossing *both* thresholds cannot silently skip phase II.
    Warning stops newly initiated attacks until completion. A transition is
    never triggered merely by the number of frames spent below a threshold.
    """

    def __init__(self, profile_key: str, max_health: int):
        if profile_key not in PHASE_TUNINGS:
            raise ValueError(f"Unknown boss personality: {profile_key}")
        self.profile_key = profile_key
        self.max_health = max_health
        self.reset()

    def reset(self):
        self.stage = 1
        self.target_stage = 1
        self.pending_stage = None
        self.warning_started_at = None
        self.warning_ends_at = None

    def cancel_warning(self):
        """Pause/editor/respawn: replay the warning on resume, not instant rage."""
        self.pending_stage = None
        self.warning_started_at = None
        self.warning_ends_at = None

    def warning_active(self, now):
        return self.pending_stage is not None and now < self.warning_ends_at

    def observe_health(self, health, now):
        """Return the next announced stage, or None if no new warning."""
        if health <= 0:
            return None  # death wins; no phase from a dead boss
        self.target_stage = max(self.target_stage, hp_stage(health, self.max_health))
        if self.pending_stage is not None or self.stage >= self.target_stage:
            return None
        self.pending_stage = self.stage + 1
        self.warning_started_at = now
        self.warning_ends_at = now + WARNING_SECONDS
        return self.pending_stage

    def advance(self, now):
        """Finish the advertised stage once and leave further stages queued."""
        if self.pending_stage is None or now < self.warning_ends_at:
            return None
        applied = self.pending_stage
        self.stage = applied
        self.cancel_warning()
        return applied

    def tuning(self):
        return PHASE_TUNINGS[self.profile_key][self.stage - 1]

    def stage_name(self, stage=None):
        return PHASE_NAMES[self.profile_key][(stage or self.stage) - 1]
