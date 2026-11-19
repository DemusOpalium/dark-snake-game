"""Wächter/Ritter Phase III: a telegraphed whole-map *magic* scan.

Only this profile may find a snake outside its normal visibility. Landing
remains governed by the original two-player no-telefrag rules and 1.1 s
destination preview; Classic and other bosses keep their vision limits.
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
from modules.boss_medusa import MedusaReading
from modules import game as game_module
from modules.enums import GameState
from modules.game import Game
from modules.boss_teleport import (
    BossTeleport, WORLD_SCAN_SECONDS, WARNING_SECONDS, SINK_SECONDS,
    world_scan_target, destination_is_safe, ABORT_VISUAL_SECONDS,
)


def prepared(monkeypatch, *, players=1, level=3, stage=3):
    now = game_module.time.time()
    clock = SimpleNamespace(now=now)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(players)
    game.level = level
    game.start_boss_fight()
    boss = game.boss
    game.enemy_ai_preview = True
    boss.set_ai_preview(True)
    boss.spawn_time = clock.now - 9
    boss.x, boss.y = (4, 4)
    boss._visual_from = boss._visual_to = (4, 4)
    boss._visual_step_start = clock.now
    boss.phases.stage = stage
    boss.phases.pending_stage = None
    boss.eyes.reading = MedusaReading()  # intentionally has NO line of sight
    game._vision_blockers = frozenset({(12, 12), (13, 12)})
    if players == 1:
        game.snake = [(GRID_WIDTH - 5, GRID_HEIGHT - 6)]
    else:
        game.snake1 = [(GRID_WIDTH - 5, GRID_HEIGHT - 6)]
        game.snake2 = [(GRID_WIDTH - 7, GRID_HEIGHT - 9)]
    return game, boss, clock


def test_mapwide_scan_target_is_deterministic_for_both_players():
    assert world_scan_target((5, 5), 3, []) is None
    assert world_scan_target((5, 5), 3, [(30, 20)]) == (30, 20)
    assert world_scan_target((5, 5), 3, [(30, 20), (7, 6)]) == (7, 6)


@pytest.mark.parametrize("players", [1, 2])
def test_guardian_phase3_scans_entire_map_without_line_of_sight(
        monkeypatch, players):
    game, boss, clock = prepared(monkeypatch, players=players)
    assert boss.profile_key == "guardian"
    assert boss.teleport.style == "tunnel"
    assert not boss.eyes.reading.actionable
    assert game._tick_boss_teleport(clock.now)
    assert boss.teleport.scanning()
    assert boss.teleport.action is None
    assert boss.update(clock.now + .2) is None
    assert (boss.x, boss.y) == (4, 4)
    assert not game._resolve_boss_body_contact(clock.now)
    assert len([e for e in game.combat_events
                if e["type"] == "boss_world_scan_warning"]) == 1
    assert not boss.teleport.scan_complete(clock.now + WORLD_SCAN_SECONDS - .01)
    clock.now += WORLD_SCAN_SECONDS + .01
    assert game._tick_boss_teleport(clock.now)
    assert not boss.teleport.scanning()
    action = boss.teleport.action
    assert action is not None
    assert action.stage == 3 and action.style == "tunnel"
    assert action.origin == (4, 4)
    assert action.destination != action.origin
    assert boss.health == boss.max_health
    blocked, heads = game._boss_teleport_safety()
    assert destination_is_safe(
        action.destination, boss.size, (GRID_WIDTH, GRID_HEIGHT),
        blocked, heads,
    )
    warnings = [e for e in game.combat_events
                if e["type"] == "boss_teleport_warning"]
    assert len(warnings) == 1
    assert warnings[0]["global_scan"] is True
    # A SECOND, destination-specific warning is still mandatory.
    clock.now += .5
    assert boss.teleport.action.phase(clock.now) == "warning"
    assert boss.update(clock.now) is None


def test_global_scan_samples_player_only_after_warning_finishes(monkeypatch):
    game, boss, clock = prepared(monkeypatch, players=2)
    assert game._tick_boss_teleport(clock.now)
    # After casting the scan, the player moves to another corner.
    game.snake1 = [(GRID_WIDTH - 4, GRID_HEIGHT - 6)]
    game.snake2 = [(5, GRID_HEIGHT - 4)]
    clock.now += WORLD_SCAN_SECONDS + .01
    game._tick_boss_teleport(clock.now)
    completed = [e for e in game.combat_events
                 if e["type"] == "boss_world_scan_complete"]
    assert len(completed) == 1
    assert completed[0]["target"] == (5, GRID_HEIGHT - 4)
    assert game.boss.teleport.action is not None


@pytest.mark.parametrize("level,stage", [(3, 2), (2, 3), (1, 3)])
def test_phase2_and_other_personalities_do_not_gain_global_eyes(
        monkeypatch, level, stage):
    game, boss, clock = prepared(monkeypatch, level=level, stage=stage)
    assert not game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is None
    assert not boss.teleport.scanning()


def test_all_bosses_without_ki_remain_classic(monkeypatch):
    game, boss, clock = prepared(monkeypatch)
    boss.set_ai_preview(False)
    assert not game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is None
    assert not boss.teleport.scanning()


def test_scan_canceled_safely_on_pause_respawn_or_editor(monkeypatch):
    for reason in ("pause", "respawn", "editor", "disable"):
        game, boss, clock = prepared(monkeypatch)
        assert game._tick_boss_teleport(clock.now)
        assert boss.teleport.scanning()
        if reason == "pause":
            game.set_state(GameState.PAUSE)
        elif reason == "respawn":
            game._begin_respawn()
        elif reason == "editor":
            game._open_level_editor()
        else:
            boss.set_ai_preview(False)
        assert not boss.teleport.scanning()
        assert boss.teleport.action is None
        assert boss.get_hitbox().width == boss.size * GRID_SIZE


def test_occupied_arrival_closes_rift_visibly_without_damage_or_ghost_hitbox(
        monkeypatch):
    game, boss, clock = prepared(monkeypatch, players=2)
    game._tick_boss_teleport(clock.now)
    clock.now += WORLD_SCAN_SECONDS + .01
    game._tick_boss_teleport(clock.now)
    dest = boss.teleport.action.destination
    game.snake2 = [dest]
    clock.now += WARNING_SECONDS + SINK_SECONDS + .01
    assert not game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is None
    assert boss.teleport.abort_visual is not None
    assert boss.get_hitbox().width == boss.size * GRID_SIZE
    assert (boss.x, boss.y) == (4, 4)
    assert "boss_teleport_aborted" in [e["type"] for e in game.combat_events]
    surface = pygame.Surface((GRID_WIDTH * GRID_SIZE, GRID_HEIGHT * GRID_SIZE))
    boss.draw(surface)
    assert boss.teleport.abort_visual is not None
    clock.now += ABORT_VISUAL_SECONDS + .01
    boss.draw(surface)
    assert boss.teleport.abort_visual is None


def test_full_board_scan_draws_rings_without_changing_boss_sprite_or_hitbox(
        monkeypatch):
    game, boss, clock = prepared(monkeypatch)
    game._tick_boss_teleport(clock.now)
    image_before = boss.image
    hitbox = boss.get_hitbox().copy()
    surface = pygame.Surface((GRID_WIDTH * GRID_SIZE, GRID_HEIGHT * GRID_SIZE))
    surface.fill((0, 0, 0))
    clock.now += WORLD_SCAN_SECONDS * .75
    boss.draw(surface)
    assert boss.get_hitbox() == hitbox
    assert boss.image is image_before
    assert boss.art_asset == boss.profile.sprite
    # Search remains a visual and search event, not a new damage source.
    assert not any(e["type"] in ("boss_damage", "boss_defeated")
                   for e in game.combat_events)


def test_canceled_search_never_uses_magic_on_retry_in_phase2():
    tele = BossTeleport("guardian")
    assert not tele.begin_search(2, 10)
    assert tele.begin_search(3, 10)
    assert tele.scanning()
    tele.cancel(10.4)
    assert not tele.scanning()
    assert not tele.ready(3, 12)
    assert tele.ready(3, 13.4)
