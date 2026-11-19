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
from modules.game_over_visual import DarkAbyssGameOver, tombstone_scene_layout
from modules.tombstone_reward_visual import (
    ASPECT, EPITAPH_IMAGE, HOLD_SECONDS as TOMB_HOLD,
    FADE_SECONDS as TOMB_FADE, TombstoneRewardPanel, INK_THEMES,
    epitaph_ink,
)
from modules.resources import find_asset
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
def test_full_size_tombstone_is_beside_stats_not_over_name_or_buttons(highscore, reward):
    visual = DarkAbyssGameOver()
    size = (1333, 941)
    target = draw(visual, size, realistic_career(reward), highscore=highscore)
    stone = visual._tombstone_reward
    scene = tombstone_scene_layout(size)
    assert scene is not None
    left, panel_width, expected_rect = scene
    assert stone._base is not None
    assert stone.last_rect == expected_rect
    assert stone.last_rect.left >= left + panel_width + 30
    assert stone.last_rect.right <= size[0]
    assert stone.last_rect.bottom == size[1]  # Skull pedestal meets abyss floor.
    assert abs(stone.last_rect.height / stone.last_rect.width - ASPECT) <= .004
    assert stone.last_slots["icon"].centery < stone.last_slots["title"].top
    assert stone.last_slots["title"].bottom < stone.last_slots["reason"].top
    assert stone.last_slots["praise"].bottom < stone.last_slots["rank"].top
    assert visual._mystic_reward._base is None
    assert visual._career_card_cache is None
    # PNG alpha exposes the original untouched abyss outside its stone edges.
    assert stone._base.get_at((0, 0)).a == 0
    assert target.get_at(stone.last_rect.center) != visual._image_for(size).get_at(
        stone.last_rect.center)
    if highscore:
        summary_top = max(20, int(size[1] * .057))
        input_rect = pygame.Rect(left + 90, summary_top + 480, panel_width - 180, 51)
        assert not input_rect.colliderect(stone.last_rect)
        assert target.get_at((input_rect.right - 25, input_rect.top + 9))[:3] == (6, 14, 29)


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
    panel = visual._tombstone_reward
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
    panel = visual._tombstone_reward
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



def test_vetted_staged_gravestone_is_bundled_with_alpha_and_copied_exactly():
    image = pygame.image.load(str(find_asset(*EPITAPH_IMAGE)))
    assert image.get_size() == (1024, 1536)
    assert image.get_at((0, 0)).a == 0
    assert image.get_at((512, 880)).a > 0
    assert TombstoneRewardPanel()._art is not None


@pytest.mark.parametrize("size", [(1350, 930), (1333, 941), (1180, 820)])
def test_large_responsive_scene_never_stretches_art_or_covers_stats(size):
    layout = tombstone_scene_layout(size)
    assert layout is not None
    left, panel_width, rect = layout
    assert left >= 0
    assert rect.left >= left + panel_width + 30
    assert rect.right <= size[0] - round(size[0] * .055)
    # The skull pedestal must meet the actual lower framebuffer edge.
    assert rect.bottom == size[1]
    assert abs(rect.height / rect.width - 1.5) < .004
    # Side-by-side arrangement preserves the original full-width stats panel.
    assert left >= 20
    assert panel_width == 700


def test_tombstone_fades_at_15_plus_3_seconds_and_resets_for_new_run():
    panel = TombstoneRewardPanel()
    result = realistic_career(True)
    rect = pygame.Rect(12, 12, 460, 690)
    canvas = pygame.Surface((600, 730), pygame.SRCALPHA)
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=20, sequence="A") == 255
    first = panel._base
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=20+TOMB_HOLD-0.1, sequence="A") == 255
    faded = panel.draw(canvas, career=result, warning=False,
                       rect=rect, now=20+TOMB_HOLD+TOMB_FADE/2, sequence="A")
    assert 110 <= faded <= 145
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=20+TOMB_HOLD+TOMB_FADE+1, sequence="A") == 0
    assert panel.draw(canvas, career=result, warning=False,
                      rect=rect, now=90, sequence="B") == 255
    assert panel._base is first
    assert len(panel._aura) == 12


@pytest.mark.parametrize("reward", [False, True])
def test_tombstone_renders_real_reward_only_and_all_text_centred(reward):
    panel = TombstoneRewardPanel()
    result = realistic_career(reward)
    rect = pygame.Rect(20, 20, 490, 735)
    screen = pygame.Surface((550, 785), pygame.SRCALPHA)
    panel.draw(screen, career=result, warning=False,
               rect=rect, now=1, sequence="x")
    assert panel._base.get_size() == rect.size
    # Real Georgia bold/italic face files may report *synthetic* bold=False
    # even when using the installed bold face. Verify usable rendered fonts
    # without relying on that platform-dependent Pygame flag.
    assert len(panel._font_cache) == 4
    assert all(font.get_height() >= 16 for font in panel._font_cache)
    assert panel._font_cache[0].size("RANGAUFSTIEG")[0] > 0
    assert panel.last_slots["icon"].centerx == rect.width // 2
    for name in ("title", "reason", "praise", "rank", "progress"):
        assert panel.last_slots[name].centerx == rect.width // 2
        assert panel.last_slots[name].right < rect.width
    if reward:
        assert panel._picture(result) is not None
        assert len(panel._images) == 1
    else:
        assert panel._images == {}


def test_actual_button_hitboxes_are_left_of_portrait_after_game_render():
    from modules.game import Game
    from modules.enums import GameState
    from modules.career_ceremony import CareerCeremony
    game = Game(headless=True)
    game.start_game(1)
    game.game_state = GameState.GAME_OVER
    game.leaderboard_mode = False
    game.round_career_result = realistic_career()
    game._death_soul_event = None
    game.draw()
    stone = game._game_over_visual._tombstone_reward.last_rect
    assert stone is not None
    for btn in game.game_over_buttons:
        assert not btn.rect.colliderect(stone)
        assert btn.rect.x >= 0
    game.round_career_result = None
    game.draw()
    assert game.game_over_buttons[0].rect.x == game.screen.get_width() // 2 - 228



@pytest.mark.parametrize("width", [350, 420, 508, 545])
@pytest.mark.parametrize("career", [
    CareerCeremony(39, 40, 2_345_678, 123_456_789, None, "none"),
    CareerCeremony(4, 5, 376, 5305, 7500, "none"),
    CareerCeremony(19, 20, 44_222, 48_123, 52_000, "pending"),
])
def test_growing_xp_and_long_german_strings_do_not_leave_carved_text_slots(width, career):
    panel = TombstoneRewardPanel()
    height = round(width * 1.5)
    canvas = pygame.Surface((width, height), pygame.SRCALPHA)
    panel.draw(canvas, career=career, warning=False,
               rect=pygame.Rect(0, 0, width, height), now=1, sequence=1)
    assert panel.last_text_bounds
    for name, rendered_lines in panel.last_text_bounds.items():
        slot = panel.last_slots[name]
        assert len(rendered_lines) >= 1, name
        for text_rect in rendered_lines:
            assert slot.contains(text_rect), (width, name, text_rect, slot)
            assert slot.contains(text_rect.move(1, 1)), (width, name, text_rect, slot)
        # Keep a distinct safe strip between each block of lettering.
    keys = ["title", "reason", "praise", "rank", "progress"]
    assert all(panel.last_slots[a].bottom < panel.last_slots[b].top
               for a, b in zip(keys, keys[1:]))
    assert panel.last_slots["progress"].bottom < round(height * .806)


def test_dynamic_engraving_shrinks_and_wraps_overlong_text_inside_safe_face(monkeypatch):
    panel = TombstoneRewardPanel()
    very_long = ("Schlangenchronik des grenzenlosen Abgrundes und der "
                 "gefrorenen uralten Welten im Schatten des Universums")
    monkeypatch.setattr(panel, "_narrative", lambda career, warning:
                        (very_long, very_long, very_long))
    width = 390
    canvas = pygame.Surface((width, 585), pygame.SRCALPHA)
    panel.draw(canvas, career=realistic_career(True), warning=False,
               rect=pygame.Rect(0, 0, width, 585), now=1, sequence=1)
    for name in ("title", "reason", "praise"):
        rect = panel.last_slots[name]
        assert panel.last_text_bounds[name]
        assert all(rect.contains(box) for box in panel.last_text_bounds[name])


def test_dark_ink_roll_is_stable_and_unlocks_more_styles_with_career_rank():
    assert len(INK_THEMES) == 5
    low = {epitaph_ink(CareerCeremony(1, 1, i, i, 500, "none"))[0]
           for i in range(50, 100)}
    high = {epitaph_ink(CareerCeremony(39, 40, i, 1_000_000 + i,
                                     None, "none"))[0]
            for i in range(50, 150)}
    assert len(low) == 2
    assert len(high) == len(INK_THEMES)
    assert low.issubset(high)
    for value in (1, 20, 4000):
        sample = CareerCeremony(1, 2, value, value, 1500, "none")
        assert epitaph_ink(sample) == epitaph_ink(sample)
    assert epitaph_ink(None) == INK_THEMES[0]
    # These are dark *themes*, not dark-on-dark text: every text color has
    # at least one high-contrast bright channel.
    for palette in INK_THEMES:
        for color in palette[1:]:
            assert max(color) >= 215


def test_engraved_palette_is_not_rerolled_every_frame():
    panel = TombstoneRewardPanel()
    career = CareerCeremony(4, 5, 376, 5305, 7500, "none")
    canvas = pygame.Surface((550, 785), pygame.SRCALPHA)
    rect = pygame.Rect(10, 10, 490, 735)
    panel.draw(canvas, career=career, warning=False, rect=rect, now=1, sequence=1)
    first, ink = panel._base, panel.last_ink_theme
    for tick in (2, 3, 4, 6, 10):
        panel.draw(canvas, career=career, warning=False,
                   rect=rect, now=tick, sequence=1)
        assert panel._base is first
        assert panel.last_ink_theme == ink
