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
from modules.bolbu_enemy import BolbuEnemy
from modules.enemies import NormalEnemy
from modules.frost_prototype import FrostPrototype


def cell_center(x, y):
    return (round((x + 0.5) * GRID_SIZE), round((y + 0.5) * GRID_SIZE))


def test_frost_radius_duration_overlap_and_deactivation():
    frost = FrostPrototype()
    frost.on_fireball_hit(cell_center(5, 5), 10.0)
    assert not frost.enabled
    assert not frost.zones
    assert frost.movement_factor_at(5, 5) == 1.0

    assert frost.toggle()
    frost.on_fireball_hit(cell_center(5, 5), 10.0)
    frost.on_fireball_hit(cell_center(6, 5), 11.0)

    assert frost.movement_factor_at(3, 5) == 0.7
    assert frost.movement_factor_at(5, 5) == 0.7
    assert frost.movement_factor_at(9, 5) == 1.0
    assert frost.movement_factor_at(7, 7) == 1.0
    frost.update(13.0)
    assert len(frost.zones) == 1
    assert frost.movement_factor_at(3, 5) == 1.0
    assert frost.movement_factor_at(5, 5) == 0.7
    frost.update(14.0)
    assert not frost.zones
    assert frost.movement_factor_at(5, 5) == 1.0

    frost.on_fireball_hit(cell_center(5, 5), 15.0)
    assert not frost.toggle()
    assert not frost.zones


@pytest.mark.parametrize("enemy_type", [NormalEnemy, BolbuEnemy])
def test_frost_scales_enemy_movement_cadence(enemy_type, monkeypatch):
    normal = enemy_type()
    chilled = enemy_type()
    for enemy in (normal, chilled):
        enemy.x, enemy.y = 5, 5
        enemy.speed = 1.0
        enemy.last_move = 100.0
        enemy.sprint_chance = 0.0
    frost = FrostPrototype()
    frost.toggle()
    frost.on_fireball_hit(cell_center(5, 5), 100.0)
    factor = frost.movement_factor_at(chilled.x, chilled.y)
    monkeypatch.setattr("modules.enemies.random.choice", lambda _: 1)

    monkeypatch.setattr("modules.enemies.time.time", lambda: 101.01)
    normal.update()
    chilled.update(movement_factor=factor)
    assert (normal.x, normal.y) == (6, 6)
    assert (chilled.x, chilled.y) == (5, 5)

    monkeypatch.setattr("modules.enemies.time.time", lambda: 101.43)
    chilled.update(movement_factor=factor)
    assert (chilled.x, chilled.y) == (6, 6)
    assert chilled.speed == 1.0
