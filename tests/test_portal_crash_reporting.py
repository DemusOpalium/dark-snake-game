import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from modules.enums import GameState
from modules.game import Game
from modules import crash_reporting
from modules import game as game_module


def test_boss_portal_does_not_replace_an_active_boss(monkeypatch):
    game = Game()
    game.start_game(1)
    assert game.start_boss_fight() is True
    active_boss = game.boss

    game.activate_portal("boss")

    assert game.boss is active_boss
    assert game.game_state is GameState.BOSS_FIGHT
    assert game.achievement_messages[-1][0] == "Bosskampf läuft bereits!"


def test_expired_portal_without_editor_map_restores_default_background(monkeypatch):
    game = Game()
    game.start_game(1)
    game.__dict__.pop("level_map", None)

    game.activate_portal("color_change")
    portal_pixel = game.background.get_at((0, 0))
    game.portal_effect_end = 0
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)

    game.update()

    assert game.portal_effect_active is False
    assert game.background is game.level_background_surface
    assert game.background.get_at((0, 0)) == game.default_background_surface.get_at((0, 0))
    assert game.background.get_at((0, 0)) != portal_pixel


def test_expired_portal_restores_editor_map(monkeypatch):
    game = Game()
    game.start_game(1)
    game.level_map = [[None for _ in range(game_module.GRID_WIDTH)]
                      for _ in range(game_module.GRID_HEIGHT)]
    game.level_map[0][0] = "test-tile"
    tile = pygame.Surface((game_module.GRID_SIZE, game_module.GRID_SIZE))
    tile.fill((1, 2, 3))
    monkeypatch.setattr("modules.graphics.get_tile", lambda name: tile)

    game.activate_portal("color_change")
    game.portal_effect_end = 0
    monkeypatch.setattr(game_module.random, "random", lambda: 1.0)

    game.update()

    assert game.background is game.level_background_surface
    assert game.background.get_at((0, 0)) == pygame.Color(1, 2, 3, 255)


def test_crash_reporting_records_events_and_installs_hook(tmp_path, monkeypatch):
    report = tmp_path / "crash.log"
    monkeypatch.setattr(crash_reporting, "REPORT_PATH", report)
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)

    crash_reporting.record_event("Portal aktiviert")
    crash_reporting.install_crash_reporting()

    assert "Portal aktiviert" in report.read_text(encoding="utf-8")
    assert sys.excepthook is crash_reporting.report_exception
