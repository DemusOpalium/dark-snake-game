"""Irians Auge D: read-only vital state observations for Classic 1P/2P.

HP and remaining lives are separate quantities. A source is recorded only
when the caller knows it. Unknown transitions are explicitly unattributed.
No mutation of gameplay state, damage, healing, lives, or progression.
"""
from __future__ import annotations

from copy import deepcopy


def _hp(value):
    if value is None:
        return None
    return round(float(value), 3)


def snapshot(game):
    """Read authoritative Classic health, shared lives and boss state."""
    count = getattr(game, "player_count", 1)
    players = ({"1": {"hp": _hp(getattr(game, "player_health", None)), "max_hp": 100}}
               if count == 1 else {
                   "1": {"hp": _hp(getattr(game, "player_health_p1", None)), "max_hp": 100},
                   "2": {"hp": _hp(getattr(game, "player_health_p2", None)), "max_hp": 100},
               })
    boss = getattr(game, "boss", None)
    return {
        "players": players,
        "lives_remaining": int(getattr(game, "lives", 0)),
        "lives_initial": 3,
        "level": int(getattr(game, "level", 1)),
        "speed_cells_s": round(float(getattr(game, "speed", 0)), 3),
        "boss": ({"key": getattr(boss, "profile_key", "classic"),
                  "hp": _hp(getattr(boss, "health", None)),
                  "max_hp": _hp(getattr(boss, "max_health", None))}
                 if boss is not None else None),
    }


class VitalObserver:
    def __init__(self):
        self.previous = None

    def reset(self):
        self.previous = None

    def observe(self, game, recorder, *, source="unattributed", checkpoint=False):
        """Log exact before/after deltas once, or a deliberate boundary snapshot."""
        if not recorder.active:
            return False
        current = snapshot(game)
        before = self.previous
        self.previous = deepcopy(current)
        if before is None:
            recorder.event("vitals_snapshot", boundary="round_start",
                           state=current, source="Dark_Snake/modules/game.py")
            return True
        changes = []
        for player, entry in current["players"].items():
            was = before["players"].get(player, {}).get("hp")
            now = entry["hp"]
            if was is not None and now is not None and was != now:
                changes.append({
                    "player": int(player), "hp_before": was, "hp_after": now,
                    "delta_hp": round(now - was, 3),
                })
        life_delta = current["lives_remaining"] - before["lives_remaining"]
        if changes or life_delta:
            recorder.event(
                "vitals_change", source=str(source)[:70],
                hp_changes=changes,
                lives_before=before["lives_remaining"],
                lives_after=current["lives_remaining"],
                lives_delta=life_delta,
                level=current["level"],
                boss=current["boss"]["key"] if current["boss"] else None,
                code="Dark_Snake/modules/game.py",
            )
        if checkpoint:
            recorder.event("vitals_snapshot", boundary=str(source)[:70],
                           state=current, source="Dark_Snake/modules/game.py")
        return bool(changes or life_delta or checkpoint)
