"""Safe Boss Teleport A in headless Windows/Pygame, 1P and 2P."""
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

from config import GRID_SIZE, GRID_WIDTH, GRID_HEIGHT
from modules import game as game_module
from modules.boss_medusa import MedusaReading
from modules.boss_teleport import (
    BossTeleport, TeleportAction, choose_destination, destination_is_safe,
    WARNING_SECONDS, SINK_SECONDS, EMERGE_SECONDS, RECOVERY_SECONDS,
)
from modules.boss_teleport_visual import COLORS, NAMES, draw_teleport_markers
from modules.enums import GameState
from modules.game import Boss, Game


def test_three_fixed_visual_styles_one_safe_movement_mechanic():
    assert {key: BossTeleport(key).style for key in ("hunter", "guardian", "medusa")} == {
        "hunter": "leap", "guardian": "tunnel", "medusa": "portal",
    }
    assert len(set(COLORS)) == len(set(NAMES)) == 3
    assert WARNING_SECONDS >= 1.0
    assert SINK_SECONDS >= .3
    assert EMERGE_SECONDS >= .3
    assert RECOVERY_SECONDS >= .5


def test_phase_boundaries_are_visible_and_never_skip_warning():
    action = TeleportAction((3, 3), (15, 12), 100, 2, "tunnel")
    assert action.phase(100) == "warning"
    assert action.phase(100 + WARNING_SECONDS - .001) == "warning"
    assert action.phase(100 + WARNING_SECONDS) == "sink"
    assert action.phase(100 + WARNING_SECONDS + SINK_SECONDS - .001) == "sink"
    assert action.phase(action.landing_time) == "emerge"
    assert action.phase(action.landing_time + EMERGE_SECONDS) == "recovery"
    assert action.phase(action.landing_time + EMERGE_SECONDS
                        + RECOVERY_SECONDS) == "done"
    assert action.progress(100 + WARNING_SECONDS) == 0
    assert action.progress(action.landing_time) == 0
    assert action.progress(action.landing_time + EMERGE_SECONDS) == 1


def test_controller_once_per_phase_and_cooldown_prevents_repeated_warps():
    controller = BossTeleport("medusa")
    assert not controller.ready(1, 100)
    assert controller.begin((4, 4), (18, 7), 2, 100)
    assert not controller.ready(2, 101)
    assert controller.needs_landing(100 + WARNING_SECONDS + SINK_SECONDS)
    controller.arrive(102)
    assert controller.used_stages == {2}
    assert controller.finish(103)
    assert not controller.ready(2, 999)
    assert not controller.ready(3, 110)
    assert controller.ready(3, 112)
    assert controller.begin((18, 7), (4, 12), 3, 112)
    controller.cancel(113)
    assert not controller.ready(3, 114)
    assert controller.ready(3, 116)


def test_safe_cell_checks_full_boss_footprint_and_both_player_heads():
    blockers = {(8, 8), (7, 5)}
    assert not destination_is_safe(
        (6, 6), 3, (25, 20), blockers, [(1, 1), (20, 15)],
    )
    assert not destination_is_safe(
        (7, 8), 3, (25, 20), blockers, [(1, 1)],
    )
    assert not destination_is_safe(
        (24, 12), 3, (25, 20), (), [(1, 1)],
    )
    assert not destination_is_safe(
        (15, 14), 3, (25, 20), (), [(17, 14)],  # inside footprint
    )
    assert not destination_is_safe(
        (15, 14), 3, (25, 20), (), [(20, 14)],  # only two cells' gap
    )
    assert destination_is_safe(
        (15, 14), 3, (25, 20), (), [(22, 14), (1, 1)],
    )


def test_no_target_or_no_safe_footprint_means_no_teleport():
    grid = (15, 15)
    assert choose_destination((0, 0), 3, grid, set(), [(5, 5)],
                              None, "medusa") is None
    assert choose_destination(
        (1, 1), 3, grid,
        {(x, y) for x in range(15) for y in range(15)},
        [(5, 5)], (5, 5), "guardian",
    ) is None


def arrange_fight(monkeypatch, *, players=1, level=1, stage=2):
    current = game_module.time.time()
    clock = SimpleNamespace(now=current)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(players)
    game.level = level
    game.start_boss_fight()
    boss = game.boss
    game.enemy_ai_preview = True
    boss.set_ai_preview(True)
    boss.spawn_time = clock.now - 6
    boss.x, boss.y = (3, 3)
    boss._visual_from = boss._visual_to = (3, 3)
    boss._visual_step_start = clock.now
    boss.phases.stage = stage
    game._vision_blockers = frozenset()
    if players == 1:
        game.snake = [(30, 20), (29, 20), (28, 20)]
    else:
        game.snake1 = [(30, 20), (29, 20), (28, 20)]
        game.snake2 = [(31, 22), (31, 23), (31, 24)]
    boss.eyes.reading = MedusaReading(
        "VISIBLE", 1, (29, 20), (29, 20), "direct",
    )
    return game, boss, clock


@pytest.mark.parametrize("players,level,style", [
    (1, 1, "portal"), (2, 1, "portal"), (1, 2, "leap"),
    (2, 3, "tunnel"),
])
def test_actual_boss_relocates_telegraphed_without_player_contact(
        monkeypatch, players, level, style):
    game, boss, clock = arrange_fight(
        monkeypatch, players=players, level=level,
    )
    original_image = boss.art_asset
    original_hp = boss.health
    original_size = boss.get_hitbox().size
    original_heads = tuple(game._player_heads_with_health())
    assert game._tick_boss_teleport(clock.now)
    action = boss.teleport.action
    assert action.style == style
    assert action.origin == (3, 3)
    assert action.destination != action.origin
    assert boss.get_hitbox().size == original_size
    blocked, heads = game._boss_teleport_safety()
    assert destination_is_safe(
        action.destination, boss.size, (GRID_WIDTH, GRID_HEIGHT),
        blocked, heads,
    )
    # No new boss shot, AoE or movement during the warning.
    assert boss.update(clock.now + .6) is None
    assert (boss.x, boss.y) == (3, 3)
    clock.now += WARNING_SECONDS + .1
    assert boss.teleport.hidden(clock.now)
    assert boss.get_hitbox().size == (0, 0)
    before = boss.health
    assert not game.damage_boss(10, "player_fireball")
    assert boss.health == before
    assert not game._resolve_boss_body_contact(clock.now)

    clock.now = action.landing_time + .01
    assert game._tick_boss_teleport(clock.now)
    assert boss.teleport.landed
    assert (boss.x, boss.y) == action.destination
    assert boss.get_hitbox().size == (0, 0)
    assert boss.update(clock.now) is None
    clock.now += EMERGE_SECONDS + .01
    assert not boss.teleport.hidden(clock.now)
    assert boss.teleport.waiting(clock.now)
    assert not game._resolve_boss_body_contact(clock.now)
    clock.now += RECOVERY_SECONDS + .01
    game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is None
    assert boss.get_hitbox().size == original_size
    assert boss.art_asset == original_image
    assert boss.health == original_hp
    assert tuple(game._player_heads_with_health()) == original_heads
    assert boss.teleport.used_stages == {2}
    event_types = [e["type"] for e in game.combat_events]
    assert event_types.count("boss_teleport_warning") == 1
    assert event_types.count("boss_teleport_arrived") == 1


def test_recheck_destination_after_1s_prevents_telefrag_if_player_moves(monkeypatch):
    game, boss, clock = arrange_fight(monkeypatch, players=2)
    game._tick_boss_teleport(clock.now)
    dest = boss.teleport.action.destination
    game.snake2 = [dest, (dest[0] - 1, dest[1])]
    clock.now += WARNING_SECONDS + SINK_SECONDS + .03
    assert not game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is None
    assert (boss.x, boss.y) == (3, 3)
    assert boss.get_hitbox().size == (boss.size * GRID_SIZE,) * 2
    assert not boss.teleport.used_stages
    assert any(e["type"] == "boss_teleport_aborted"
               for e in game.combat_events)


def test_classic_no_ki_and_no_sight_never_move_boss_magically(monkeypatch):
    game, boss, clock = arrange_fight(monkeypatch)
    boss.set_ai_preview(False)
    assert not game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is None
    boss.set_ai_preview(True)
    boss.eyes.reading = MedusaReading()  # no wall-vision or omniscience
    assert not game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is None


def test_boss_phase_warning_preempts_teleport_without_phase_overlap(monkeypatch):
    game, boss, clock = arrange_fight(monkeypatch)
    assert game._tick_boss_teleport(clock.now)
    assert boss.teleport.action is not None
    stage = boss.phases.observe_health(int(boss.max_health * .34), clock.now)
    assert stage == 3
    game._announce_boss_phase(boss, 3, clock.now)
    assert boss.teleport.action is None
    assert boss.phases.warning_active(clock.now)
    assert boss.phases.stage == 2


@pytest.mark.parametrize("interrupt", ["pause", "editor", "respawn", "disable"])
def test_interruptions_cancel_half_finished_burrow_safely(monkeypatch, interrupt):
    game, boss, clock = arrange_fight(monkeypatch)
    game._tick_boss_teleport(clock.now)
    clock.now += WARNING_SECONDS + .02
    assert boss.teleport.hidden(clock.now)
    if interrupt == "pause":
        game.set_state(GameState.PAUSE)
    elif interrupt == "editor":
        game._open_level_editor()
    elif interrupt == "respawn":
        game._begin_respawn()
    else:
        boss.set_ai_preview(False)
    assert boss.teleport.action is None
    assert boss.get_hitbox().size == (boss.size * GRID_SIZE,) * 2
    assert (boss.x, boss.y) == (3, 3)


def test_unmodified_fixed_boss_sprite_and_visual_markers(monkeypatch):
    game, boss, clock = arrange_fight(monkeypatch, level=3)
    game._tick_boss_teleport(clock.now)
    action = boss.teleport.action
    image_before = boss.image
    surface = pygame.Surface((1350, 930), pygame.SRCALPHA)
    draw_teleport_markers(surface, action, clock.now, GRID_SIZE, boss.size)
    assert surface.get_bounding_rect().width > 0
    boss.draw(surface)
    assert boss.image is image_before
    assert boss.art_asset == boss.profile.sprite
