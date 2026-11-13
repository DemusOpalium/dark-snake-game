"""An isolated, repeatable grid playtest for World Studio fields."""

from dataclasses import dataclass
from time import monotonic

import pygame

from config import GRID_HEIGHT, GRID_WIDTH, START_SPEED
from modules.enums import Direction
from modules.level_effects import EffectCells


COLLISION_COLORS = {
    "WALL": (246, 151, 84),
    "BARRIER": (106, 184, 244),
}
PLAYER_COLORS = ((117, 237, 159), (205, 151, 249))
MAX_CATCH_UP_STEPS = 4
MAX_HEALTH = 100
TIME_TOLERANCE = 1e-9


def _next_cell(cell, direction):
    x, y = cell
    dx, dy = direction.value
    return (x + dx) % GRID_WIDTH, (y + dy) % GRID_HEIGHT


def _spawn_cells(collisions, effects, player_count):
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
            cell in effects, abs(cell[0] - center_x) + abs(cell[1] - preferred_y), cell[1], cell[0],
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
    next_step: float
    direction: Direction = Direction.RIGHT
    blocked: str | None = None
    health: int = MAX_HEALTH
    slow_percent: int = 0
    entered_cell_at: float = 0.0
    next_damage: float | None = None

    @property
    def speed_percent(self):
        return 100 - self.slow_percent


class LevelPlaytest:
    """Test authored collision and effect fields with a one-cell start."""

    def __init__(self, collisions, player_count, *, started_at=None, effects: EffectCells | None = None):
        if player_count not in (1, 2):
            raise ValueError("Der Wandtest unterstützt einen oder zwei Spieler.")
        self._collisions = dict(collisions)
        self._effects = dict(effects or {})
        self.player_count = player_count
        self.step_seconds = 1 / START_SPEED
        start = monotonic() if started_at is None else started_at
        self.players = tuple(PlaytestPlayer(cell, start)
                             for cell in _spawn_cells(self._collisions, self._effects, player_count))
        for player in self.players:
            self._enter_cell(player, start)
            player.next_step = start + self._step_interval(player)

    def apply_actions(self, actions):
        for index, player in enumerate(self.players, 1):
            if player.health == 0:
                continue
            for direction in Direction:
                if f"p{index}_{direction.name.lower()}" in actions:
                    player.direction = direction

    def update(self, now=None):
        now = monotonic() if now is None else now
        for player in self.players:
            self._advance_player(player, now)

    def _advance_player(self, player, now):
        moves = 0
        while player.health > 0:
            step = player.next_step
            damage = player.next_damage
            if step <= now + TIME_TOLERANCE and (damage is None or step <= damage + TIME_TOLERANCE):
                self._move_player(player, step)
                moves += 1
                if moves == MAX_CATCH_UP_STEPS and player.next_step <= now + TIME_TOLERANCE:
                    player.next_step = now + self._step_interval(player)
            elif damage is not None and damage <= now + TIME_TOLERANCE:
                self._damage(player, damage)
            else:
                return

    def _step_interval(self, player):
        return self.step_seconds * 100 / player.speed_percent

    def _move_player(self, player, at):
        target = _next_cell(player.cell, player.direction)
        player.blocked = self._collisions.get(target)
        if player.blocked is None:
            player.cell = target
            self._enter_cell(player, at)
        player.next_step = at + self._step_interval(player)

    def _enter_cell(self, player, at):
        field = self._effects.get(player.cell)
        player.slow_percent = field.slow.percent if field and field.slow else 0
        player.entered_cell_at = at
        player.next_damage = None
        if field and field.damage:
            self._damage(player, at)

    def _damage(self, player, at):
        field = self._effects[player.cell].damage
        player.health = max(0, player.health - field.amount)
        next_hit = at + field.interval
        expires = None if field.duration is None else player.entered_cell_at + field.duration
        if player.health == 0 or (expires is not None and next_hit >= expires - TIME_TOLERANCE):
            player.next_damage = None
        else:
            player.next_damage = next_hit

    def draw(self, surface, board_rect):
        """Draw the two snakes as distinct directional markers over the map."""
        shared_cell = self.player_count == 2 and self.players[0].cell == self.players[1].cell
        for index, (player, color) in enumerate(zip(self.players, PLAYER_COLORS)):
            rect = _cell_rect(board_rect, player.cell).inflate(-4, -4)
            if shared_cell:
                rect.width //= 2
                rect.x += index * rect.width
            pygame.draw.rect(surface, color, rect, width=2 if player.health == 0 else 0, border_radius=3)
            dx, dy = player.direction.value
            front = (rect.centerx + dx * rect.width // 3, rect.centery + dy * rect.height // 3)
            pygame.draw.line(surface, (28, 32, 37), rect.center, front, width=2)
