"""Regression tests for Boss Smooth Movement B (visual only)."""
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

from config import GRID_SIZE
from modules import game as game_module
from modules.game import Boss, Boss2


@pytest.mark.parametrize("boss_type", [Boss, Boss2])
def test_boss_glide_does_not_change_combat_hitbox_or_step_timing(monkeypatch, boss_type):
    clock = [100.0]
    monkeypatch.setattr(game_module.time, "time", lambda: clock[0])
    boss = boss_type(1)
    boss.x, boss.y = 8, 8
    boss.last_move = clock[0]
    boss._visual_from = boss._visual_to = (8, 8)
    boss._visual_step_start = clock[0]
    # Force +1,+1 for the step. Visual interpolation must NOT move the grid hitbox.
    monkeypatch.setattr(game_module.random, "choice", lambda choices: 1)
    clock[0] += boss.chase_speed
    boss.update(clock[0])
    assert (boss.x, boss.y) == (9, 9)
    logical_rect = boss.get_hitbox()
    assert logical_rect.topleft == (9 * GRID_SIZE, 9 * GRID_SIZE)
    assert boss._visual_position(clock[0]) == pytest.approx((8, 8))
    midpoint = clock[0] + boss.chase_speed * .45
    assert boss._visual_position(midpoint) == pytest.approx((8.5, 8.5))
    assert boss.get_hitbox() == logical_rect
    assert boss.get_rect() == logical_rect
    assert boss._visual_position(clock[0] + boss.chase_speed) == pytest.approx((9, 9))
    # Only an actual boss movement tick changes its authoritative hitbox.
    boss.update(midpoint)
    assert boss.get_hitbox() == logical_rect
