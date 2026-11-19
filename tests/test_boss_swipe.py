"""Boss Defense D: charged swipe, safe side lanes, live hitbox, shield fallback."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE
from modules.boss_defense import IncomingShot
from modules.boss_swipe import MedusaSwipe, choose_swipe
from modules import game as game_module
from modules.game import Boss, Boss2, Game


def shot(identity=1, position=(13, 7), velocity=(-1, 0), radius_cells=.5):
    return IncomingShot(identity, position, velocity, radius_cells)


def observe(swipe, now, *, position=(5, 5), incoming=None, blockers=(),
            heads=(), grid=(45, 35)):
    threat = incoming or shot()
    return swipe.observe(
        position, position, 3, (threat,), (threat,),
        blockers, grid, heads, now,
    )


def test_swipe_perpendicular_to_actual_incoming_ray_not_into_it():
    incoming = shot()
    assert choose_swipe((5, 5), 3, incoming, (incoming,),
                        (), (45, 35)) == (5, 3)
    vertical = shot(position=(7, 13), velocity=(0, -1))
    destination = choose_swipe((5, 5), 3, vertical, (vertical,),
                               (), (45, 35))
    assert destination is not None
    assert destination[1] == 5
    assert abs(destination[0] - 5) == 2


def test_four_cell_boss_can_clear_a_centered_projectile_with_three_cells():
    # An oversized boss would still overlap the shot after just two tiles.
    incoming = shot(position=(13, 7))
    dst = choose_swipe((5, 5), 4, incoming, (incoming,), (), (45, 35),
                       rng=lambda candidates: candidates[0])
    assert dst is not None
    assert dst[0] == 5
    assert abs(dst[1] - 5) == 3



def test_large_slow_fireball_needs_4_cell_swipe_to_clear_future_hitbox():
    # 96px fireball artwork is 3.2 GRID cells wide; predicting only the
    # first 10 frames incorrectly treated a 2-cell dodge as a safe escape.
    flame = shot(position=(13, 6.5), velocity=(-.15, 0),
                 radius_cells=1.6)
    destination = choose_swipe(
        (5, 5), 3, flame, (flame,), (), (45, 35),
        rng=lambda candidates: candidates[0],
    )
    assert destination is not None
    assert destination[0] == 5
    assert abs(destination[1] - 5) >= 4



def test_swipe_respects_full_footprint_and_intermediate_walls():
    incoming = shot()
    assert choose_swipe((5, 5), 3, incoming, (incoming,),
                        {(6, 4)}, (45, 35)) is None
    assert choose_swipe((5, 5), 3, incoming, (incoming,),
                        {(6, 4), (7, 8)}, (45, 35)) is None


def test_swipe_rejects_player_head_on_destination():
    incoming = shot()
    result = choose_swipe((5, 5), 3, incoming, (incoming,),
                          (), (45, 35), [(6, 4)])
    assert result is None


def test_swipe_requires_continuous_reaction_and_spends_two_charges():
    swipe = MedusaSwipe()
    assert swipe.charges(10) == 2
    assert observe(swipe, 10) is None
    assert observe(swipe, 10.04) is None
    first = observe(swipe, 10.07)
    assert first is not None
    assert first.destination == (5, 3)
    assert swipe.charges(10.07) == 1
    assert first.position(first.began_at) == (5, 5)
    assert first.position(first.began_at + first.duration / 2) == pytest.approx((5, 4))
    assert first.position(first.began_at + first.duration) == (5, 3)
    incoming = shot(2, position=(13, 7))
    assert observe(swipe, 10.30, incoming=incoming) is None
    assert observe(swipe, 10.37, incoming=incoming) is not None
    assert swipe.charges(10.37) == 0
    assert observe(swipe, 11, incoming=shot(3)) is None
    assert swipe.charges(22.06) == 0
    assert swipe.charges(22.08) == 1
    assert swipe.charges(22.38) == 2


def test_swipe_cancellation_does_not_refund_charges():
    swipe = MedusaSwipe()
    observe(swipe, 10)
    assert observe(swipe, 10.07) is not None
    swipe.cancel()
    assert swipe.action is None
    assert swipe.charges(10.1) == 1
    swipe.reset()
    assert swipe.charges(10.1) == 2


def test_swipe_blocked_by_current_player_head_keeps_shield_fallback():
    incoming = shot()
    assert choose_swipe(
        (5, 5), 3, incoming, (incoming,),
        (), (45, 35), [(6, 4)],
    ) is None


def make_combat(monkeypatch, boss_class=Boss):
    clock = SimpleNamespace(now=100.)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(1)
    game.start_boss_fight()
    boss = boss_class(1)
    boss.x, boss.y = 5, 5
    boss.size = 3
    boss._visual_from = boss._visual_to = (5, 5)
    boss._visual_step_start = clock.now
    boss.last_move = clock.now
    boss.spawn_time = clock.now - 5
    boss.facing = (1, 0)
    boss.set_ai_preview(True)
    game.boss = boss
    game.enemy_ai_preview = True
    game.snake = [(2, 2)]
    return game, boss, clock


@pytest.mark.parametrize("boss_type", [Boss, Boss2])
def test_game_swipe_sprite_and_hitbox_interpolate_together(monkeypatch, boss_type):
    game, boss, clock = make_combat(monkeypatch, boss_type)
    game.projectiles = [{"pos": (12.5, 6.5), "dir": (-1, 0)}]
    start_rect = boss.get_hitbox()
    game._scan_boss_defense(clock.now)
    assert boss.swipe.action is None
    clock.now += .07
    game._scan_boss_defense(clock.now)
    assert boss.swipe.action is not None
    assert boss.swipe.charges(clock.now) == 1
    assert boss.defense.active(clock.now) is False
    assert boss.get_hitbox() == start_rect
    assert boss._visual_position(clock.now) == pytest.approx((5, 5))
    assert boss.update(clock.now) is None
    clock.now += .09
    vx, vy = boss._visual_position(clock.now)
    assert (vx, vy) == pytest.approx((5, 4))
    assert boss.get_hitbox().topleft == (5 * GRID_SIZE, 4 * GRID_SIZE)
    clock.now += .09
    assert boss.get_hitbox().topleft == (5 * GRID_SIZE, 3 * GRID_SIZE)
    assert boss._visual_position(clock.now) == pytest.approx((5, 3))
    assert boss.swipe.charges(clock.now) == 1


def test_game_no_safe_side_lane_falls_back_to_existing_shield(monkeypatch):
    game, boss, clock = make_combat(monkeypatch)
    game.projectiles = [{"pos": (12.5, 6.5), "dir": (-1, 0)}]
    # Block the one safe upper lane inside the boss's footprint.
    game._vision_blockers = {(6, 4)}
    boss.navigation_blockers = game._vision_blockers
    game._scan_boss_defense(clock.now)
    clock.now += .07
    game._scan_boss_defense(clock.now)
    assert boss.swipe.action is None
    assert boss.swipe.charges(clock.now) == 2
    assert boss.defense.active(clock.now)


def test_swipe_disabled_preserves_classic_normal_logic(monkeypatch):
    game, boss, clock = make_combat(monkeypatch)
    boss.set_ai_preview(False)
    game.projectiles = [{"pos": (12.5, 6.5), "dir": (-1, 0)}]
    game._scan_boss_defense(clock.now)
    clock.now += .5
    game._scan_boss_defense(clock.now)
    assert boss.swipe.action is None
    assert boss.swipe.charges(clock.now) == 2
    assert not boss.defense.active(clock.now)
    assert boss.get_hitbox().topleft == (5 * GRID_SIZE, 5 * GRID_SIZE)


def test_pause_cancel_does_not_keep_half_finished_sweep(monkeypatch):
    game, boss, clock = make_combat(monkeypatch)
    game.projectiles = [{"pos": (12.5, 6.5), "dir": (-1, 0)}]
    game._scan_boss_defense(clock.now)
    clock.now += .07
    game._scan_boss_defense(clock.now)
    assert boss.swipe.active(clock.now)
    boss.cancel_swipe(clock.now)
    assert not boss.swipe.active(clock.now)
    assert boss.get_hitbox().topleft == (5 * GRID_SIZE, 3 * GRID_SIZE)
    assert boss.swipe.charges(clock.now) == 1
