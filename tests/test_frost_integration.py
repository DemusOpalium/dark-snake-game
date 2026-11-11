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
from modules.game import FlameProjectile, Game


def place_enemy(game, kind, now):
    enemy = kind()
    enemy.x, enemy.y = 8, 6
    enemy.width = enemy.height = GRID_SIZE
    enemy.speed = 1.0
    enemy.health = 10
    enemy.sprint_chance = 0.0
    enemy.spawn_time = now - 3
    enemy.last_move = now
    game.enemies.append(enemy)
    return enemy


@pytest.fixture
def match(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("modules.game.time.time", lambda: now[0])
    monkeypatch.setattr("modules.game.time.monotonic", lambda: now[0])
    monkeypatch.setattr("modules.game.random.random", lambda: 1.0)
    game = Game(headless=True)
    game.start_game(1)
    game.items.clear()
    return game, now


@pytest.mark.parametrize("enabled", [False, True])
def test_fireball_creates_at_most_one_frost_zone_on_confirmed_hit(match, enabled):
    game, now = match
    assert not game.frost.enabled
    if enabled:
        assert game.admin_panel.toggle_frost() == "Frost-Test aktiviert."
    target = place_enemy(game, NormalEnemy, now[0])
    other = place_enemy(game, NormalEnemy, now[0])
    for enemy in (target, other):
        enemy.spawn_time = now[0]
        enemy.speed = 0.1
    center = target.get_hitbox().center
    flame = FlameProjectile(*center, (1, 0), speed=0)
    game.flame_projectiles.append(flame)

    game.update()
    assert not game.frost.zones
    assert flame in game.flame_projectiles
    assert target.health == other.health == 10

    now[0] += 2.01
    game.last_update_time = now[0]
    game.update()
    assert target.health == 10 - flame.damage
    assert other.health == 10
    assert flame not in game.flame_projectiles
    assert len(game.frost.zones) == int(enabled)
    if enabled:
        assert game.frost.zones[0].center == center

    game.update()
    assert len(game.frost.zones) == int(enabled)


def test_fireball_hit_on_boss_also_creates_a_single_frost_zone(match):
    game, _ = match
    game.admin_panel.toggle_frost()
    assert game.start_boss_fight()
    boss = game.boss
    boss.x, boss.y = 8, 6
    health = boss.health
    center = boss.get_hitbox().center
    flame = FlameProjectile(*center, (1, 0), speed=0)
    game.flame_projectiles.append(flame)

    game.update()

    assert boss.health == health - flame.damage
    assert flame not in game.flame_projectiles
    assert [zone.center for zone in game.frost.zones] == [center]


@pytest.mark.parametrize("enemy_type", [NormalEnemy, BolbuEnemy])
def test_match_slows_enemy_until_frost_expires(match, monkeypatch, enemy_type):
    game, now = match
    enemy = place_enemy(game, enemy_type, now[0])
    center = enemy.get_hitbox().center
    game.admin_panel.toggle_frost()
    game.frost.on_fireball_hit(center, now[0])
    game.frost.on_fireball_hit(center, now[0])
    monkeypatch.setattr("modules.enemies.random.choice", lambda _: 1)

    now[0] += 1.01
    game.last_update_time = now[0]
    game.update()
    assert (enemy.x, enemy.y) == (8, 6)

    now[0] = 101.43
    game.last_update_time = now[0]
    game.update()
    assert len(game.frost.zones) == 2
    assert (enemy.x, enemy.y) == (9, 7)

    now[0] = 103.0
    enemy.last_move = 101.99
    game.last_update_time = now[0]
    game.update()
    assert not game.frost.zones
    assert (enemy.x, enemy.y) == (10, 8)


def test_frost_is_visible_behind_enemy_sprites(match):
    game, now = match
    enemy = place_enemy(game, NormalEnemy, now[0])
    enemy.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
    enemy.image.fill((38, 210, 85))
    rect = enemy.get_render_rect()
    game.background.fill((12, 14, 17))
    game.admin_panel.toggle_frost()
    game.frost.on_fireball_hit(rect.center, now[0])

    game.draw()

    assert tuple(game.screen.get_at(rect.center)[:3]) == (38, 210, 85)
    red, green, blue = game.screen.get_at((rect.right + 4, rect.centery))[:3]
    assert red > 12
    assert blue > green > red
