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

from config import GRID_SIZE
from modules import game as game_module
from modules.bolbu_enemy import BolbuProjectile
from modules.enums import GameState, ItemType
from modules.game import FlameProjectile, Game, Item
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


def test_special_damage_item_logs_nonlethal_boss_damage_and_keeps_cooldown():
    game, boss = make_game_with_boss(12)
    item = Item(ItemType.SPECIAL_DAMAGE)
    game.handle_item_pickup(item)
    game.handle_item_pickup(item)

    assert boss.health == 7
    assert game.score == 100
    assert game.boss is boss
    assert game.game_state is GameState.BOSS_FIGHT
    events = game.combat_events
    assert [event["type"] for event in events] == ["boss_damage"]
    assert events[0]["source"] == "special_damage_item"
    assert events[0]["damage"] == 5
    assert events[0]["health"] == 7


def test_lethal_special_damage_item_awards_item_and_boss_points_once():
    game, boss = make_game_with_boss(1)
    game.level = 2
    item = Item(ItemType.SPECIAL_DAMAGE)
    game.handle_item_pickup(item)

    assert boss.health == 0
    assert game.boss is None
    assert game.game_state is GameState.GAME
    assert not game.boss_fight_active
    game.handle_item_pickup(item)
    assert not game.damage_boss(1, "player_fireball")

    assert game.score == 300
    assert game.effects["boss_loot"] > game_module.time.time()
    assert game.boss_spawn_timer > game.effects["boss_loot"]
    damage, victory = game.combat_events
    assert (damage["type"], damage["source"], damage["damage"], damage["health"]) == (
        "boss_damage", "special_damage_item", 1, 0,
    )
    assert (victory["type"], victory["source"], victory["score"]) == (
        "boss_defeated", "special_damage_item", 200,
    )
    assert [effect.name for effect in game.effect_manager.active_effects()] == ["explosion"]


def test_successive_boss_fights_remove_only_their_own_aura():
    game = Game(headless=True)
    game.start_game(1)
    effects = game.effect_manager
    other_aura = effects.spawn("boss_aura", (-10, -10), {"loop": True})
    fog = effects.spawn("fog", (20, 20), {"loop": True})

    for _ in range(2):
        before = effects.active_effects()
        assert game.start_boss_fight()
        fight_effects = effects.active_effects()
        aura = fight_effects[-1]
        assert aura.name == "boss_aura"
        assert all(aura is not effect for effect in before)

        assert game.damage_boss(game.boss.health, "player_fireball")

        after = effects.active_effects()
        assert all(effect is not aura for effect in after)
        assert all(any(effect is previous for effect in after) for previous in before)
        assert sum(effect.name == "boss_aura" for effect in after) == 1
        victory_explosion = after[-1]
        assert victory_explosion.name == "explosion"
        effects.update(0.05)
        assert victory_explosion.age == pytest.approx(0.05)

    assert any(effect is other_aura for effect in effects.active_effects())
    assert any(effect is fog for effect in effects.active_effects())
    assert game.score == 200
    assert sum(event["type"] == "boss_defeated" for event in game.combat_events) == 2


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


def test_fireballs_share_source_artwork_but_move_independently():
    first = FlameProjectile(100, 100, (1, 0))
    second = FlameProjectile(100, 100, (1, 0))
    assert first.image_orig is second.image_orig
    start = second.get_render_rect()
    first.update()
    assert first.get_render_rect() != start
    assert second.get_render_rect() == start


def setup_classic_boss_shot(monkeypatch, players=1, second_head=(4, 4)):
    game = Game(headless=True)
    game.start_game(players)
    game.items.clear()
    if players == 1:
        game.snake = [(4, 4)]
    else:
        game.snake1 = [(4, 4)]
        game.snake2 = [second_head]
    now = game_module.time.time()
    monkeypatch.setattr(game_module.time, "time", lambda: now)
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)
    game.last_update_time = now
    game.respawn_invincible_until = now - 1
    projectile = {"from_boss": True, "pos": (4, 4), "dir": (0.5, 0)}
    game.projectiles.append(projectile)
    return game, projectile


def test_classic_boss_shot_hits_once_per_update_and_keeps_moving(monkeypatch):
    game, projectile = setup_classic_boss_shot(monkeypatch)

    game.update()
    assert game.player_health == 90
    assert game.projectiles == [projectile]
    assert projectile["pos"] == (4.5, 4)

    game.update()
    assert game.player_health == 80
    assert game.projectiles == [projectile]
    assert projectile["pos"] == (5.0, 4)


def test_classic_boss_shot_keeps_grid_move_cadence(monkeypatch):
    game, projectile = setup_classic_boss_shot(monkeypatch)
    game.last_update_time -= 1

    game.update()
    assert game.player_health == 90
    assert game.snake[0] == (5, 4)
    assert projectile["pos"] == (5.0, 4)


@pytest.mark.parametrize("second_head, expected_p2", [((4, 4), 90), ((4, 5), 100)])
def test_classic_boss_shot_applies_same_rule_to_both_players(monkeypatch, second_head, expected_p2):
    game, _ = setup_classic_boss_shot(monkeypatch, 2, second_head)

    game.update()
    assert (game.player_health_p1, game.player_health_p2) == (90, expected_p2)


def test_classic_boss_shot_respects_respawn_protection(monkeypatch):
    game, projectile = setup_classic_boss_shot(monkeypatch)
    game.respawn_invincible_until = game_module.time.time() + 1

    game.update()
    assert game.player_health == 100
    assert projectile["pos"] == (4.5, 4)


def test_two_distinct_classic_boss_shots_apply_two_hits(monkeypatch):
    game, projectile = setup_classic_boss_shot(monkeypatch)
    game.projectiles.append(projectile.copy())

    game.update()
    assert game.player_health == 80


def test_lethal_classic_boss_shot_on_both_heads_costs_one_shared_life(monkeypatch):
    game, _ = setup_classic_boss_shot(monkeypatch, 2)
    game.player_health_p1 = game.player_health_p2 = 10
    game.lives = 1

    game.update()
    assert game.game_state == GameState.GAME_OVER
    assert game.lives == 0
    assert (game.player_health_p1, game.player_health_p2) == (0, 0)
