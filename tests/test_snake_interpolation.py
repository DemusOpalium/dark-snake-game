import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

import modules.game as game_module
from config import GRID_HEIGHT, GRID_SIZE, GRID_WIDTH
from modules.enums import Direction
from modules.game import Game


FLOAT_TOLERANCE = 1e-9


def assert_positions(actual, expected):
    """Compare each pixel axis without masking meaningful movement errors."""
    assert len(actual) == len(expected)
    for (actual_x, actual_y), (expected_x, expected_y) in zip(actual, expected):
        assert actual_x == pytest.approx(expected_x, abs=FLOAT_TOLERANCE)
        assert actual_y == pytest.approx(expected_y, abs=FLOAT_TOLERANCE)


def assert_between_cells(position, start, target, grid_size=GRID_SIZE):
    """The renderer may only occupy the segment between confirmed cells."""
    for value, start_axis, target_axis in zip(position, start, target):
        lower = min(start_axis, target_axis) * grid_size
        upper = max(start_axis, target_axis) * grid_size
        assert lower - FLOAT_TOLERANCE <= value <= upper + FLOAT_TOLERANCE


def interpolation_game(players=1):
    game = Game(headless=True)
    game.start_game(players)
    game.speed = 5
    game.last_update_time = 10
    return game


def test_normal_movement_interpolates_previous_to_current_cell():
    game = interpolation_game()
    game.previous_snake = [(5, 5), (4, 5)]
    game.snake = [(6, 5), (5, 5)]
    positions = game.get_snake_render_positions(now=10.1)
    assert_positions(positions, [(5.5 * GRID_SIZE, 5 * GRID_SIZE),
                                 (4.5 * GRID_SIZE, 5 * GRID_SIZE)])
    assert positions[0][0] - positions[1][0] == pytest.approx(
        GRID_SIZE, abs=FLOAT_TOLERANCE)
    assert_between_cells(positions[0], (5, 5), (6, 5))


def test_direction_change_uses_only_confirmed_corner_positions():
    game = interpolation_game()
    game.previous_snake = [(5, 5), (4, 5)]
    game.snake = [(5, 4), (5, 5)]
    positions = game.get_snake_render_positions(now=10.1)
    assert_positions(positions, [
        (5 * GRID_SIZE, 4.5 * GRID_SIZE),
        (4.5 * GRID_SIZE, 5 * GRID_SIZE),
    ])
    assert_between_cells(positions[0], (5, 5), (5, 4))


def test_two_players_have_independent_interpolation_history():
    game = interpolation_game(2)
    game.previous_snake1, game.snake1 = [(1, 1)], [(2, 1)]
    game.previous_snake2, game.snake2 = [(8, 8)], [(8, 7)]
    p1_positions = game.get_snake_render_positions(1, now=10.1)
    p2_positions = game.get_snake_render_positions(2, now=10.1)
    assert_positions(p1_positions, [(1.5 * GRID_SIZE, GRID_SIZE)])
    assert_positions(p2_positions, [(8 * GRID_SIZE, 7.5 * GRID_SIZE)])
    assert_between_cells(p1_positions[0], (1, 1), (2, 1))
    assert_between_cells(p2_positions[0], (8, 8), (8, 7))


def test_gameplay_collision_stays_on_current_grid_position_during_render_move():
    game = interpolation_game()
    game.previous_snake, game.snake = [(4, 5)], [(5, 5)]
    game.boss = SimpleNamespace(
        get_rect=lambda: pygame.Rect(5 * GRID_SIZE, 5 * GRID_SIZE,
                                     GRID_SIZE, GRID_SIZE))
    assert game.get_snake_render_positions(now=10.05)[0][0] < 5 * GRID_SIZE
    assert game.check_boss_collision(game.snake[0])


def test_start_and_restart_reset_visual_history():
    game = interpolation_game()
    assert game.previous_snake == game.snake
    game.previous_snake = [(0, 0)]
    game.start_game(1)
    assert game.previous_snake == game.snake
    assert_positions(game.get_snake_render_positions(now=game.last_update_time), [
        (game.snake[0][0] * GRID_SIZE, game.snake[0][1] * GRID_SIZE)])


def test_render_interpolation_scales_with_view_grid_size(monkeypatch):
    game = interpolation_game()
    game.previous_snake, game.snake = [(1, 1)], [(2, 1)]
    for grid_size in (20, 30, 40):  # VIEW_SCALE 1.0, 1.5 und 2.0
        monkeypatch.setattr(game_module, "GRID_SIZE", grid_size)
        positions = game.get_snake_render_positions(now=10.1)
        assert_positions(positions, [(1.5 * grid_size, grid_size)])
        assert_between_cells(positions[0], (1, 1), (2, 1), grid_size)


@pytest.mark.parametrize("players,player", [(1, 1), (2, 1), (2, 2)])
@pytest.mark.parametrize("grid_size", [20, 30, 40])
@pytest.mark.parametrize(
    "direction,head,tail,destination",
    [
        (Direction.LEFT, (0, 4), (1, 4), (GRID_WIDTH - 1, 4)),
        (Direction.RIGHT, (GRID_WIDTH - 1, 4), (GRID_WIDTH - 2, 4), (0, 4)),
        (Direction.UP, (4, 0), (4, 1), (4, GRID_HEIGHT - 1)),
        (Direction.DOWN, (4, GRID_HEIGHT - 1), (4, GRID_HEIGHT - 2), (4, 0)),
    ],
)
def test_head_and_body_snap_on_actual_wrap(
    monkeypatch, players, player, grid_size, direction, head, tail, destination
):
    game = interpolation_game(players)
    game.items.clear()
    suffix = str(player) if players == 2 else ""
    setattr(game, f"snake{suffix}", [head, tail])
    setattr(game, f"next_direction{suffix}", direction)
    game._reset_snake_interpolation()
    monkeypatch.setattr(game_module, "GRID_SIZE", grid_size)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    now = game_module.time.time()
    monkeypatch.setattr(game_module.time, "time", lambda: now)
    game.last_update_time = now - 1.0

    game.update()
    assert getattr(game, f"snake{suffix}") == [destination, head]
    head_position, body_position = game.get_snake_render_positions(player, now=now + 0.05)
    assert_positions([head_position], [tuple(axis * grid_size for axis in destination)])
    assert_between_cells(body_position, tail, head, grid_size)
    assert body_position != tuple(axis * grid_size for axis in head)

    now += 1.0
    game.update()
    second_head = tuple(axis + step for axis, step in zip(destination, direction.value))
    assert getattr(game, f"snake{suffix}") == [second_head, destination]
    head_position, body_position = game.get_snake_render_positions(player, now=now + 0.05)
    assert_between_cells(head_position, destination, second_head, grid_size)
    assert_positions([body_position], [tuple(axis * grid_size for axis in destination)])


@pytest.mark.parametrize("players,player", [(1, 1), (2, 1), (2, 2)])
@pytest.mark.parametrize("direction", [Direction.LEFT, Direction.RIGHT, Direction.UP, Direction.DOWN])
def test_wrap_uses_regular_grid_ticks_and_draws_at_the_destination(monkeypatch, players, player, direction):
    # A 125 ms grid interval and 64 Hz frame clock give exact binary timestamps.
    start_time = 100.0
    clock = SimpleNamespace(now=start_time)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    monkeypatch.setattr(game_module.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(players)
    game.speed = 8
    game.items.clear()
    game.background.fill((15, 23, 35))

    dx, dy = direction.value
    edge = (
        GRID_WIDTH - 1 if dx > 0 else 0 if dx < 0 else 4,
        GRID_HEIGHT - 1 if dy > 0 else 0 if dy < 0 else 6,
    )
    before_edge = (edge[0] - dx, edge[1] - dy)
    destination = ((edge[0] + dx) % GRID_WIDTH, (edge[1] + dy) % GRID_HEIGHT)
    next_cell = (destination[0] + dx, destination[1] + dy)
    snake = [before_edge, (edge[0] - 2 * dx, edge[1] - 2 * dy)]
    suffix = str(player) if players == 2 else ""
    setattr(game, f"snake{suffix}", snake)
    setattr(game, f"snake_direction{suffix}", direction)
    setattr(game, f"next_direction{suffix}", direction)
    if players == 2:
        other = 3 - player
        companion = [(12, 12), (11, 12)]
        setattr(game, f"snake{other}", companion)
    game._reset_snake_interpolation()

    head_color = (51, 217, 133)
    head = pygame.Surface((GRID_SIZE, GRID_SIZE))
    head.fill(head_color)
    other_sprite = pygame.Surface((GRID_SIZE, GRID_SIZE))
    other_sprite.fill((147, 74, 203))
    game.settings[f"custom_head_p{player}"] = "wrap-head"
    monkeypatch.setattr(game.options_menu, "get_skin_image",
                        lambda _, name: head if name == "wrap-head" else other_sprite)
    arrival_rect = pygame.Rect(destination[0] * GRID_SIZE, destination[1] * GRID_SIZE,
                               GRID_SIZE, GRID_SIZE)

    steps = []
    previous_head = before_edge
    for frame in range(1, 29):
        clock.now = start_time + frame / 64
        game.update()
        if snake[0] != previous_head:
            steps.append((frame, snake[0], snake[1]))
            previous_head = snake[0]
        if 16 <= frame < 24:
            game.draw_game(include_hud=False)
            mask = pygame.mask.from_threshold(game.screen, head_color, (1, 1, 1, 255))
            assert mask.get_bounding_rects() == [arrival_rect]
        if players == 2:
            assert companion[0] == (12 + frame // 8, 12)

    assert steps == [(8, edge, before_edge), (16, destination, edge),
                     (24, next_cell, destination)]
    assert_positions(game.get_snake_render_positions(player, now=clock.now), [
        ((destination[0] + dx / 2) * GRID_SIZE, (destination[1] + dy / 2) * GRID_SIZE),
        (destination[0] * GRID_SIZE, destination[1] * GRID_SIZE),
    ])


@pytest.mark.parametrize("players", [1, 2])
def test_portal_resets_interpolation_even_for_an_adjacent_teleport(monkeypatch, players):
    game = interpolation_game(players)
    if players == 1:
        game.snake = [(4, 5), (3, 5)]
    else:
        game.snake1 = [(4, 5), (3, 5)]
        game.snake2 = [(6, 5), (7, 5)]
    game._reset_snake_interpolation()
    coordinates = iter([5, 5, 6, 6])

    def randint(minimum, maximum):
        if minimum == 0 and maximum in (GRID_WIDTH - 1, GRID_HEIGHT - 1):
            return next(coordinates)
        return minimum

    monkeypatch.setattr(game_module.random, "randint", randint)
    game.activate_portal("teleport")

    assert_positions(game.get_snake_render_positions(1, now=10), [
        (5 * GRID_SIZE, 5 * GRID_SIZE), (3 * GRID_SIZE, 5 * GRID_SIZE)])
    if players == 2:
        assert_positions(game.get_snake_render_positions(2, now=10), [
            (6 * GRID_SIZE, 6 * GRID_SIZE), (7 * GRID_SIZE, 5 * GRID_SIZE)])


@pytest.mark.parametrize("players", [1, 2])
def test_respawn_resets_interpolation_for_every_player(players):
    game = interpolation_game(players)
    if players == 1:
        game.snake = [(1, 1), (2, 1)]
    else:
        game.snake1 = [(1, 1), (2, 1)]
        game.snake2 = [(3, 2), (3, 1)]
    game._reset_snake_interpolation()
    game.lives = 2
    game.handle_self_collision()
    for player in range(1, players + 1):
        snake = game.snake if players == 1 else getattr(game, f"snake{player}")
        assert len(snake) == 1
        assert_positions(game.get_snake_render_positions(player, now=10), [
            tuple(axis * GRID_SIZE for axis in snake[0])])
