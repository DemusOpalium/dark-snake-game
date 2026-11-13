"""An isolated, repeatable grid playtest for World Studio walls."""

from dataclasses import dataclass
from time import monotonic

import pygame

from config import GRID_HEIGHT, GRID_WIDTH, START_SPEED
from modules.enums import Direction


COLLISION_COLORS = {
    "WALL": (246, 151, 84),
    "BARRIER": (106, 184, 244),
}
PLAYER_COLORS = ((117, 237, 159), (205, 151, 249))
MAX_CATCH_UP_STEPS = 4


def _next_cell(cell, direction):
    x, y = cell
    dx, dy = direction.value
    return (x + dx) % GRID_WIDTH, (y + dy) % GRID_HEIGHT


def _spawn_cells(collisions, player_count):
    """Choose free, distinct cells with at least one available direction."""
    available = {(x, y) for y in range(GRID_HEIGHT) for x in range(GRID_WIDTH)
                 if (x, y) not in collisions}
    candidates = {cell for cell in available
                  if any(_next_cell(cell, direction) in available for direction in Direction)}
    if len(candidates) < player_count:
        raise ValueError("Für den Wandtest fehlen freie Startfelder mit einem freien Nachbarfeld.")

    chosen = []
    center_x, center_y = GRID_WIDTH // 2, GRID_HEIGHT // 2
    for player in range(player_count):
        preferred_y = center_y + player * 2
        cell = min(candidates, key=lambda cell: (
            abs(cell[0] - center_x) + abs(cell[1] - preferred_y), cell[1], cell[0],
        ))
        chosen.append(cell)
        candidates.remove(cell)
    return chosen


def _cell_rect(board_rect, cell):
    width = board_rect.width // GRID_WIDTH
    height = board_rect.height // GRID_HEIGHT
    x, y = cell
    return pygame.Rect(board_rect.x + x * width, board_rect.y + y * height, width, height)


def draw_collision_overlay(surface, board_rect, collisions):
    """Mark authored walls independently of the tiles underneath them."""
    for cell, kind in collisions.items():
        rect = _cell_rect(board_rect, cell)
        pygame.draw.rect(surface, COLLISION_COLORS[kind], rect, width=2)


@dataclass(slots=True)
class PlaytestPlayer:
    cell: tuple[int, int]
    direction: Direction = Direction.RIGHT
    blocked: str | None = None


class LevelPlaytest:
    """Test only movement and collisions, with the classic one-cell start."""

    def __init__(self, collisions, player_count, *, started_at=None):
        if player_count not in (1, 2):
            raise ValueError("Der Wandtest unterstützt einen oder zwei Spieler.")
        self._collisions = dict(collisions)
        self.player_count = player_count
        self.players = tuple(PlaytestPlayer(cell) for cell in _spawn_cells(self._collisions, player_count))
        self.step_seconds = 1 / START_SPEED
        start = monotonic() if started_at is None else started_at
        self._next_step = start + self.step_seconds

    def apply_actions(self, actions):
        for index, player in enumerate(self.players, 1):
            for direction in Direction:
                if f"p{index}_{direction.name.lower()}" in actions:
                    player.direction = direction

    def update(self, now=None):
        now = monotonic() if now is None else now
        for _ in range(MAX_CATCH_UP_STEPS):
            if now < self._next_step:
                return
            for player in self.players:
                target = _next_cell(player.cell, player.direction)
                player.blocked = self._collisions.get(target)
                if player.blocked is None:
                    player.cell = target
            self._next_step += self.step_seconds
        if self._next_step <= now:
            self._next_step = now + self.step_seconds

    def draw(self, surface, board_rect):
        """Draw the two snakes as distinct directional markers over the map."""
        shared_cell = self.player_count == 2 and self.players[0].cell == self.players[1].cell
        for index, (player, color) in enumerate(zip(self.players, PLAYER_COLORS)):
            rect = _cell_rect(board_rect, player.cell).inflate(-4, -4)
            if shared_cell:
                rect.width //= 2
                rect.x += index * rect.width
            pygame.draw.rect(surface, color, rect, border_radius=3)
            dx, dy = player.direction.value
            front = (rect.centerx + dx * rect.width // 3, rect.centery + dy * rect.height // 3)
            pygame.draw.line(surface, (28, 32, 37), rect.center, front, width=2)
