"""Real Dark Abyss renderer: the cinematic counts only *display* round totals."""
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

from modules.game_over_visual import (
    CEREMONY_COLORS, CEREMONY_TIERS, COUNTER_DURATION_SECONDS,
    COUNTER_START_SECONDS, TITLE_TEXT, TITLE_LETTER_SECONDS,
    DarkAbyssGameOver, ceremony_color, revealed_counter,
    revealed_title_letters,
)


@pytest.mark.parametrize("value", [0, 1, 250, 9515, 3_000_000, 1_234_567_890])
def test_countup_is_monotonic_constant_time_and_exactly_reaches_real_total(value):
    times = [-2., 0., .9, COUNTER_START_SECONDS,
             COUNTER_START_SECONDS + .1,
             COUNTER_START_SECONDS + COUNTER_DURATION_SECONDS / 2,
             COUNTER_START_SECONDS + COUNTER_DURATION_SECONDS - .01,
             COUNTER_START_SECONDS + COUNTER_DURATION_SECONDS,
             COUNTER_START_SECONDS + COUNTER_DURATION_SECONDS + 250.]
    displayed = [revealed_counter(value, t) for t in times]
    assert displayed == sorted(displayed)
    assert displayed[0] == 0
    assert displayed[-1] == value
    assert all(0 <= v <= value for v in displayed)
    assert revealed_counter(-10, 999.) == 0


def test_typewriter_spells_game_over_in_place_and_is_not_fps_dependent():
    assert revealed_title_letters(-1) == 0
    assert revealed_title_letters(0) == 0
    assert revealed_title_letters(TITLE_LETTER_SECONDS) == 1
    assert revealed_title_letters(4 * TITLE_LETTER_SECONDS) == 4
    assert revealed_title_letters(len(TITLE_TEXT) * TITLE_LETTER_SECONDS) == len(TITLE_TEXT)
    assert revealed_title_letters(500) == len(TITLE_TEXT)


def test_palette_thresholds_match_each_counter_not_an_unvalidated_skill_rating():
    assert len(CEREMONY_TIERS) == 4
    assert len(CEREMONY_COLORS) == 6
    for key, thresholds in CEREMONY_TIERS.items():
        assert len(thresholds) == len(CEREMONY_COLORS)
        assert thresholds == tuple(sorted(thresholds))
        assert ceremony_color(key, 0) == CEREMONY_COLORS[0]
        assert ceremony_color(key, thresholds[2] - 1) == CEREMONY_COLORS[1]
        assert ceremony_color(key, thresholds[-1]) == CEREMONY_COLORS[-1]
    assert ceremony_color("PUNKTE", 15_000) == CEREMONY_COLORS[-1]
    assert ceremony_color("BOSSE", 1) != ceremony_color("GEGNER", 1)


def render(visual, *, now, sequence, size=(1350, 930), score=9515, level=7,
           enemies=134, bosses=6, name="TestName", highscore=True):
    target = pygame.Surface(size)
    visual.draw(target, score=score, level=level, enemies=enemies,
                bosses=bosses, items=203, players=1,
                highscore_entry=highscore, name_input=name, buttons=[],
                now=now, reward_sequence=sequence)
    return target


def test_actual_game_over_typing_then_counts_then_final_exact_numbers():
    ui = DarkAbyssGameOver()
    first = render(ui, now=40., sequence="round-one")
    assert ui.last_reveal_title == ""
    assert ui.last_reveal_numbers == (0, 0, 0, 0)
    cache = ui._metric_label_cache.copy()
    assert len(cache) == 4
    # The zero-score surface of each stat card is physically painted;
    # unchanged inputs on the next frame reuse those four cached glyphs.
    render(ui, now=40.01, sequence="round-one")
    assert all(ui._metric_label_cache[i][1] is cache[i][1] for i in range(4))

    typed = render(ui, now=40. + 4 * TITLE_LETTER_SECONDS,
                   sequence="round-one")
    assert ui.last_reveal_title == "GAME"
    assert ui.last_reveal_numbers == (0, 0, 0, 0)

    halfway = render(ui, now=40. + COUNTER_START_SECONDS +
                     COUNTER_DURATION_SECONDS / 2, sequence="round-one")
    counts = ui.last_reveal_numbers
    assert 0 < counts[0] < 9515
    assert 0 < counts[1] < 7
    assert 0 < counts[2] < 134
    assert 0 < counts[3] < 6
    assert ui.last_reveal_title == "GAME OVER"

    last = render(ui, now=40. + COUNTER_START_SECONDS +
                  COUNTER_DURATION_SECONDS + .01, sequence="round-one")
    assert ui.last_reveal_title == "GAME OVER"
    assert ui.last_reveal_numbers == (9515, 7, 134, 6)
    assert ui._metric_label_cache[0][0][0] == 9515
    assert ui._metric_label_cache[0][0][1] == ceremony_color("PUNKTE", 9515)
    # The rendered pixel buffer changes in the actual scoreboard region.
    stat_rect = pygame.Rect(55, 310, 640, 100)
    assert pygame.image.tostring(first.subsurface(stat_rect), "RGB") != (
        pygame.image.tostring(last.subsurface(stat_rect), "RGB"))
    assert pygame.image.tostring(typed.subsurface(stat_rect), "RGB") != (
        pygame.image.tostring(halfway.subsurface(stat_rect), "RGB"))


def test_new_round_replays_while_old_summary_and_name_never_change():
    ui = DarkAbyssGameOver()
    target = render(ui, now=100., sequence="A", score=308,
                    enemies=4, bosses=0)
    assert ui.last_reveal_numbers == (0, 0, 0, 0)
    render(ui, now=120., sequence="A", score=308, enemies=4, bosses=0)
    assert ui.last_reveal_numbers == (308, 7, 4, 0)
    # Same total and same UI object, but a DIFFERENT round key.
    render(ui, now=200., sequence="B", score=308, enemies=4, bosses=0)
    assert ui.last_reveal_numbers == (0, 0, 0, 0)
    assert ui.last_reveal_title == ""
    assert target.get_size() == (1350, 930)


@pytest.mark.parametrize("size", [(900, 620), (1350, 930)])
def test_countup_preserves_name_entry_and_controls_at_every_stage(size):
    ui = DarkAbyssGameOver()
    begin = render(ui, now=10., sequence="short", size=size, score=615,
                   level=2, enemies=5, bosses=1, name="Irian")
    finish = render(ui, now=100., sequence="short", size=size, score=615,
                    level=2, enemies=5, bosses=1, name="Irian")
    assert ui.last_reveal_numbers == (615, 2, 5, 1)
    # Name field background pixels are constant; no replay mask covers input.
    # The field X changes in the large side-by-side layout only with a reward,
    # which this renderer test intentionally does not provide.
    px = size[0] // 2
    y = max(20, round(size[1] * .057)) + 480 + 8
    assert begin.get_at((px + 140, y)) == finish.get_at((px + 140, y))


def test_missing_career_data_is_not_replaced_by_fake_achievement():
    ui = DarkAbyssGameOver()
    render(ui, now=0, sequence="zero", score=0, level=1, enemies=0, bosses=0)
    render(ui, now=25, sequence="zero", score=0, level=1, enemies=0, bosses=0)
    assert ui.last_reveal_numbers == (0, 1, 0, 0)
    assert ui._tombstone_reward._base is None
