"""Medusa Tactics B: telegraphed Frost throws with one hit per player."""
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

from config import GRID_SIZE
from modules.boss_medusa import MedusaReading
from modules.boss_tactics import MedusaTactics
from modules.boss_tactics_visual import draw_medusa_volley
from modules import game as game_module
from modules.game import Game, Boss


def reading(kind="VISIBLE", target=(8, 7)):
    return MedusaReading(kind, 1, target, target, "direct")


def test_frost_volley_uses_confirmed_sight_not_search_memory_or_walls():
    tactics = MedusaTactics()
    assert tactics.cast(reading("SEARCHING"), 100, (5, 5), (), (40, 35)) is None
    assert tactics.cast(reading(), 100, (5, 5), {(8, 7)}, (40, 35)) is None
    attack = tactics.cast(reading("RELAY"), 100, (5, 5), (), (40, 35))
    assert attack is not None
    assert attack.target == (8, 7)
    assert attack.phase(100.9) == "warning"
    assert attack.phase(101.35) == "impact"
    assert attack.phase(102.0) == "done"
    assert tactics.cast(reading(), 102, (5, 5), (), (40, 35)) is None
    assert tactics.cast(reading(), 106.01, (5, 5), (), (40, 35)) is not None


def test_damage_once_each_player_during_impact_not_per_frame():
    tactics = MedusaTactics()
    a = tactics.cast(reading(), 100, (4, 5), (), (40, 35))
    assert a is not None
    players = [((8, 7), "p1"), ((8, 8), "p2")]
    assert tactics.hit_players(101.3, players) == ()
    assert tactics.hit_players(101.36, players) == ("p1", "p2")
    assert tactics.hit_players(101.40, players) == ()
    assert tactics.hit_players(101.98, players) == ()
    assert tactics.hit_players(102.1, players) == ()
    assert tactics.volley is None


def test_new_player_can_enter_after_impact_but_only_once():
    tactics = MedusaTactics()
    tactics.cast(reading(), 1, (1, 1), (), (40, 35))
    assert tactics.hit_players(2.36, [((15, 15), "p1")]) == ()
    assert tactics.hit_players(2.50, [((8, 7), "p1")]) == ("p1",)
    assert tactics.hit_players(2.55, [((8, 7), "p1")]) == ()


def test_cancel_removes_warning_without_instant_recast():
    tactics = MedusaTactics()
    tactics.cast(reading(), 1, (1, 1), (), (40, 35))
    tactics.cancel(1.2)
    assert tactics.volley is None
    assert tactics.cast(reading(), 1.3, (1, 1), (), (40, 35)) is None
    tactics.reset()
    assert tactics.cast(reading(), 2, (1, 1), (), (40, 35)) is not None


def test_frost_warning_and_impact_are_drawn_without_gameplay_side_effects():
    tactics = MedusaTactics()
    volley = tactics.cast(reading(), 10, (3, 4), (), (40, 35))
    surface = pygame.Surface((24 * GRID_SIZE, 20 * GRID_SIZE), pygame.SRCALPHA)
    draw_medusa_volley(surface, volley, 10.4, GRID_SIZE)
    assert surface.get_bounding_rect().width > 0
    assert volley.hit_players == set()
    surface.fill((0, 0, 0, 0))
    draw_medusa_volley(surface, volley, 11.5, GRID_SIZE)
    assert surface.get_bounding_rect().width > 0
    assert volley.hit_players == set()


def make_combat(monkeypatch, players):
    clock = SimpleNamespace(now=100.)
    monkeypatch.setattr(game_module.time, "time", lambda: clock.now)
    game = Game(headless=True)
    game.start_game(players)
    game.start_boss_fight()
    boss = game.boss
    assert isinstance(boss, Boss)
    boss.spawn_time = clock.now - 5
    boss.x, boss.y = 5, 5
    boss.set_ai_preview(True)
    game.respawn_invincible_until = clock.now - 1
    game.effects["invincibility"] = 0
    return game, clock, boss


@pytest.mark.parametrize("players", [1, 2])
def test_game_integration_frost_hit_requires_warning_and_no_duplicate_damage(
        monkeypatch, players):
    game, clock, boss = make_combat(monkeypatch, players)
    if players == 1:
        game.snake = [(8, 7)]
        health_attrs = ("player_health",)
    else:
        game.snake1 = [(8, 7)]
        game.snake2 = [(8, 8)]
        health_attrs = ("player_health_p1", "player_health_p2")
    boss.eyes.reading = reading()
    assert not game._tick_medusa_volley(clock.now)
    assert boss.tactics.volley is not None
    assert all(getattr(game, key) == 100 for key in health_attrs)
    clock.now += 1.36
    assert not game._tick_medusa_volley(clock.now)
    assert all(getattr(game, key) == 90 for key in health_attrs)
    clock.now += .05
    game._tick_medusa_volley(clock.now)
    assert all(getattr(game, key) == 90 for key in health_attrs)
    assert len([ev for ev in game.combat_events
                if ev["type"] == "medusa_frost_hit"]) == players


def test_game_invincibility_protects_player_without_consuming_the_hit(monkeypatch):
    game, clock, boss = make_combat(monkeypatch, 1)
    game.snake = [(8, 7)]
    boss.eyes.reading = reading()
    game._tick_medusa_volley(clock.now)
    clock.now += 1.36
    game.respawn_invincible_until = clock.now + .1
    game._tick_medusa_volley(clock.now)
    assert game.player_health == 100
    clock.now += .15
    game._tick_medusa_volley(clock.now)
    assert game.player_health == 90


def test_game_ai_disabled_never_casts_or_damages(monkeypatch):
    game, clock, boss = make_combat(monkeypatch, 1)
    game.snake = [(8, 7)]
    boss.eyes.reading = reading()
    boss.set_ai_preview(False)
    clock.now += 10
    game._tick_medusa_volley(clock.now)
    assert boss.tactics.volley is None
    assert game.player_health == 100
