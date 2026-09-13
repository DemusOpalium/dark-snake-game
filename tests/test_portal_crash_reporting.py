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


def test_boss_portal_does_not_replace_an_active_boss(monkeypatch):
    game = Game()
    game.start_game(1)
    assert game.start_boss_fight() is True
    active_boss = game.boss

    game.activate_portal("boss")

    assert game.boss is active_boss
    assert game.game_state is GameState.BOSS_FIGHT
    assert game.achievement_messages[-1][0] == "Bosskampf läuft bereits!"


def test_crash_reporting_records_events_and_installs_hook(tmp_path, monkeypatch):
    report = tmp_path / "crash.log"
    monkeypatch.setattr(crash_reporting, "REPORT_PATH", report)
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)

    crash_reporting.record_event("Portal aktiviert")
    crash_reporting.install_crash_reporting()

    assert "Portal aktiviert" in report.read_text(encoding="utf-8")
    assert sys.excepthook is crash_reporting.report_exception
