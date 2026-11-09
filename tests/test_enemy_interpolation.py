import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE
from modules import enemies
from modules.bolbu_enemy import BolbuEnemy
from modules.enemies import NormalEnemy


@pytest.mark.parametrize("enemy_type", [NormalEnemy, BolbuEnemy])
def test_enemy_glides_and_its_hitbox_matches_the_sprite(monkeypatch, enemy_type):
    now = 10.0
    monkeypatch.setattr(enemies.time, "time", lambda: now)
    enemy = enemy_type()
    if enemy_type is BolbuEnemy:
        assert enemy.image.get_size() == (enemy.width, enemy.height) == (GRID_SIZE, GRID_SIZE)
    enemy.x, enemy.y = 2, 3
    enemy.speed = 1
    enemy._start_sprint(now, 2.0, 10, 3)
    assert enemy.get_hitbox().topleft == (2 * GRID_SIZE, 3 * GRID_SIZE)

    now += 0.4
    enemy.update()
    assert (enemy.x, enemy.y) == (3, 3)  # Grid state already committed.
    assert enemy.get_hitbox().topleft == (2 * GRID_SIZE, 3 * GRID_SIZE)

    now += enemy.GLIDE_SECONDS / 2
    enemy.update()
    expected = pygame.Rect(round(2.5 * GRID_SIZE), 3 * GRID_SIZE, enemy.width, enemy.height)
    assert enemy.get_hitbox() == enemy.get_render_rect() == expected
    enemy.image = pygame.Surface(expected.size, pygame.SRCALPHA)
    enemy.image.fill((255, 255, 255, 255))
    surface = pygame.Surface((10 * GRID_SIZE, 10 * GRID_SIZE), pygame.SRCALPHA)
    enemy.draw(surface)
    assert surface.get_bounding_rect() == expected

    now += enemy.GLIDE_SECONDS
    enemy.update()
    assert enemy.get_hitbox().topleft == (3 * GRID_SIZE, 3 * GRID_SIZE)


def test_bolbu_can_sprint_after_a_six_without_any_previous_sprint(monkeypatch):
    now = 10.0
    monkeypatch.setattr(enemies.time, "time", lambda: now)
    enemy = BolbuEnemy()
    enemy.x, enemy.y = 2, 3
    enemy.speed = 1
    monkeypatch.setattr(enemies.random, "randint", lambda *_: 6)
    enemy.roll_dice(2, 0)
    now += 0.4
    enemy.update()
    assert (enemy.x, enemy.y) == (2, 2)
