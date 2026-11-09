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

from config import DARK_GREY, GREEN, GRID_SIZE, RED, WHITE
from modules.aoe_zones import GrowingBossAOEZone
from modules.enemies import NormalEnemy
from modules.enums import GameState
from modules.fire_explosion import FireExplosionAnimation
from modules.game import Boss, Game


EFFECT_COLOR = (48, 192, 144)


def assert_region(surface, rect, color):
    region = surface.subsurface(rect)
    expected = pygame.Surface(region.get_size(), pygame.SRCALPHA)
    expected.fill(color)
    assert pygame.image.tobytes(region, "RGB") == pygame.image.tobytes(expected, "RGB")


def assert_bar(surface, x, fill_width, fill_color):
    assert_region(surface, (x + 8, 80, 30, 2), WHITE)
    assert_region(surface, (x + 2, 84, fill_width - 2, 12), fill_color)
    assert_region(surface, (x + fill_width, 84, 198 - fill_width, 12), DARK_GREY)


def prepare_world(players):
    game = Game(headless=True)
    game.start_game(players)
    game.items.clear()
    game.achievement_messages.clear()
    game.background.fill((15, 23, 35))
    game.player_health = 25
    game.player_health_p1 = 75
    game.player_health_p2 = 60
    # The opaque world sprite spans the left bar and remains visible beside it.
    marker = pygame.Surface((260, 40), pygame.SRCALPHA)
    marker.fill(EFFECT_COLOR)
    effect = game.effect_manager.spawn("render_regression_marker", (130, 95), {"layer": "world"})
    effect.frames = [marker]
    return game


@pytest.mark.parametrize("players", [1, 2])
@pytest.mark.parametrize(("state", "shade"), [
    (GameState.GAME, 0),
    (GameState.PAUSE, 180),
    (GameState.GAME_OVER, 200),
])
def test_game_draw_composites_world_then_screen_overlay_then_hud(players, state, shade):
    game = prepare_world(players)
    game.game_state = state
    game.draw()

    screen = game.screen
    if players == 1:
        assert_bar(screen, 20, 50, (255, 127, 0))
    else:
        assert_bar(screen, 20, 150, (127, 255, 0))
        assert_bar(screen, screen.get_width() - 220, 120, (0, 128, 255))

    # The pause/game-over shade darkens the world but leaves the HUD at full color.
    expected = pygame.Surface((1, 1), pygame.SRCALPHA)
    expected.fill(EFFECT_COLOR)
    overlay = pygame.Surface((1, 1), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, shade))
    expected.blit(overlay, (0, 0))
    assert_region(screen, (230, 86, 20, 12), expected.get_at((0, 0)))
    assert_region(screen, (screen.get_width() - 34, 16, 18, 18), RED)
    score_area = screen.subsurface((20, 10, 145, 31))
    assert pygame.mask.from_threshold(score_area, WHITE, (1, 1, 1, 255)).count() > 0


def test_draw_game_keeps_hud_for_direct_callers():
    game = prepare_world(1)
    game.draw_game()
    assert_bar(game.screen, 20, 50, (255, 127, 0))
    assert_region(game.screen, (230, 86, 20, 12), EFFECT_COLOR)


def solid_sprite(size, color):
    image = pygame.Surface(size, pygame.SRCALPHA)
    image.fill(color)
    return image


def test_boss_attack_warning_is_visible_behind_boss_snake_and_health_bar(monkeypatch):
    game = prepare_world(1)
    game.game_state = GameState.BOSS_FIGHT
    game.snake = [(7, 6)]
    game._reset_snake_interpolation()
    snake_color = (55, 105, 205)
    boss_color = (44, 218, 124)
    skin = solid_sprite((GRID_SIZE, GRID_SIZE), snake_color)
    monkeypatch.setattr(game.options_menu, "get_skin_image", lambda *_: skin)

    boss = game.boss = Boss(level=1)
    boss.x, boss.y = 8, 6
    rect = boss.get_render_rect()
    now = boss.spawn_time + 10
    boss.last_move = now
    boss.next_aoe = now
    warning = solid_sprite((8, 8), (220, 35, 50))
    monkeypatch.setattr("modules.game.get_aoe_effect", lambda: warning)
    assert boss.update(now) == "aoe"
    boss.image = solid_sprite(rect.size, boss_color)
    monkeypatch.setattr("modules.game.time.time", lambda: now + 3.5)

    game.draw()

    assert_region(game.screen, (rect.x + 5, rect.y + 5, 8, 8), boss_color)
    assert_region(game.screen, (rect.x - GRID_SIZE + 5, rect.y + 5, 8, 8), snake_color)
    assert_region(game.screen, (rect.x + 5, rect.y - 8, 8, 2), GREEN)
    # The warning extends beyond the sprites and remains visible on the field.
    warning_pixel = game.screen.get_at((rect.right + 5, rect.centery))
    assert warning_pixel.r > 100
    assert_bar(game.screen, 20, 50, (255, 127, 0))


@pytest.mark.parametrize("effect_kind", ["growing_zone", "managed_aura", "fire_explosion"])
def test_world_effects_are_visible_behind_normal_enemies(effect_kind):
    game = prepare_world(1)
    enemy = NormalEnemy()
    enemy.x, enemy.y = 8, 6
    enemy.width = enemy.height = GRID_SIZE
    enemy_color = (55, 105, 205)
    enemy.image = solid_sprite((GRID_SIZE, GRID_SIZE), enemy_color)
    game.enemies.append(enemy)
    rect = enemy.get_render_rect()
    frame = solid_sprite((3 * GRID_SIZE, 3 * GRID_SIZE), EFFECT_COLOR)
    if effect_kind == "growing_zone":
        zone = GrowingBossAOEZone(rect.center, GRID_SIZE, 2 * GRID_SIZE, 4,
                                  (*EFFECT_COLOR, 255))
        zone.image = frame
        game.aoe_zones.append(zone)
    elif effect_kind == "managed_aura":
        effect = game.effect_manager.spawn("boss_aura", rect.center)
        effect.frames = [frame]
    else:
        explosion = FireExplosionAnimation(rect.center, scale_factor=1)
        explosion.frames = [frame]
        game.explosions.append(explosion)

    game.draw()

    assert_region(game.screen, (rect.x + 5, rect.y + 5, 8, 8), enemy_color)
    assert_region(game.screen, (rect.right + 5, rect.y + 5, 4, 8), EFFECT_COLOR)


def test_update_advances_zone_and_explosion_without_painting_them(monkeypatch):
    game = prepare_world(1)
    center = (8 * GRID_SIZE, 6 * GRID_SIZE)
    zone = GrowingBossAOEZone(center, GRID_SIZE, 2 * GRID_SIZE, 4, (*EFFECT_COLOR, 255))
    zone.image = solid_sprite((GRID_SIZE, GRID_SIZE), EFFECT_COLOR)
    explosion = FireExplosionAnimation(center, scale_factor=1)
    explosion.frames = [solid_sprite((GRID_SIZE, GRID_SIZE), EFFECT_COLOR)]
    game.aoe_zones.append(zone)
    game.explosions.append(explosion)
    now = zone.created_time + 1
    game.last_update_time = now
    monkeypatch.setattr("modules.game.time.time", lambda: now)
    monkeypatch.setattr("modules.game.random.random", lambda: 1.0)
    sentinel = (3, 15, 23)
    game.screen.fill(sentinel)

    game.update()

    assert zone.radius > GRID_SIZE
    assert explosion.frame_timer == 1
    assert_region(game.screen, (center[0] - 4, center[1] - 4, 8, 8), sentinel)
