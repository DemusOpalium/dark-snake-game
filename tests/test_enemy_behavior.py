"""Enemy Vision B: safe, opt-in movement reactions and future-age profiles."""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from modules.enemy_behavior import (
    BehaviorProfile, FROST_PROTOTYPE_BEHAVIORS,
    movement_intention, permitted_step, reaction_state,
)
from modules.enemy_vision import VisionResult, VisionProfile, VisionSensor
from modules.enemies import NormalEnemy
from modules.bolbu_enemy import BolbuEnemy
from modules.game import Game
from modules import game as game_module


@pytest.mark.parametrize("state,result,action", [
    ("PATROL", VisionResult(), "CHASE"),
    ("CHASE", VisionResult("VISIBLE", 1, (8, 5), 10.0), "CHASE"),
    ("SEARCH", VisionResult("SEARCHING", 1, (8, 5), 10.0), "CHASE"),
    ("PATROL", VisionResult(), "GUARD"),
    ("GUARD", VisionResult("VISIBLE", 1, (8, 5), 10.0), "GUARD"),
])
def test_vision_signal_drives_behavior_state_without_creating_damage(
        state, result, action):
    assert reaction_state(result, (5, 5), BehaviorProfile(action)) == state


def test_lost_target_investigated_only_within_real_vision_memory():
    eyes = VisionSensor(VisionProfile(fov_degrees=90, radius_cells=6,
                                      scan_interval=.1, memory_seconds=1.2))
    first = eyes.observe((5, 5), (1, 0), [(1, (8, 5))], frozenset(), now=100)
    assert reaction_state(first, (5, 5), BehaviorProfile()) == "CHASE"
    lost = eyes.observe((5, 5), (1, 0), [], frozenset(), now=100.2)
    assert reaction_state(lost, (5, 5), BehaviorProfile()) == "SEARCH"
    assert movement_intention((5, 5), lost.last_known_cell, "SEARCH",
                              frozenset(), (45, 31)) == (1, 0)
    forgotten = eyes.observe((5, 5), (1, 0), [], frozenset(), now=101.5)
    assert reaction_state(forgotten, (5, 5), BehaviorProfile()) == "PATROL"


@pytest.mark.parametrize("position,target,expected", [
    ((5, 5), (9, 5), (1, 0)),
    ((5, 5), (5, 2), (0, -1)),
    ((5, 5), (8, 8), (1, 1)),
    ((5, 5), (5, 5), (0, 0)),
])
def test_chase_makes_a_bounded_grid_move_toward_last_confirmed_target(
        position, target, expected):
    step = movement_intention(position, target, "CHASE", frozenset(), (45, 31))
    assert step == expected
    assert max(map(abs, step)) <= 1


def test_preview_never_phases_through_solid_walls_or_diagonal_corners():
    start = (5, 5)
    wall = {(6, 5)}
    assert not permitted_step(start, (1, 0), wall, (45, 31))
    assert not permitted_step(start, (1, 1), wall, (45, 31))
    step = movement_intention(start, (9, 5), "CHASE", wall, (45, 31))
    assert step not in ((1, 0), (1, 1), (1, -1))
    assert permitted_step(start, step, wall, (45, 31))
    assert not permitted_step((0, 0), (-1, 0), set(), (45, 31))
    assert not permitted_step((44, 30), (1, 1), set(), (45, 31))


def test_frostage_three_candidate_profiles_are_inert_until_age_spawns_exist():
    assert set(FROST_PROTOTYPE_BEHAVIORS) == {
        "frostage_eisskelett", "frostage_frostwisp", "frostage_frosttitan",
    }
    sight = VisionResult("VISIBLE", 1, (6, 5), 1)
    assert reaction_state(sight, (5, 5),
                          FROST_PROTOTYPE_BEHAVIORS["frostage_eisskelett"]) == "CHASE"
    assert reaction_state(sight, (5, 5),
                          FROST_PROTOTYPE_BEHAVIORS["frostage_frostwisp"]) == "RETREAT"
    assert movement_intention((5, 5), (6, 5), "RETREAT",
                              frozenset(), (45, 31)) == (-1, 0)
    assert reaction_state(sight, (5, 5),
                          FROST_PROTOTYPE_BEHAVIORS["frostage_frosttitan"]) == "GUARD"
    assert movement_intention((5, 5), (6, 5), "GUARD",
                              frozenset(), (45, 31)) == (0, 0)


@pytest.mark.parametrize("bad", [
    {"visible_action": "TELEPORT"}, {"chase_speed": 0},
    {"chase_speed": 4}, {"retreat_distance": -1},
])
def test_bad_profiles_rejected_before_use(bad):
    with pytest.raises(ValueError):
        BehaviorProfile(**bad)


def _ready_game(players=1):
    game = Game(headless=True)
    game.start_game(players)
    game.settings["enemy_spawn_rate"] = 0
    game.last_update_time = time.time()
    game.respawn_invincible_until = float("inf")
    return game


def _fresh_enemy():
    enemy = NormalEnemy()
    enemy.x, enemy.y, enemy.facing = 5, 5, (1, 0)
    enemy.speed = 2
    enemy.last_move = time.time() - 3
    enemy.sprint_active = False
    enemy.sprint_chance = 0
    return enemy


def test_real_classic_singleplayer_movement_follows_vision_only_when_opted_in():
    game = _ready_game()
    game.snake = [(9, 5)]
    enemy = _fresh_enemy()
    game.enemies = [enemy]
    assert not game.enemy_ai_preview
    game.enemy_ai_preview = True
    before = (game.player_health, game.score, game.lives)
    game.update()
    assert enemy.eyes.result.visible
    assert enemy.behavior_state == "CHASE"
    assert (enemy.x, enemy.y) == (6, 5)
    assert (game.player_health, game.score, game.lives) == before


def test_two_player_reaction_chases_selected_nearest_head_not_always_player_one():
    game = _ready_game(2)
    game.snake1, game.snake2 = [(9, 5)], [(5, 7)]
    enemy = _fresh_enemy()
    enemy.eyes.profile = VisionProfile(fov_degrees=360)
    game.enemies = [enemy]
    game.enemy_ai_preview = True
    game.update()
    assert enemy.eyes.result.target_player == 2
    assert enemy.behavior_state == "CHASE"
    assert (enemy.x, enemy.y) == (5, 6)


def test_bolbu_preview_guards_while_visible_and_legacy_shot_logic_remains():
    game = _ready_game()
    game.snake = [(8, 5)]
    enemy = BolbuEnemy()
    enemy.x, enemy.y, enemy.facing = 5, 5, (1, 0)
    enemy.last_move = time.time() - 2
    enemy.sprint_chance = 0
    enemy.last_shot = enemy.last_dice = time.time()
    game.enemies = [enemy]
    game.enemy_ai_preview = True
    game.update()
    assert enemy.eyes.result.visible
    assert enemy.behavior_state == "GUARD"
    assert (enemy.x, enemy.y) == (5, 5)
    assert not game.enemy_projectiles


def test_vision_preview_respects_blockers_and_requires_actual_sight():
    game = _ready_game()
    game._vision_blockers = frozenset({(6, 5)})
    game.snake = [(9, 5)]
    enemy = _fresh_enemy()
    game.enemies = [enemy]
    game.enemy_ai_preview = True
    game.update()
    assert not enemy.eyes.result.visible
    assert enemy.behavior_state == "PATROL"
    assert (enemy.x, enemy.y) not in game._vision_blockers


def test_admin_pause_stops_all_ai_and_reset_disables_preview():
    game = _ready_game()
    game.snake = [(9, 5)]
    enemy = _fresh_enemy()
    game.enemies = [enemy]
    assert "aktiviert" in game.admin_panel.toggle_enemy_ai()
    game.admin_panel.active = True
    start = (enemy.x, enemy.y)
    game.update()
    assert (enemy.x, enemy.y) == start
    assert enemy.eyes.result.kind == "UNAWARE"
    game.admin_panel.active = False
    game.update()
    assert enemy.behavior_state == "CHASE"
    assert (enemy.x, enemy.y) != start
    game.reset_game()
    assert not game.enemy_ai_preview


def test_behavior_preview_off_preserves_classic_random_walk(monkeypatch):
    game = _ready_game()
    game.snake = [(9, 5)]
    enemy = _fresh_enemy()
    enemy.eyes.result = VisionResult("VISIBLE", 1, (9, 5), time.time())
    monkeypatch.setattr("modules.enemies.random.choice", lambda _: -1)
    # Classic old code chooses one independent random dx,dy each.
    game.enemies = [enemy]
    game.update()
    assert not enemy.behavior_enabled
    assert enemy.behavior_state == "PATROL"
    assert (enemy.x, enemy.y) == (4, 4)


def test_developer_overlay_labels_behavior_without_changing_player_hud():
    game = _ready_game()
    enemy = _fresh_enemy()
    enemy.behavior_state = "CHASE"
    enemy.behavior_enabled = True
    enemy.eyes.result = VisionResult("VISIBLE", 1, (7, 5), time.time())
    game.enemy_ai_preview = True
    game.screen.fill((0, 0, 0))
    game._draw_enemy_sight_debug(enemy)
    assert game.screen.get_at((enemy.x * 30 + 15, enemy.y * 30 + 15))[:3] != (0, 0, 0)
