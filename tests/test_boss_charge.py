"""Medusa Roll/Charge A – locked geometry, one hit/charge and interruptions.

The existing World Studio, regular Classic gameplay and progression must
remain unaffected. Tests use the same real Game/Boss classes as Windows CI.
"""
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

from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH
from modules.boss_charge import (
    CHARGE_SECONDS, COOLDOWN_SECONDS, RECOVERY_SECONDS, WARNING_SECONDS,
    ChargeAction, MedusaCharge, choose_charge, swept_footprint,
)
from modules.boss_charge_visual import draw_medusa_charge
from modules.boss_medusa import MedusaReading
from modules import game as game_module
from modules.enums import GameState
from modules.game import BOSS_BODY_DAMAGE, Boss, Game


def fight(monkeypatch, players=1, level=1):
    clock = SimpleNamespace(now=100.)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(players)
    game.level = level
    game.start_boss_fight()
    boss = game.boss
    boss.spawn_time = clock.now - 8
    boss.x, boss.y = 5, 5
    boss._visual_from = boss._visual_to = (5, 5)
    boss._visual_step_start = boss.last_move = clock.now
    boss.set_ai_preview(True)
    game.enemy_ai_preview = True
    game._vision_blockers = frozenset()
    game.respawn_invincible_until = 0
    game.effects["invincibility"] = 0
    game._boss_contact_ready_at.clear()
    boss.eyes.reading = MedusaReading(
        "VISIBLE", 1, (14, 6), (14, 6), "direct",
    )
    if players == 1:
        game.snake = [(8, 6)]
    else:
        game.snake1 = [(8, 6)]
        game.snake2 = [(10, 6)]
    return game, boss, clock


def test_fixed_cardinal_lane_respects_full_footprint_and_all_cells():
    assert choose_charge(
        (5, 5), 3, (14, 6), (), (GRID_WIDTH, GRID_HEIGHT),
    ) == (9, 5)
    assert choose_charge(
        (5, 5), 3, (14, 6), {(8, 5)}, (GRID_WIDTH, GRID_HEIGHT),
    ) is None
    assert choose_charge(
        (5, 5), 3, (14, 6), (), (GRID_WIDTH, GRID_HEIGHT),
        bodies={(8, 6)},
    ) is None
    assert choose_charge((5, 5), 3, (7, 15), (), (45, 31)) is None
    assert choose_charge((41, 5), 3, (44, 6), (), (45, 31)) is None


def test_continuous_sweep_prevents_tunneling_between_coarse_frames():
    assert not swept_footprint((2, 5), (2, 5), 2, (7, 5))
    assert swept_footprint((2, 5), (10, 5), 2, (7, 5))
    assert not swept_footprint((2, 5), (10, 5), 2, (7, 9))
    assert swept_footprint((7, 5), (3, 5), 2, (5, 6))


def test_timeline_warn_charge_recover_and_cooldown():
    charge = MedusaCharge()
    action = charge.begin((5, 5), 3, (14, 6), (), (45, 31), (), 100)
    assert action.phase(100) == "warning"
    assert action.phase(100 + WARNING_SECONDS - .001) == "warning"
    assert action.phase(action.charge_at) == "charge"
    assert action.phase(action.impact_end) == "recovery"
    assert action.phase(action.ends_at) == "done"
    assert action.position(action.charge_at + CHARGE_SECONDS / 2) == pytest.approx((7, 5))
    assert action.position(action.impact_end) == (9, 5)
    assert charge.tick(action.charge_at)[2] is True
    assert charge.tick(action.charge_at + .02)[2] is False
    assert charge.tick(action.impact_end)[3] is True
    assert charge.tick(action.impact_end + .02)[3] is False
    assert not charge.ready(action.impact_end)
    charge.finish()
    assert not charge.ready(100 + COOLDOWN_SECONDS - .01)
    assert charge.ready(100 + COOLDOWN_SECONDS)


@pytest.mark.parametrize("fps", [30, 60, 120])
@pytest.mark.parametrize("players", [1, 2])
def test_1p_2p_charge_deals_existing_body_damage_once_at_all_fps(
        monkeypatch, players, fps):
    game, boss, clock = fight(monkeypatch, players=players)
    assert game._tick_boss_charge(clock.now)
    action = boss.charge.action
    assert action.destination == (9, 5)
    hp_before = (
        (game.player_health,) if players == 1 else
        (game.player_health_p1, game.player_health_p2)
    )
    for frame in range(1, int((WARNING_SECONDS + CHARGE_SECONDS + RECOVERY_SECONDS + .1) * fps) + 1):
        clock.now = 100 + frame / fps
        game._tick_boss_charge(clock.now)
        assert not game._resolve_boss_body_contact(clock.now) or boss.charge.action is None
    assert boss.charge.action is None
    assert (boss.x, boss.y) == (9, 5)
    hp_after = (
        (game.player_health,) if players == 1 else
        (game.player_health_p1, game.player_health_p2)
    )
    assert hp_after == tuple(hp - BOSS_BODY_DAMAGE for hp in hp_before)
    assert game.lives == 3
    event_types = [e["type"] for e in game.combat_events]
    assert event_types.count("boss_charge_warning") == 1
    assert event_types.count("boss_charge_started") == 1
    assert event_types.count("boss_charge_hit") == players
    assert event_types.count("boss_charge_impact") == 1
    assert event_types.count("boss_charge_recovered") == 1
    assert event_types.count("boss_body_contact") == 0


def test_charge_cannot_hit_during_recovery_when_a_new_head_enters(monkeypatch):
    game, boss, clock = fight(monkeypatch, players=2)
    game.snake2 = [(35, 25)]
    assert game._tick_boss_charge(clock.now)
    action = boss.charge.action
    clock.now = action.impact_end + .01
    game._tick_boss_charge(clock.now)
    assert game.player_health_p2 == 100
    game.snake2 = [(10, 6)]  # enters now but charge finished moving
    clock.now += .02
    game._tick_boss_charge(clock.now)
    assert game.player_health_p2 == 100
    assert sum(e["type"] == "boss_charge_hit" for e in game.combat_events) == 1


def test_low_fps_jump_over_full_motion_still_hits(monkeypatch):
    game, boss, clock = fight(monkeypatch, players=1)
    game.snake = [(11, 6)]  # only the far end of four-tile movement
    game._tick_boss_charge(clock.now)
    action = boss.charge.action
    clock.now = action.impact_end + .15  # no intermediate game updates
    assert game._tick_boss_charge(clock.now)
    assert game.player_health == 100 - BOSS_BODY_DAMAGE
    assert boss.charge.action is action


def test_two_player_lethal_impact_consumes_one_shared_life(monkeypatch):
    game, boss, clock = fight(monkeypatch, players=2)
    game.player_health_p1 = 5
    game.player_health_p2 = 5
    game._tick_boss_charge(clock.now)
    clock.now = boss.charge.action.impact_end + .01
    game._tick_boss_charge(clock.now)
    assert game.lives == 2
    assert game.player_health_p1 == game.player_health_p2 == 100
    assert game.respawn.active
    assert boss.charge.action is None
    assert sum(e["type"] == "boss_charge_hit" for e in game.combat_events) == 2


def test_warning_is_real_and_hitbox_matches_boss_sprite(monkeypatch):
    game, boss, clock = fight(monkeypatch)
    original_sprite = boss.image
    original_art = boss.art_asset
    rect = boss.get_hitbox().copy()
    assert game._tick_boss_charge(clock.now)
    action = boss.charge.action
    image = pygame.Surface((GRID_WIDTH * GRID_SIZE, GRID_HEIGHT * GRID_SIZE),
                           pygame.SRCALPHA)
    draw_medusa_charge(image, action, clock.now + .3, GRID_SIZE, boss.size)
    assert image.get_bounding_rect().width > 0
    assert boss.get_hitbox() == rect
    clock.now = action.charge_at + CHARGE_SECONDS / 2
    px, py = boss._visual_position(clock.now)
    assert (px, py) == pytest.approx((7, 5))
    assert boss.get_hitbox().topleft == (7 * GRID_SIZE, 5 * GRID_SIZE)
    boss.draw(image)
    assert boss.image is original_sprite
    assert boss.art_asset == original_art


@pytest.mark.parametrize("interruption", ["pause", "editor", "respawn", "phase", "disable"])
def test_interruptions_remove_live_dash_without_ghost_hitbox(monkeypatch, interruption):
    game, boss, clock = fight(monkeypatch)
    game._tick_boss_charge(clock.now)
    clock.now = boss.charge.action.charge_at + .05
    game._tick_boss_charge(clock.now)
    if interruption == "pause":
        game.set_state(GameState.PAUSE)
    elif interruption == "editor":
        game._open_level_editor()
    elif interruption == "respawn":
        game._begin_respawn()
    elif interruption == "phase":
        stage = boss.phases.observe_health(int(boss.max_health * .69), clock.now)
        assert stage == 2
        game._announce_boss_phase(boss, stage, clock.now)
    else:
        boss.set_ai_preview(False)
    assert boss.charge.action is None
    assert boss.get_hitbox().size == (boss.size * GRID_SIZE,) * 2
    assert 5 <= boss.x <= 9
    assert boss.charge.next_ready_at > clock.now


def test_hidden_target_other_bosses_and_swipe_never_charge(monkeypatch):
    game, boss, clock = fight(monkeypatch)
    boss.eyes.reading = MedusaReading(
        "SEARCHING", 1, (14, 6), (14, 6), "memory",
    )
    assert not game._tick_boss_charge(clock.now)
    assert boss.charge.action is None
    boss.eyes.reading = MedusaReading(
        "VISIBLE", 1, (14, 6), (14, 6), "direct",
    )
    assert game._tick_boss_charge(clock.now)
    assert not game._tick_medusa_volley(clock.now)
    assert boss.tactics.volley is None
    assert boss.update(clock.now + .2) is None
    boss.set_ai_preview(False)
    assert not game._tick_boss_charge(clock.now + 10)
    assert boss.charge.action is None
