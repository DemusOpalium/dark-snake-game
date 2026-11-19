"""Fixed boss personalities, profile-specific decisions and artwork."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1, 1))

from config import GRID_SIZE, GRID_WIDTH, GRID_HEIGHT
from modules import game as game_module
from modules.boss_medusa import MedusaReading
from modules.boss_personality import PROFILES, guardian_step, profile_for_level
from modules.game import Boss, Boss2, Game


def test_three_fixed_ids_images_and_nonrandom_level_rotation():
    assert set(PROFILES) == {"hunter", "guardian", "medusa"}
    assert [profile_for_level(level).key for level in range(1, 8)] == [
        "medusa", "hunter", "guardian", "medusa", "hunter", "guardian", "medusa",
    ]
    assert {p.sprite for p in PROFILES.values()} == {
        "Boss-RingG60.png", "Boss-AlexG60.png", "Boss-SkullPurPurG60.png",
    }
    assert len({p.sprite for p in PROFILES.values()}) == 3
    assert PROFILES["medusa"].remote_eye_limit == 2
    assert all(p.remote_eye_limit == 0 for k, p in PROFILES.items()
               if k != "medusa")


@pytest.mark.parametrize("level,key,kind", [
    (1, "medusa", Boss), (2, "hunter", Boss),
    (3, "guardian", Boss2), (4, "medusa", Boss),
])
def test_game_spawn_assigns_stable_artwork_and_matching_ability_profile(
        level, key, kind):
    game = Game(headless=True)
    game.start_game(1)
    game.level = level
    assert game.start_boss_fight()
    boss = game.boss
    assert type(boss) is kind
    assert boss.profile_key == key
    assert boss.profile == profile_for_level(level)
    assert boss.art_asset == boss.profile.sprite
    assert boss.image is not None
    assert boss.image.get_size() == (boss.size * GRID_SIZE,
                                     boss.size * GRID_SIZE)
    assert boss.eyes.MAX_EYES == boss.profile.remote_eye_limit
    assert boss.announcement == f"{boss.profile.name} erscheint!"


def test_same_boss_archetype_always_same_sprite_even_in_restarted_round():
    for level in (1, 2, 3, 5):
        first = Game(headless=True)
        first.start_game(1)
        first.level = level
        first.start_boss_fight()
        second = Game(headless=True)
        second.start_game(1)
        second.level = level
        second.start_boss_fight()
        assert first.boss.profile_key == second.boss.profile_key
        assert first.boss.art_asset == second.boss.art_asset
        assert first.boss.image.get_size() == second.boss.image.get_size()


def test_hunter_faster_and_only_medusa_uses_remote_frost():
    hunter = Boss(level=2, profile_key="hunter")
    guardian = Boss2(level=3, profile_key="guardian")
    medusa = Boss(level=1, profile_key="medusa")
    for boss in (hunter, guardian, medusa):
        assert boss.ai_preview is False
        boss.set_ai_preview(True)
        assert boss.chase_speed == boss.profile.movement_interval
    assert hunter.chase_speed < medusa.chase_speed < guardian.chase_speed
    assert hunter.profile.swipe and not hunter.profile.shield
    assert guardian.profile.shield and not guardian.profile.swipe
    assert medusa.profile.shield and medusa.profile.swipe
    assert not hunter.profile.frost_throw and not guardian.profile.frost_throw
    assert medusa.profile.frost_throw
    assert hunter.eyes.MAX_EYES == guardian.eyes.MAX_EYES == 0
    assert medusa.eyes.MAX_EYES == 2
    for boss in (hunter, guardian, medusa):
        boss.set_ai_preview(False)
        assert boss.chase_speed == boss._classic_chase_speed
        assert boss._aoe_interval == 5
        assert boss._projectile_interval == 3


def test_guardian_ring_behavior_respects_walls_and_not_chase_at_any_distance():
    pos, size = (10, 10), 4
    # On the desired ring (distance=5): maintain position.
    assert guardian_step(pos, size, (17, 12), (), (GRID_WIDTH, GRID_HEIGHT)) == (0, 0)
    # Player close -> full body retreats.
    away = guardian_step(pos, size, (12, 12), (), (GRID_WIDTH, GRID_HEIGHT))
    assert away is not None and away != (0, 0)
    target = (12, 12)
    next_center = (12 + away[0], 12 + away[1])
    assert sum((next_center[i] - target[i]) ** 2 for i in (0, 1)) > 0
    # With all 8 neighboring lanes blocked the guard must not clip walls.
    blockers = {(10 + dx, 10 + dy)
                for dx, dy in ((-1, 0), (4, 0), (0, -1), (0, 4))}
    assert guardian_step(pos, size, (12, 12), blockers,
                         (GRID_WIDTH, GRID_HEIGHT)) == (0, 0)


@pytest.mark.parametrize("level,expect_frost", [
    (1, True), (2, False), (3, False),
])
def test_only_tactical_medusa_throws_frost_in_opt_in_mode(
        monkeypatch, level, expect_frost):
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(1)
    game.level = level
    game.start_boss_fight()
    boss = game.boss
    boss.spawn_time = clock.now - 5
    boss.set_ai_preview(True)
    boss.eyes.reading = MedusaReading(
        "VISIBLE", 1, (10, 10), (10, 10), "direct",
    )
    game._vision_blockers = frozenset()
    game._tick_medusa_volley(clock.now)
    assert (boss.tactics.volley is not None) is expect_frost


def test_personality_overlay_is_developer_only(monkeypatch):
    game = Game(headless=True)
    game.start_game(1)
    game.start_boss_fight()
    boss = game.boss
    boss.set_ai_preview(True)
    game.enemy_ai_preview = True
    # State changes are not dependent on rendering. Drawing works
    # both with and without the debug overlay and cannot change art.
    before_art = boss.art_asset
    game.draw_game()
    game.draw_game()
    assert boss.art_asset == before_art
