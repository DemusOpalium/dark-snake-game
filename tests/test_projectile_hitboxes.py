import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE
from modules.bolbu_enemy import BolbuProjectile
from modules.enums import GameState, ItemType
from modules.game import Game, Item
from modules.enemies import NormalEnemy
from modules.projectile_config import (
    BOLBU_PROJECTILE_SPEED_PX_PER_TICK, PLAYER_PROJECTILE_DAMAGE,
)


def make_game_with_boss(health):
    game = Game(headless=True)
    game.start_game(1)
    boss = SimpleNamespace(
        health=health, x=5, y=5, size=3,
        get_hitbox=lambda: pygame.Rect(5 * GRID_SIZE, 5 * GRID_SIZE,
                                       3 * GRID_SIZE, 3 * GRID_SIZE),
    )
    boss.get_rect = boss.get_hitbox
    game.boss = boss
    game.boss_fight_active = True
    game.game_state = GameState.BOSS_FIGHT
    return game, boss


def test_fireball_can_defeat_one_hp_boss_without_negative_health():
    game, boss = make_game_with_boss(1)
    assert game.damage_boss(3, "player_fireball")
    assert boss.health == 0
    assert game.boss is None
    assert game.game_state == GameState.GAME
    assert not game.boss_fight_active
    assert [event["type"] for event in game.combat_events].count("boss_defeated") == 1


def test_nonlethal_fireball_only_reduces_boss_health():
    game, boss = make_game_with_boss(10)
    assert not game.damage_boss(3, "player_fireball")
    assert boss.health == 7 and game.boss is boss
    assert not any(event["type"] == "boss_defeated" for event in game.combat_events)


def test_boss_death_is_processed_only_once():
    game, boss = make_game_with_boss(1)
    score = game.score
    assert game.damage_boss(3, "player_fireball")
    assert not game.damage_boss(PLAYER_PROJECTILE_DAMAGE, "player_projectile")
    assert game.score == score + 100 * game.level
    assert sum(event["type"] == "boss_defeated" for event in game.combat_events) == 1


def test_normal_shot_and_fireball_share_boss_death_handler():
    for source, damage in (("player_projectile", PLAYER_PROJECTILE_DAMAGE),
                           ("player_fireball", 3)):
        game, _ = make_game_with_boss(1)
        game.damage_boss(damage, source)
        defeated = [e for e in game.combat_events if e["type"] == "boss_defeated"]
        assert len(defeated) == 1 and defeated[0]["source"] == source


def test_multishot_projectiles_are_identified_separately():
    game = Game(headless=True)
    game.start_game(1)
    game.extra_auto_shots = 2
    game.auto_shoot_for_head(game.snake[0], game.snake_direction)
    assert [p["projectile_type"] for p in game.projectiles].count("multishot") == 2


def test_bolbu_speed_is_documented_pixels_per_tick_and_avoidable():
    projectile = BolbuProjectile(1, 1, (1, 0))
    start = projectile.rect.x
    projectile.update()
    assert projectile.rect.x - start == BOLBU_PROJECTILE_SPEED_PX_PER_TICK
    assert BOLBU_PROJECTILE_SPEED_PX_PER_TICK < GRID_SIZE


def test_item_hitbox_is_centered_inside_render_rect_at_edges_and_corners():
    item = Item(ItemType.FOOD, hitbox_scale=0.85)
    item.x = item.y = 0
    render, hitbox = item.get_render_rect(), item.get_hitbox()
    assert render.contains(hitbox) and render.center == hitbox.center
    assert hitbox.collidepoint(hitbox.left, hitbox.top)
    assert not hitbox.collidepoint(render.right - 1, render.bottom - 1)


def test_enemy_hitbox_matches_scaled_rendering():
    enemy = NormalEnemy()
    assert enemy.get_hitbox() == enemy.get_render_rect()
    assert enemy.get_rect() == enemy.get_hitbox()
