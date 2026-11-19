"""Boss Phases A: 70/35% HP, unique identities, safe 1P/2P transitions."""
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

from modules.boss_phases import (
    BossPhases, PHASE_TUNINGS, PHASE_2_HP, PHASE_3_HP,
    RECOVERY_SECONDS, WARNING_SECONDS, hp_stage,
)
from modules.boss_medusa import MedusaReading
from modules.boss_tactics import MedusaTactics
from modules.boss_defense import MedusaDefense
from modules.boss_swipe import MedusaSwipe
from modules import game as game_module
from modules.enums import GameState
from modules.game import Boss, Boss2, Game


def test_exact_hp_thresholds_are_level_independent_and_one_time():
    assert (PHASE_2_HP, PHASE_3_HP) == (0.70, 0.35)
    assert hp_stage(100, 100) == 1
    assert hp_stage(71, 100) == 1
    assert hp_stage(70, 100) == 2
    assert hp_stage(36, 100) == 2
    assert hp_stage(35, 100) == 3

    phase = BossPhases("hunter", 100)
    assert phase.observe_health(100, 1) is None
    assert phase.observe_health(70, 2) == 2
    assert phase.warning_active(2 + WARNING_SECONDS - .01)
    assert phase.advance(2 + WARNING_SECONDS - .01) is None
    assert phase.advance(2 + WARNING_SECONDS) == 2
    assert phase.advance(2 + WARNING_SECONDS + 1) is None
    assert phase.observe_health(70, 5) is None
    assert phase.observe_health(35, 6) == 3
    assert phase.advance(6 + WARNING_SECONDS) == 3
    assert phase.observe_health(100, 10) is None  # healing cannot regress


def test_big_hit_crossing_two_thresholds_announces_each_stage_in_order():
    phase = BossPhases("medusa", 100)
    assert phase.observe_health(30, 10) == 2
    assert phase.observe_health(30, 10.1) is None
    assert phase.target_stage == 3
    assert phase.advance(11.2) == 2
    assert phase.observe_health(30, 11.21) == 3
    assert phase.advance(12.41) == 3
    assert phase.advance(15) is None


def test_phase_pause_restarts_warning_not_instant_stage_change():
    phase = BossPhases("guardian", 100)
    assert phase.observe_health(69, 10) == 2
    phase.cancel_warning()
    assert not phase.warning_active(1000)
    assert phase.advance(1000) is None
    assert phase.stage == 1
    assert phase.observe_health(69, 1000) == 2
    assert phase.warning_active(1000.1)
    assert phase.advance(1001.2) == 2


def test_each_boss_profile_has_unique_phase_emphasis():
    assert set(PHASE_TUNINGS) == {"hunter", "guardian", "medusa"}
    assert all(len(v) == 3 and v[0].move == 1 for v in PHASE_TUNINGS.values())
    hunter = PHASE_TUNINGS["hunter"][2]
    guard = PHASE_TUNINGS["guardian"][2]
    medusa = PHASE_TUNINGS["medusa"][2]
    assert hunter.projectile < guard.projectile
    assert hunter.swipe < 1 and guard.swipe == 1
    assert guard.shield < 1 and guard.aoe < 1
    assert medusa.frost < 1 and medusa.eye < 1


@pytest.mark.parametrize("boss_type,key,level", [
    (Boss, "hunter", 2),
    (Boss2, "guardian", 3),
    (Boss, "medusa", 1),
])
def test_tuning_never_changes_fixed_art_health_damage_or_classic_rules(
        boss_type, key, level):
    boss = boss_type(level, health_multiplier=1.5, profile_key=key)
    assert boss.max_health == boss.health
    art = boss.art_asset
    hitbox = boss.get_hitbox().copy()
    original = (boss.chase_speed, boss._aoe_interval, boss._projectile_interval)
    assert boss.phases.stage == 1
    boss.set_ai_preview(True)
    move_p1 = boss.chase_speed
    assert boss.phases.observe_health(int(boss.max_health * .65), 10) == 2
    assert boss.phases.advance(10 + WARNING_SECONDS) == 2
    boss.apply_phase_tuning()
    assert boss.chase_speed <= move_p1
    assert boss.art_asset == art
    assert boss.max_health >= boss.health
    assert boss.get_hitbox() == hitbox
    assert boss.tactics.DAMAGE == 10
    assert boss.defense.SHIELD_SECONDS == .8
    boss.set_ai_preview(False)
    assert boss.phases.stage == 1
    assert (boss.chase_speed, boss._aoe_interval, boss._projectile_interval) == original
    assert boss.tactics.COOLDOWN_SECONDS == MedusaTactics.COOLDOWN_SECONDS
    assert boss.defense.COOLDOWN_SECONDS == MedusaDefense.COOLDOWN_SECONDS
    assert boss.swipe.RECHARGE_SECONDS == MedusaSwipe.RECHARGE_SECONDS


def make_combat(monkeypatch, level=1, players=1):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(players)
    game.level = level
    game.start_boss_fight()
    game.boss.set_ai_preview(True)
    return game, game.boss, clock


@pytest.mark.parametrize("level,key", [(1, "medusa"), (2, "hunter"), (3, "guardian")])
def test_real_damage_event_only_announces_when_threshold_reached(
        monkeypatch, level, key):
    game, boss, clock = make_combat(monkeypatch, level)
    assert boss.profile_key == key
    assert not game.damage_boss(1, "special_damage_item", is_projectile=False)
    assert boss.phases.stage == 1
    assert boss.phases.pending_stage is None
    threshold_hp = int(boss.max_health * PHASE_2_HP)
    assert not game.damage_boss(boss.health - threshold_hp,
                                "special_damage_item", is_projectile=False)
    assert boss.health == threshold_hp
    assert boss.phases.pending_stage == 2
    assert boss.phases.warning_active(clock.now)
    assert boss.next_proj >= clock.now + WARNING_SECONDS + RECOVERY_SECONDS
    assert boss.next_aoe >= clock.now + WARNING_SECONDS + RECOVERY_SECONDS
    announcements = [e for e in game.combat_events if e["type"] == "boss_phase_warning"]
    assert len(announcements) == 1
    assert announcements[0]["boss"] == key and announcements[0]["phase"] == 2

    # No movement or new boss projectile/area attack during the warning,
    # even if normal cooldowns would otherwise be expired.
    boss.next_proj = clock.now - 1
    boss.next_aoe = clock.now - 1
    old_pos = (boss.x, boss.y)
    clock.now += .6
    assert boss.update(clock.now) is None
    assert (boss.x, boss.y) == old_pos
    game._tick_boss_phases(clock.now)
    assert boss.phases.stage == 1
    clock.now += .61
    game._tick_boss_phases(clock.now)
    assert boss.phases.stage == 2
    assert boss.phases.pending_stage is None
    active = [e for e in game.combat_events if e["type"] == "boss_phase_active"]
    assert len(active) == 1 and active[0]["phase"] == 2
    game._tick_boss_phases(clock.now + 3)
    assert len([e for e in game.combat_events
                if e["type"] == "boss_phase_active"]) == 1


def test_1p_2p_phase_changes_do_not_change_player_hp_or_lives(monkeypatch):
    for players in (1, 2):
        game, boss, clock = make_combat(monkeypatch, 1, players)
        before = (game.lives, game.player_health,
                  game.player_health_p1, game.player_health_p2)
        game.damage_boss(boss.health - int(boss.max_health * .32),
                         "special_damage_item", is_projectile=False)
        assert boss.phases.pending_stage == 2
        clock.now += WARNING_SECONDS
        game._tick_boss_phases(clock.now)
        assert boss.phases.stage == 2
        clock.now += WARNING_SECONDS
        game._tick_boss_phases(clock.now)
        assert boss.phases.pending_stage == 3
        clock.now += WARNING_SECONDS
        game._tick_boss_phases(clock.now)
        assert boss.phases.stage == 3
        assert before == (game.lives, game.player_health,
                          game.player_health_p1, game.player_health_p2)


def test_medusa_warning_cancels_pending_frost_and_prevents_surprise_cast(
        monkeypatch):
    game, boss, clock = make_combat(monkeypatch, level=1)
    boss.spawn_time = clock.now - 5
    boss.eyes.reading = MedusaReading(
        "VISIBLE", 1, (12, 12), (12, 12), "direct",
    )
    game._vision_blockers = frozenset()
    game._tick_medusa_volley(clock.now)
    assert boss.tactics.volley is not None
    clock.now += .1
    game.damage_boss(boss.health - int(boss.max_health * .7),
                     "special_damage_item", is_projectile=False)
    assert boss.tactics.volley is None
    assert boss.phases.pending_stage == 2
    assert not game._tick_medusa_volley(clock.now)
    assert boss.tactics.volley is None
    assert boss.tactics.next_cast_at >= boss.phases.warning_ends_at + RECOVERY_SECONDS


def test_pause_does_not_fast_forward_boss_phase_and_preview_off_cancels(
        monkeypatch):
    game, boss, clock = make_combat(monkeypatch)
    game.damage_boss(boss.health - int(boss.max_health * .7),
                     "special_damage_item", is_projectile=False)
    assert boss.phases.pending_stage == 2
    game.set_state(GameState.PAUSE)
    assert boss.phases.pending_stage is None
    clock.now += 100
    assert boss.phases.stage == 1
    game.set_state(GameState.BOSS_FIGHT)
    game._tick_boss_phases(clock.now)
    assert boss.phases.pending_stage == 2
    assert boss.phases.warning_active(clock.now)
    boss.set_ai_preview(False)
    game._tick_boss_phases(clock.now + 100)
    assert boss.phases.stage == 1
    assert boss.phases.pending_stage is None


def test_boss_phase_warning_visual_keeps_original_sprite_and_hitbox(
        monkeypatch):
    game, boss, clock = make_combat(monkeypatch)
    boss.x, boss.y = 10, 10
    boss._visual_from = boss._visual_to = (10, 10)
    boss._visual_step_start = clock.now
    before_art = boss.art_asset
    rect = boss.get_hitbox().copy()
    game.damage_boss(boss.health - int(boss.max_health * .7),
                     "special_damage_item", is_projectile=False)
    screen = pygame.Surface((1200, 900), pygame.SRCALPHA)
    boss.draw(screen)
    assert boss.get_hitbox() == rect
    assert boss.art_asset == before_art
    assert screen.get_bounding_rect().width > 0


def test_lethal_hit_never_adds_false_phase_or_extra_rewards(monkeypatch):
    game, boss, clock = make_combat(monkeypatch)
    assert game.damage_boss(boss.health, "player_fireball")
    assert game.boss is None
    assert not any(event["type"].startswith("boss_phase")
                   for event in game.combat_events)
