"""Dark Abyss: reward art placement, glow, fade and truthful award captions."""
import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules.career_ceremony import CareerCeremony
from modules.career_reward_visual import (
    HOLD_SECONDS, FADE_SECONDS, MysticRewardPanel, PANEL_HEIGHT,
)
from modules.game_over_visual import DarkAbyssGameOver
from modules.skin_inventory import skin_registry


def realistic_career(reward=False):
    grant = skin_registry().career[0]
    return CareerCeremony(
        rank_before=1 if reward else 4,
        rank_after=2 if reward else 4,
        earned_xp=1413 if reward else 130,
        total_xp=1413 if reward else 4393,
        next_rank_xp=1500 if reward else 5000,
        reward_state="granted" if reward else "none",
        reward_id=grant["id"] if reward else None,
        reward_type=grant["type"] if reward else None,
        reward_filename=grant["filename"] if reward else None,
        reward_required_rank=2 if reward else None,
    )


def draw(visual, size, career, *, highscore=True, now=100, sequence="run-1"):
    target = pygame.Surface(size)
    visual.draw(
        target, score=308, level=2, enemies=4, items=12,
        bosses=0, players=1, highscore_entry=highscore,
        name_input="TestName", buttons=[], now=now,
        career=career, reward_sequence=sequence,
    )
    return target


@pytest.mark.parametrize("highscore", [True, False])
@pytest.mark.parametrize("reward", [False, True])
def test_award_is_separate_below_name_and_main_panel(highscore, reward):
    visual = DarkAbyssGameOver()
    size = (1333, 941)
    target = draw(visual, size, realistic_career(reward), highscore=highscore)
    panel = visual._mystic_reward
    assert panel._base is not None
    rect = panel.last_rect
    assert rect is not None
    assert 650 < rect.width < size[0]
    assert rect.height == PANEL_HEIGHT
    assert rect.centerx == size[0] // 2
    top = max(20, int(size[1] * .057))
    main_panel_bottom = top + 418
    input_bottom = top + 450 + 30 + 51
    assert rect.top > main_panel_bottom
    assert rect.top > input_bottom + 15
    assert rect.bottom <= size[1] - 17
    assert panel._base.get_at((30, 30)).a > 0
    assert visual._career_card_cache is None
    assert target.get_at(rect.center) != visual._image_for(size).get_at(rect.center)


@pytest.mark.parametrize("size", [(900, 620), (900, 730), (1100, 790)])
def test_compact_fallback_keeps_name_and_buttons_uncovered(size):
    visual = DarkAbyssGameOver()
    result = draw(visual, size, realistic_career(), highscore=True)
    assert visual._mystic_reward._base is None
    assert visual._career_card_cache is not None
    panel_top = max(20, int(size[1] * .057))
    name_bottom = panel_top + 531
    assert name_bottom < size[1]
    panel_width = min(700, size[0] - 40)
    input_rect = pygame.Rect(
        (size[0] - panel_width) // 2 + 90,
        panel_top + 480, panel_width - 180, 51,
    )
    # Sample the dark interior, not the intentionally cyan input border.
    assert result.get_at((input_rect.right - 25, input_rect.y + 9))[:3] == (6, 14, 29)
    # Real mouse-button hitboxes at y520..572 stay available.
    visual_no_entry = DarkAbyssGameOver()
    draw(visual_no_entry, size, realistic_career(), highscore=False)
    assert visual_no_entry._mystic_reward._base is None


def test_earned_picture_is_loaded_and_ceremonial_copy_cached():
    visual = DarkAbyssGameOver()
    game_result = realistic_career(reward=True)
    draw(visual, (1333, 941), game_result, now=11)
    panel = visual._mystic_reward
    assert panel._narrative(game_result, False)[0] == "SCHLANGENKRONE ERRUNGEN"
    assert "Karriererang 2" in panel._narrative(game_result, False)[1]
    assert panel._picture(game_result) is not None
    assert len(panel._images) == 1
    before = panel._base
    draw(visual, (1333, 941), game_result, now=12)
    assert panel._base is before
    assert len(panel._aura) == 12


def test_no_unearned_achievement_claim_for_fourth_real_round_values():
    visual = DarkAbyssGameOver()
    current = realistic_career()
    draw(visual, (1333, 941), current, now=99)
    panel = visual._mystic_reward
    title, explanation, praise = panel._narrative(current, False)
    assert title == "CHRONIK DER TIEFE"
    assert "130 XP" in explanation
    assert "ohne neues Relikt" in praise
    assert panel._images == {}
    assert current.xp_to_next_rank == 607


def test_panel_fades_after_several_seconds_but_new_run_resets_animation():
    panel = MysticRewardPanel()
    canvas = pygame.Surface((900, 700), pygame.SRCALPHA)
    rect = pygame.Rect(100, 100, 720, PANEL_HEIGHT)
    result = realistic_career(reward=True)
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=30.0, sequence="runA") == 255
    first = panel._base
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=30.0 + HOLD_SECONDS - 0.1,
                      sequence="runA") == 255
    middle = panel.draw(canvas, career=result, warning=False, rect=rect,
                        now=30.0 + HOLD_SECONDS + FADE_SECONDS / 2,
                        sequence="runA")
    assert 110 <= middle <= 145
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=30.0 + HOLD_SECONDS + FADE_SECONDS + 2,
                      sequence="runA") == 0
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=99.0, sequence="runB") == 255
    assert panel._base is first


def test_pending_or_failed_commit_never_claims_a_reward():
    panel = MysticRewardPanel()
    pending = CareerCeremony(1, 2, 1413, 1413, 1500, "pending")
    assert panel._narrative(pending, False)[0] == "DIE CHRONIK WARTET"
    text = " ".join(panel._narrative(pending, False)).lower()
    assert "ungeprüft" in text
    assert panel._picture(pending) is None
    title, reason, praise = panel._narrative(None, True)
    assert "UNGEWISS" in title
    assert "nicht bestätigt" in reason
    assert panel._picture(None) is None


def test_glow_read_only_does_not_modify_economy():
    result = realistic_career(reward=True)
    snapshot = result.__dict__.copy()
    visual = DarkAbyssGameOver()
    for time in (1., 1.2, 2., 3., 7., 9., 10.):
        draw(visual, (1333, 941), result, now=time)
    assert result.__dict__ == snapshot
