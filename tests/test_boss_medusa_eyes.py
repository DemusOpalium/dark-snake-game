"""Medusa Eyes A: actual sight, relay, prediction and safe boss movement."""
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

from modules.boss_medusa import MedusaEyes, medusa_step
from modules.game import Boss, Boss2
from modules import game as game_module


def see(eyes, now, origin=(5, 5), target=(8, 5),
        facing=(1, 0), blockers=frozenset(), player=1):
    return eyes.observe(
        origin, facing, [(player, target)], blockers, now, (40, 35),
    )


def test_medusa_needs_continuous_sight_before_placing_a_remote_eye():
    eyes = MedusaEyes()
    assert see(eyes, 10).kind == "UNAWARE"
    assert not eyes.remote
    assert see(eyes, 10.11).kind == "VISIBLE"
    assert len(eyes.remote) == 1
    assert eyes.remote[0].cell == (5, 5)
    assert see(eyes, 10.2).target_player == 1


def test_remote_eye_relay_after_boss_moves_away_but_not_through_wall():
    eyes = MedusaEyes()
    see(eyes, 10)
    see(eyes, 10.11)
    relay = see(eyes, 10.2, origin=(14, 5))
    assert relay.kind == "RELAY"
    assert relay.source == "relay"
    blocked = see(eyes, 10.3, origin=(14, 5), blockers={(7, 5)})
    assert blocked.kind == "SEARCHING"
    assert blocked.last_known_cell == (8, 5)


def test_memory_and_expiring_remote_eyes_do_not_see_through_time():
    eyes = MedusaEyes()
    see(eyes, 10)
    see(eyes, 10.11)
    seen = see(eyes, 10.2, origin=(14, 5))
    assert seen.kind == "RELAY"
    memory = see(eyes, 11, origin=(14, 5), target=(30, 30))
    assert memory.kind == "SEARCHING"
    assert memory.last_known_cell == (8, 5)
    lost = see(eyes, 15, origin=(14, 5), target=(30, 30))
    assert lost.kind == "UNAWARE"
    assert not lost.actionable
    # Eye lifetime is independent from sight memory and must eventually expire.
    see(eyes, 20, origin=(14, 5), target=(30, 30))
    assert not eyes.remote


def test_two_player_target_switch_and_reaction_delay():
    eyes = MedusaEyes(heavy=True)
    eyes.observe((5, 5), (1, 0),
                 [(1, (8, 5)), (2, (6, 5))], (), 1, (40, 35))
    result = eyes.observe((5, 5), (1, 0),
                          [(1, (8, 5)), (2, (6, 5))], (), 1.1, (40, 35))
    assert result.kind == "VISIBLE"
    assert result.target_player == 2


def test_prediction_is_bounded_by_two_cells_and_game_bounds():
    eyes = MedusaEyes()
    see(eyes, 5)
    see(eyes, 5.11)
    result = see(eyes, 5.25, target=(10, 5))
    assert result.kind == "VISIBLE"
    assert result.predicted_cell[0] <= 12
    assert result.predicted_cell[0] >= 10


def test_boss_steps_respect_large_footprint_and_blocked_diagonals():
    # A 4x4 boss cannot clip one cell of its footprint across a wall.
    assert medusa_step((5, 5), 4, (15, 7), frozenset({(9, 6)}), (40, 35)) != (1, 0)
    assert medusa_step((5, 5), 4, (15, 7), frozenset(), (40, 35)) == (1, 0)
    assert medusa_step((0, 0), 4, (-100, -100), frozenset(), (40, 35)) == (0, 0)


@pytest.mark.parametrize("boss_type", [Boss, Boss2])
def test_boss_preview_switch_preserves_classic_and_resets_all_eye_state(
        monkeypatch, boss_type):
    clock = [100.]
    monkeypatch.setattr(game_module.time, "time", lambda: clock[0])
    boss = boss_type(1)
    assert not boss.ai_preview
    boss.x, boss.y = 5, 5
    boss.last_move = clock[0]
    boss._visual_from = boss._visual_to = (5, 5)
    boss._visual_step_start = clock[0]
    boss.set_ai_preview(True)
    eye_origin = (boss.x + boss.size // 2, boss.y + boss.size // 2)
    boss.eyes.observe(eye_origin, (1, 0), [(1, (eye_origin[0] + 2, eye_origin[1]))],
                      frozenset(), clock[0], (40, 35))
    clock[0] += .11
    boss.eyes.observe(eye_origin, (1, 0), [(1, (eye_origin[0] + 2, eye_origin[1]))],
                      frozenset(), clock[0], (40, 35))
    assert boss.eyes.reading.kind == "VISIBLE"
    assert boss.eyes.remote
    boss.set_ai_preview(False)
    assert boss.eyes.reading.kind == "UNAWARE"
    assert not boss.eyes.remote
    assert not boss.ai_preview


@pytest.mark.parametrize("boss_type", [Boss, Boss2])
def test_boss_preview_moves_only_on_original_boss_step_cadence(monkeypatch, boss_type):
    clock = [10.]
    monkeypatch.setattr(game_module.time, "time", lambda: clock[0])
    boss = boss_type(1)
    boss.x, boss.y = 5, 5
    boss.last_move = clock[0]
    boss._visual_from = boss._visual_to = (5, 5)
    boss._visual_step_start = clock[0]
    boss.set_ai_preview(True)
    origin = (boss.x + boss.size // 2, boss.y + boss.size // 2)
    target = (origin[0] + 6, origin[1])
    boss.eyes.observe(origin, (1, 0), [(1, target)], (), clock[0], (40, 35))
    clock[0] += .15
    boss.eyes.observe(origin, (1, 0), [(1, target)], (), clock[0], (40, 35))
    assert boss.eyes.reading.actionable
    boss.update(clock[0])
    assert (boss.x, boss.y) == (5, 5)  # not yet at movement tick
    clock[0] += boss.chase_speed
    boss.update(clock[0])
    assert boss.x == 6
    assert boss.get_hitbox().x == 6 * game_module.GRID_SIZE
