import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

from config import GRID_HEIGHT, GRID_WIDTH, START_SPEED
from modules.enums import Direction
from modules.level_effects import CellEffects, DamageField, SLOW_PERCENTAGES, SlowField
from modules.level_playtest import (
    COLLISION_COLORS,
    PLAYER_COLORS,
    LevelPlaytest,
    draw_collision_overlay,
)


CENTER = GRID_WIDTH // 2, GRID_HEIGHT // 2
STEP = 1 / START_SPEED


@pytest.mark.parametrize("kind", ["WALL", "BARRIER"])
def test_wall_contact_stops_until_player_turns(kind):
    x, y = CENTER
    test = LevelPlaytest({(x + 2, y): kind}, 1, started_at=0)
    player, = test.players
    assert player.cell == CENTER
    assert player.direction == Direction.RIGHT

    test.update(STEP / 2)
    assert player.cell == CENTER
    test.update(STEP)
    assert player.cell == (x + 1, y)
    assert player.blocked is None

    for tick in range(2, 50):
        test.update(STEP * tick)
        assert player.cell == (x + 1, y)
        assert player.blocked == kind

    test.apply_actions(["p1_up"])
    test.update(STEP * 50)
    assert player.cell == (x + 1, y - 1)
    assert player.blocked is None


@pytest.mark.parametrize("blocked_player", [1, 2])
def test_two_players_move_and_turn_independently(blocked_player):
    x, y = CENTER
    blocked_y = y + 2 * (blocked_player - 1)
    test = LevelPlaytest({(x + 2, blocked_y): "WALL"}, 2, started_at=0)
    stopped = test.players[blocked_player - 1]
    moving = test.players[2 - blocked_player]
    moving_y = moving.cell[1]
    assert (test.players[0].cell, test.players[1].cell) == ((x, y), (x, y + 2))

    test.update(STEP * 2)
    assert stopped.cell == (x + 1, blocked_y)
    assert stopped.blocked == "WALL"
    assert moving.cell == (x + 2, moving_y)
    assert moving.blocked is None

    test.apply_actions([f"p{blocked_player}_down"])
    test.update(STEP * 3)
    assert stopped.cell == (x + 1, blocked_y + 1)
    assert stopped.blocked is None
    assert moving.cell == (x + 3, moving_y)


@pytest.mark.parametrize(
    ("direction", "steps", "edge", "wrapped"),
    [
        ("left", CENTER[0], (0, CENTER[1]), (GRID_WIDTH - 1, CENTER[1])),
        ("right", GRID_WIDTH - 1 - CENTER[0], (GRID_WIDTH - 1, CENTER[1]), (0, CENTER[1])),
        ("up", CENTER[1], (CENTER[0], 0), (CENTER[0], GRID_HEIGHT - 1)),
        ("down", GRID_HEIGHT - 1 - CENTER[1], (CENTER[0], GRID_HEIGHT - 1), (CENTER[0], 0)),
    ],
)
def test_wrap_targets_respect_collisions(direction, steps, edge, wrapped):
    free = LevelPlaytest({}, 1, started_at=0)
    blocked = LevelPlaytest({wrapped: "BARRIER"}, 1, started_at=0)
    for test in (free, blocked):
        test.apply_actions([f"p1_{direction}"])
        for tick in range(1, steps + 1):
            test.update(STEP * tick)
        assert test.players[0].cell == edge
        test.update(STEP * (steps + 1))

    assert free.players[0].cell == wrapped
    assert free.players[0].blocked is None
    assert blocked.players[0].cell == edge
    assert blocked.players[0].blocked == "BARRIER"


def test_spawns_are_deterministic_free_and_distinct():
    x, y = CENTER
    collisions = {(x, y): "WALL", (x, y + 2): "BARRIER"}
    first = LevelPlaytest(collisions, 2, started_at=0)
    second = LevelPlaytest(collisions, 2, started_at=0)
    cells = [player.cell for player in first.players]

    assert cells == [player.cell for player in second.players]
    assert len(set(cells)) == 2
    assert all(cell not in collisions for cell in cells)
    assert all(
        any(
            ((column + dx) % GRID_WIDTH, (row + dy) % GRID_HEIGHT) not in collisions
            for dx, dy in (direction.value for direction in Direction)
        )
        for column, row in cells
    )


def test_an_isolated_free_cell_cannot_start_a_playtest():
    collisions = {(x, y): "WALL" for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)
                  if (x, y) != CENTER}

    with pytest.raises(ValueError, match="Startfelder"):
        LevelPlaytest(collisions, 1, started_at=0)


def test_playtest_copies_collisions_and_does_not_change_the_draft():
    x, y = CENTER
    collisions = {(x + 2, y): "WALL"}
    original = collisions.copy()
    test = LevelPlaytest(collisions, 1, started_at=0)
    test.update(STEP)
    assert collisions == original
    collisions.clear()

    test.update(STEP * 2)

    assert test.players[0].cell == (x + 1, y)
    assert test.players[0].blocked == "WALL"
    assert collisions == {}


def test_overlay_marks_walls_barriers_and_both_snakes_without_erasing_tiles():
    size = 12
    board = pygame.Rect(5, 7, GRID_WIDTH * size, GRID_HEIGHT * size)
    screen = pygame.Surface((board.right, board.bottom))
    tile_color = (10, 20, 30)
    screen.fill(tile_color)
    collisions = {(0, 0): "WALL", (1, 0): "BARRIER"}
    test = LevelPlaytest(collisions, 2, started_at=0)

    draw_collision_overlay(screen, board, collisions)
    test.draw(screen, board)

    assert screen.get_at((board.left, board.top))[:3] == COLLISION_COLORS["WALL"]
    assert screen.get_at((board.left + size, board.top))[:3] == COLLISION_COLORS["BARRIER"]
    assert screen.get_at((board.left + size // 2, board.top + size // 2))[:3] == tile_color
    for player, color in zip(test.players, PLAYER_COLORS):
        column, row = player.cell
        pixel = (board.left + column * size + size // 2, board.top + row * size + 3)
        assert screen.get_at(pixel)[:3] == color


def test_players_share_a_free_cell_and_remain_visible():
    x, y = CENTER
    size = 18
    board = pygame.Rect(0, 0, GRID_WIDTH * size, GRID_HEIGHT * size)
    screen = pygame.Surface(board.size)
    test = LevelPlaytest({}, 2, started_at=0)
    test.apply_actions(("p1_down", "p2_up"))

    test.update(STEP)

    shared_cell = (x, y + 1)
    assert [player.cell for player in test.players] == [shared_cell, shared_cell]
    test.draw(screen, board)
    left, top = x * size, (y + 1) * size
    pixels = {
        screen.get_at((px, py))[:3]
        for px in range(left, left + size)
        for py in range(top, top + size)
    }
    assert set(PLAYER_COLORS) <= pixels


def test_damage_applies_on_entry_and_repeats_only_at_the_interval():
    x, y = CENTER
    test = LevelPlaytest({(x + 2, y): "WALL"}, 1, started_at=0, effects={
        (x + 1, y): CellEffects(damage=DamageField(amount=12, interval=0.5)),
    })
    player, = test.players

    test.update(STEP / 2)
    assert player.health == 100
    test.update(STEP)
    assert player.cell == (x + 1, y)
    assert player.health == 88
    for frame in range(8, 38):
        test.update(frame / 60)
    assert player.blocked == "WALL"
    assert player.health == 88
    test.update(STEP + 0.5)
    assert player.health == 76
    test.update(STEP + 0.5)
    assert player.health == 76
    test.update(STEP + 1.0)
    assert player.health == 64

    test.apply_actions(("p1_up",))
    test.update(STEP * 10)
    assert player.cell == (x + 1, y - 1)
    test.apply_actions(("p1_down",))
    test.update(STEP * 11)
    assert player.cell == (x + 1, y)
    assert player.health == 52


def test_damage_duration_limits_a_visit_and_restarts_on_reentry():
    x, y = CENTER
    test = LevelPlaytest({(x + 2, y): "BARRIER"}, 1, started_at=0, effects={
        (x + 1, y): CellEffects(damage=DamageField(amount=10, interval=0.5, duration=1.0)),
    })
    player, = test.players

    for tick in range(1, 20):
        test.update(STEP * tick)
    assert player.health == 80
    assert player.blocked == "BARRIER"

    test.apply_actions(("p1_up",))
    test.update(STEP * 20)
    test.apply_actions(("p1_down",))
    test.update(STEP * 21)
    assert player.cell == (x + 1, y)
    assert player.health == 70


def test_damage_repeat_is_cancelled_when_a_player_leaves_at_its_deadline():
    x, y = CENTER
    test = LevelPlaytest({}, 1, started_at=0, effects={
        (x + 1, y): CellEffects(damage=DamageField(amount=8, interval=STEP)),
    })
    player, = test.players

    test.update(STEP)
    assert player.health == 92
    test.update(STEP * 2)
    assert player.cell == (x + 2, y)
    assert player.health == 92
    test.update(STEP * 3)
    assert player.health == 92


@pytest.mark.parametrize("percent", SLOW_PERCENTAGES)
def test_slow_reduces_movement_on_the_occupied_cell_and_restores_it_on_exit(percent):
    x, y = CENTER
    test = LevelPlaytest({}, 1, started_at=0, effects={
        (x + 1, y): CellEffects(slow=SlowField(percent=percent)),
    })
    player, = test.players
    interval = STEP / (1 - percent / 100)

    test.update(STEP)
    assert player.cell == (x + 1, y)
    assert player.speed_percent == 100 - percent
    test.update(STEP + interval - 0.0001)
    assert player.cell == (x + 1, y)
    test.update(STEP + interval)
    assert player.cell == (x + 2, y)
    assert player.speed_percent == 100
    test.update(STEP * 2 + interval)
    assert player.cell == (x + 3, y)


def test_touching_another_slow_field_replaces_the_factor_without_stacking():
    x, y = CENTER
    test = LevelPlaytest({}, 1, started_at=0, effects={
        (x + 1, y): CellEffects(slow=SlowField(percent=75)),
        (x + 2, y): CellEffects(slow=SlowField(percent=50)),
    })
    player, = test.players

    test.update(STEP)
    assert player.speed_percent == 25
    test.update(STEP * 5)
    assert player.cell == (x + 2, y)
    assert player.speed_percent == 50
    test.update(STEP * 7)
    assert player.cell == (x + 3, y)
    assert player.speed_percent == 100


def test_combined_fields_and_knockout_are_independent_for_two_players():
    x, y = CENTER
    effects = {
        (x + 1, y): CellEffects(damage=DamageField(amount=60, interval=0.5), slow=SlowField(percent=75)),
        (x + 1, y + 2): CellEffects(damage=DamageField(amount=8)),
    }
    test = LevelPlaytest({(x + 2, y): "WALL"}, 2, started_at=0, effects=effects)
    first, second = test.players
    effects.clear()

    test.update(STEP)
    assert (first.health, first.speed_percent, second.health, second.speed_percent) == (40, 25, 92, 100)
    test.update(STEP * 5)
    assert first.cell == (x + 1, y)
    assert first.health == 0
    assert second.cell == (x + 5, y + 2)
    test.apply_actions(("p1_down", "p2_down"))
    test.update(STEP * 6)
    assert first.cell == (x + 1, y) and first.health == 0
    assert second.cell == (x + 5, y + 3) and second.health == 92
