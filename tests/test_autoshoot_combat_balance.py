"""Play-balance regression: one weak auto-shot must not delete boss phases."""
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

from modules.boss_balance import (
    BASE_BOSS_HP, GUARDIAN_EXTRA_HP, boss_max_health,
    hits_to_defeat, estimated_auto_shoot_seconds,
)
from modules.boss_phases import hp_stage
from modules.enums import ItemType
from modules.game import Boss, Boss2, Game, Item
from modules.projectile_config import (
    MAX_AUTO_SHOTS_PER_HEAD, PLAYER_PROJECTILE_DAMAGE,
    PLAYER_PROJECTILE_ENEMY_DAMAGE, PLAYER_FIREBALL_DAMAGE,
)


def make_boss_fight(level=1, players=1):
    game = Game(headless=True)
    game.start_game(players)
    game.level = level
    game.start_boss_fight()
    assert game.boss
    return game


def pickup():
    return Item(ItemType.PROJECTILE_SHOOT)


def test_one_shot_damage_math_prevents_instant_boss_kills():
    assert PLAYER_PROJECTILE_DAMAGE == 2
    assert PLAYER_PROJECTILE_ENEMY_DAMAGE == 1
    assert PLAYER_FIREBALL_DAMAGE == 3  # retain manual fireball damage
    assert MAX_AUTO_SHOTS_PER_HEAD == 1
    assert BASE_BOSS_HP == 64
    assert GUARDIAN_EXTRA_HP == 8

    for level, hp in ((1, 64), (2, 70), (3, 84), (4, 82)):
        game = make_boss_fight(level)
        assert game.boss.health == game.boss.max_health == hp
        before = game.boss
        # A full former three-shot salvo (30 HP) is no longer meaningful
        # burst damage. Even three direct *confirmed* pickup hits cannot KO.
        for _ in range(3):
            assert game.damage_boss(PLAYER_PROJECTILE_DAMAGE, "player_projectile") is False
        assert game.boss is before
        assert game.boss.health == hp - 6


@pytest.mark.parametrize("level,hp", [(1, 64), (2, 70), (3, 84)])
def test_reference_2s_auto_fire_has_roughly_one_minute_early_boss_budget(
        level, hp):
    hits = hits_to_defeat(hp, PLAYER_PROJECTILE_DAMAGE)
    assert hits in (32, 35, 42)
    seconds = estimated_auto_shoot_seconds(
        hp, PLAYER_PROJECTILE_DAMAGE, interval=2,
    )
    assert 60 <= seconds <= 90
    assert seconds == hits * 2
    assert boss_max_health(level, guardian=level == 3) == hp


@pytest.mark.parametrize("players", [1, 2])
def test_repeated_pickups_keep_only_one_auto_shot_per_head(players):
    game = make_boss_fight(1, players)
    for _ in range(4):
        game.handle_item_pickup(pickup())
    assert game.effects["projectile_shoot"] > 0
    assert game.extra_auto_shots == 0

    # The 1P or 2P pickup immediately enables automatic targeting, but only
    # one projectile for each living snake per scheduled firing interval.
    game.projectiles.clear()
    game.auto_shoot()
    assert len(game.projectiles) == players
    assert all(shot["projectile_type"] == "player_projectile"
               for shot in game.projectiles)

    # Force another scheduled wave (direct helper) without any new multiplier.
    game.projectiles.clear()
    game.auto_shoot_for_head(
        game.snake[0] if players == 1 else game.snake1[0],
        game.snake_direction if players == 1 else game.snake_direction1,
    )
    assert len(game.projectiles) == 1


def test_profile_hp_uses_multiplier_but_preserves_fixed_art_and_phase_math():
    for level, key, boss_type in (
        (1, "medusa", Boss),
        (2, "hunter", Boss),
        (3, "guardian", Boss2),
    ):
        boss = boss_type(level, health_multiplier=1.25, profile_key=key)
        expected = boss_max_health(
            level, 1.25, guardian=key == "guardian",
        )
        assert boss.health == boss.max_health == expected
        assert boss.phases.max_health == expected
        assert boss.art_asset == boss.profile.sprite
        assert hp_stage(int(expected * .7), expected) == 2
        assert hp_stage(int(expected * .35), expected) == 3


def test_boss_fight_logs_max_health_and_elapsed_for_future_tuning(monkeypatch):
    from modules import game as game_module
    game = make_boss_fight()
    boss = game.boss
    started = game.boss_fight_started_at
    monkeypatch.setattr(game_module.time, "time", lambda: started + 65)
    # A direct lethal hit is used only as a controlled telemetry fixture;
    # automatic pickup projectiles always do 2 HP, tested separately.
    assert game.damage_boss(boss.health, "test_finisher", is_projectile=False)
    events = [event for event in game.combat_events
              if event["type"] == "boss_defeated"]
    assert len(events) == 1
    assert events[0]["boss"] == "medusa"
    assert events[0]["max_health"] == 64
    assert events[0]["duration_seconds"] == 65
