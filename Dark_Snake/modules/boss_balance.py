"""DARK SNAKE — deterministic boss HP and Auto-Shoot combat budget.

The goal is enough room for the three HP phases to play out even when a
player picks up the automatic weapon. Time budgets are *reference estimates*:
misses, fireballs, shields, swipes, two players and other items all matter.
No change to actual projectile movement, collision, or tick scheduling.
"""

from __future__ import annotations

from math import ceil

# These values are balanced against the actual user setting of 2s between
# auto-shot volleys. With one pellet for 2 HP, a level 1 boss needs 32 hits
# (64s on perfect continuous hit rate), and a level 3 guardian needs 42
# (84s). Fireballs and specials shorten these baseline estimates.
BASE_BOSS_HP = 64
BOSS_HP_PER_LEVEL = 6
GUARDIAN_EXTRA_HP = 8


def boss_max_health(level: int, health_multiplier=1.0, *, guardian=False) -> int:
    """Fixed difficulty by level/profile, scaled by existing game setting."""
    level = max(1, int(level))
    base = BASE_BOSS_HP + BOSS_HP_PER_LEVEL * (level - 1)
    if guardian:
        base += GUARDIAN_EXTRA_HP
    return max(1, int(base * max(0.01, health_multiplier)))


def hits_to_defeat(hp: int, damage: int) -> int:
    """Nominal required shots, if *every* projectile is a valid hit."""
    return ceil(hp / damage) if hp > 0 and damage > 0 else 0


def estimated_auto_shoot_seconds(hp: int, damage: int, interval: float,
                                 player_heads=1) -> float:
    """Full-accuracy baseline, NOT a predicted real battle duration."""
    shots_per_wave = max(1, int(player_heads))
    waves = ceil(hits_to_defeat(hp, damage) / shots_per_wave)
    return waves * max(0.0, float(interval))
