"""Project confirmed career progress into one immutable Game Over presentation.

This is deliberately a read-only view of the two already committed ledgers:
never infer rank/skin from transient score, never award cosmetics on draw.
"""
from __future__ import annotations

from dataclasses import dataclass

from modules.career_ranks import (
    MAX_CAREER_RANK, RANK_MIN_XP, _validate_state as validate_career_state,
    career_rank,
)
from modules.skin_inventory import _validate_inventory as validate_skin_inventory


@dataclass(frozen=True)
class CareerCeremony:
    """Single completed round's facts for the Dark Abyss, safe to render often."""

    rank_before: int
    rank_after: int
    earned_xp: int
    total_xp: int
    next_rank_xp: int | None
    reward_state: str  # "granted", "none", "pending"
    reward_id: str | None = None
    reward_type: str | None = None
    reward_filename: str | None = None
    reward_required_rank: int | None = None

    @property
    def xp_to_next_rank(self) -> int | None:
        if self.next_rank_xp is None:
            return None
        return self.next_rank_xp - self.total_xp


def career_ceremony_for_round(round_id, career, inventory=None, registry=None):
    """Return a truthful presentation of exactly ONE committed round UUID.

    Older game history may already have many awards. Only the XP and grant
    belonging to this run are presented as NEW. When inventory sync has failed,
    the ceremony reports a pending check, not a made-up missing reward.
    """
    validate_career_state(career)
    if not isinstance(round_id, str):
        raise ValueError("A committed round ID is required for the ceremony.")
    earlier_xp = 0
    current_xp = None
    earned_xp = None
    for award in career["awards"]:
        after_xp = earlier_xp + award["xp"]
        if award["round_id"] == round_id:
            current_xp = after_xp
            earned_xp = award["xp"]
            break
        earlier_xp = after_xp
    if current_xp is None:
        raise ValueError("Game Over round is absent from verified career awards.")

    new_rank = career_rank(current_xp)
    next_total = (RANK_MIN_XP[new_rank] if new_rank < MAX_CAREER_RANK else None)
    reward_state, reward_id, reward_type, reward_filename = (
        "pending", None, None, None
    )
    reward_required_rank = None
    if inventory is not None and registry is not None:
        validate_skin_inventory(inventory, registry)
        if round_id in inventory["processed_rounds"]:
            matched = [grant for grant in inventory["grants"]
                       if grant["round_id"] == round_id]
            if len(matched) > 1:
                raise ValueError("At most one cosmetic reward per round.")
            if matched:
                item = registry.by_id[matched[0]["skin_id"]]
                reward_state = "granted"
                reward_id = item["id"]
                reward_type = item["type"]
                reward_filename = item["filename"]
                reward_required_rank = matched[0]["required_rank"]
            else:
                reward_state = "none"
    return CareerCeremony(
        rank_before=career_rank(earlier_xp),
        rank_after=new_rank,
        earned_xp=earned_xp,
        total_xp=current_xp,
        next_rank_xp=next_total,
        reward_state=reward_state,
        reward_id=reward_id,
        reward_type=reward_type,
        reward_filename=reward_filename,
        reward_required_rank=reward_required_rank,
    )
