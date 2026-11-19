"""Medusa Tactics B: a bounded, telegraphed Frost throw.

The boss throws at a cell *already observed* by Medusa Eyes, not at
unobserved player movement. This module models timing/hits only: no pygame,
no rendering, no damage mutation, and no World Studio integration.

It does NOT use the legacy DamageZone.apply_effect(), which can apply damage
per frame. Each volley hits each player at most once during the impact window.
"""
from __future__ import annotations

from dataclasses import dataclass, field

Cell = tuple[int, int]


@dataclass
class FrostVolley:
    origin: tuple[float, float]   # boss center in grid units at throw time
    target: Cell                  # fixed target in grid units
    started_at: float
    impact_at: float
    expires_at: float
    hit_players: set[str] = field(default_factory=set)

    def phase(self, now: float) -> str:
        if now < self.started_at or now >= self.expires_at:
            return "done"
        return "warning" if now < self.impact_at else "impact"


class MedusaTactics:
    """One visible warning, then one short AoE impact; bounded cast frequency."""

    WARNING_SECONDS = 1.35
    IMPACT_SECONDS = 0.65
    COOLDOWN_SECONDS = 6.0
    RADIUS_CELLS = 1.25
    DAMAGE = 10

    def __init__(self):
        self.volley: FrostVolley | None = None
        self.next_cast_at = float("-inf")

    def reset(self):
        self.volley = None
        self.next_cast_at = float("-inf")

    def cancel(self, now: float | None = None):
        """Discard a pending danger when gameplay becomes suspended."""
        self.volley = None
        if now is not None:
            self.next_cast_at = max(self.next_cast_at, now + self.WARNING_SECONDS)

    def cast(self, reading, now: float, origin: tuple[float, float],
             blockers, grid_size: Cell) -> FrostVolley | None:
        """Throw only at actually VISIBLE/RELAY-observed, valid clear cells.

        A SEARCHING last-known position is useful for navigation, but cannot
        grant a boss fresh attack knowledge through a wall.
        """
        if self.volley is not None and self.volley.phase(now) != "done":
            return None
        if now < self.next_cast_at or reading.kind not in ("VISIBLE", "RELAY"):
            return None
        cell = reading.predicted_cell
        if cell is None:
            return None
        x, y = cell
        if not (0 <= x < grid_size[0] and 0 <= y < grid_size[1]):
            return None
        if cell in blockers:
            return None
        self.volley = FrostVolley(
            origin=origin, target=cell, started_at=now,
            impact_at=now + self.WARNING_SECONDS,
            expires_at=now + self.WARNING_SECONDS + self.IMPACT_SECONDS,
        )
        self.next_cast_at = now + self.COOLDOWN_SECONDS
        return self.volley

    def hit_players(self, now: float, heads: list[tuple[Cell, str]]) -> tuple[str, ...]:
        """Return newly impacted players exactly once; caller applies damage."""
        volley = self.volley
        if volley is None or volley.phase(now) != "impact":
            if volley is not None and volley.phase(now) == "done":
                self.volley = None
            return ()
        r2 = self.RADIUS_CELLS ** 2
        hits = []
        for (x, y), player_key in heads:
            if player_key in volley.hit_players:
                continue
            if (x - volley.target[0]) ** 2 + (y - volley.target[1]) ** 2 <= r2:
                volley.hit_players.add(player_key)
                hits.append(player_key)
        return tuple(hits)
