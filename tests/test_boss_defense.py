"""Boss Defense C: real sight, reaction delay and one-use shield."""
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

from modules.boss_defense import IncomingShot, MedusaDefense
from modules import game as game_module
from modules.game import Boss, Boss2, Game


def incoming(shot_id=1, pos=(13, 7), velocity=(-1, 0)):
    return IncomingShot(shot_id, pos, velocity)


def test_shield_requires_continuous_real_line_of_sight_and_reaction():
    d = MedusaDefense()
    shot = incoming()
    origin = (7, 7)
    assert not d.observe(origin, (1, 0), 3, [shot], (), 10.)
    assert not d.active(10.)
    assert not d.observe(origin, (1, 0), 3, [shot], (), 10.03)
    assert d.observe(origin, (1, 0), 3, [shot], (), 10.07)
    assert d.active(10.07)
    assert d.consume(10.08)
    assert not d.consume(10.09)
    assert not d.active(10.09)


def test_shield_wont_raise_through_wall_or_from_behind():
    for facing, blockers, shot in [
        ((1, 0), {(10, 7)}, incoming()),
        ((-1, 0), (), incoming()),
        ((1, 0), (), incoming(pos=(13, 7), velocity=(1, 0))),
        ((1, 0), (), incoming(pos=(20, 7), velocity=(-1, 0))),
    ]:
        d = MedusaDefense()
        assert not d.observe((7, 7), facing, 3, [shot], blockers, 10)
        assert not d.observe((7, 7), facing, 3, [shot], blockers, 11)
        assert not d.active(11)


def test_shield_requires_same_observed_projectile_and_enforces_cooldown():
    d = MedusaDefense()
    assert not d.observe((7, 7), (1, 0), 3, [incoming(1)], (), 10)
    assert not d.observe((7, 7), (1, 0), 3, [incoming(2)], (), 10.07)
    assert d.observe((7, 7), (1, 0), 3, [incoming(2)], (), 10.14)
    assert not d.observe((7, 7), (1, 0), 3, [incoming(2)], (), 12)
    d.cancel()
    assert not d.active(12)
    assert not d.observe((7, 7), (1, 0), 3, [incoming(2)], (), 13)
    assert not d.observe((7, 7), (1, 0), 3, [incoming(2)], (), 17.15)
    assert d.observe((7, 7), (1, 0), 3, [incoming(2)], (), 17.22)


@pytest.mark.parametrize("boss_type", [Boss, Boss2])
def test_opt_in_switch_clears_shield_and_classic_stays_original(boss_type):
    boss = boss_type(1)
    assert not boss.ai_preview
    assert not boss.defense.active(100)
    boss.set_ai_preview(True)
    boss.defense.observe((7, 7), (1, 0), 3, [incoming()], (), 10)
    boss.defense.observe((7, 7), (1, 0), 3, [incoming()], (), 10.07)
    assert boss.defense.active(10.08)
    boss.set_ai_preview(False)
    assert not boss.defense.active(10.08)
    assert boss.defense.candidate_id is None
    assert boss.defense.next_ready_at == float("-inf")


def setup_boss(monkeypatch):
    clock = SimpleNamespace(now=100.)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(1)
    game.start_boss_fight()
    boss = game.boss
    boss.x, boss.y = 5, 5
    boss.size = 3
    boss.facing = (1, 0)
    boss.spawn_time = clock.now - 5
    boss.set_ai_preview(True)
    return game, boss, clock


def test_game_scans_only_player_shots_and_consumes_shield_once(monkeypatch):
    game, boss, clock = setup_boss(monkeypatch)
    game.projectiles[:] = [
        {"pos": (13, 6.5), "dir": (-1, 0), "from_boss": True},
        {"pos": (13, 6.5), "dir": (-1, 0), "from_boss": False},
    ]
    # Swipe D is preferred when a side lane is free. Block both lanes so
    # this legacy regression continues to exercise the shield fallback.
    game._vision_blockers = {(6, 4), (6, 9)}
    initial = boss.health
    game._scan_boss_defense(clock.now)
    assert not boss.defense.active(clock.now)
    clock.now += .07
    game._scan_boss_defense(clock.now)
    assert boss.defense.active(clock.now)
    game.damage_boss(10, "player_projectile")
    assert boss.health == initial
    assert any(e["type"] == "boss_shield_blocked" for e in game.combat_events)
    game.damage_boss(10, "player_projectile")
    assert boss.health == initial - 10


def test_special_nonprojectile_damage_bypasses_shield(monkeypatch):
    game, boss, clock = setup_boss(monkeypatch)
    boss.defense.shield_until = clock.now + .7
    initial = boss.health
    game.damage_boss(1, "special_damage_item", is_projectile=False)
    assert boss.health == initial - 1
    assert boss.defense.active(clock.now)
    game.damage_boss(1, "player_fireball")
    assert boss.health == initial - 1
    assert not boss.defense.active(clock.now)


def test_shield_drawing_is_separate_from_logical_boss_hitbox(monkeypatch):
    game, boss, clock = setup_boss(monkeypatch)
    old_rect = boss.get_hitbox().copy()
    boss.defense.shield_until = clock.now + .7
    boss._visual_from = boss._visual_to = (boss.x, boss.y)
    boss._visual_step_start = clock.now
    surface = pygame.Surface((1000, 800), pygame.SRCALPHA)
    boss.draw(surface)
    assert boss.get_hitbox() == old_rect
    assert surface.get_bounding_rect().width > 0
    assert surface.get_at((old_rect.x - 6, old_rect.centery)).a > 0
