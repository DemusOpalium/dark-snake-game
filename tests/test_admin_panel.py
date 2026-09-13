import os
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules.aoe_zones import DamageZone, DebuffZone, HealZone
from modules.enums import Direction, ItemType
from modules.game import Game


def game_with_players(count=1):
    game = Game()
    game.start_game(count)
    return game


def test_all_immediate_admin_actions(monkeypatch):
    game = game_with_players()
    panel = game.admin_panel
    head = game.snake[0]

    assert panel.spawn_fireball().startswith("Feuerball")
    assert len(game.flame_projectiles) == 1

    monkeypatch.setattr(game, "start_boss_fight", lambda: setattr(game, "boss", object()))
    assert panel.spawn_boss() == "Bosskampf gestartet."
    assert panel.spawn_boss() == "Bosskampf läuft bereits."

    game.player_health = 4
    panel.full_heal()
    assert game.player_health == 100

    before = time.time()
    panel.enable_multi_shot()
    assert before + 89 <= game.effects["projectile_shoot"] <= time.time() + 90

    panel.toggle_hitboxes()
    assert game.debug_show_hitboxes is True

    panel.spawn_bolbu_item()
    assert game.items[-1].type is ItemType.SPAWN_BOLBU
    assert (game.items[-1].x, game.items[-1].y) != head

    panel.spawn_explosion()
    assert len(game.explosions) == 1

    panel.spawn_damage_zone()
    assert isinstance(game.aoe_zones[-1], DamageZone)

    monkeypatch.setattr("modules.admin_panel.random.choice", lambda choices: "heal")
    assert panel.spawn_random_zone() == "Zufällig gewählt: Heilzone."
    assert isinstance(game.aoe_zones[-1], HealZone)


def test_two_player_heal_and_random_slow_zone(monkeypatch):
    game = game_with_players(2)
    game.player_health_p1, game.player_health_p2 = 1, 2
    assert "Beide Spieler" in game.admin_panel.full_heal()
    assert (game.player_health_p1, game.player_health_p2) == (100, 100)
    monkeypatch.setattr("modules.admin_panel.random.choice", lambda choices: "slow")
    game.admin_panel.spawn_random_zone()
    assert isinstance(game.aoe_zones[-1], DebuffZone)


def test_admin_and_editor_capture_input_and_pause_updates(monkeypatch):
    game = game_with_players()
    original_direction = game.next_direction
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB, unicode="\t"))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP, unicode=""))
    game.handle_events()
    assert game.admin_panel.active
    assert game.next_direction is original_direction

    old_head = game.snake[0]
    game.last_update_time = 0
    game.update()
    assert game.snake[0] == old_head

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode=""))
    game.handle_events()
    assert not game.admin_panel.active

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F2, unicode=""))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT, unicode=""))
    game.handle_events()
    assert game.level_editor.active
    assert game.next_direction is Direction.RIGHT
    game.update()
    assert game.snake[0] == old_head


def test_admin_menu_draws_title_labels_and_tooltip():
    game = game_with_players()
    panel = game.admin_panel
    panel.active = True
    panel.buttons[5].is_hovered = True
    panel.draw(game.screen)
    assert len(panel.buttons) == 9
    assert all(panel.panel_rect.contains(button.rect) for button in panel.buttons)
    assert panel.ACTIONS[5][1] == "Bolbu-Item"
    assert "Einsammeln" in panel.ACTIONS[5][2]
