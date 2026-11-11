import os
import random
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

import pygame

from developer_simulator import SCENARIOS, SimulatedClock
from modules.game import Game
from modules.simulation_checks import run_rule_checks


def run_checks(scenarios, game_factory=Game, **kwargs):
    return run_rule_checks(scenarios, 20261109, game_factory=game_factory,
                           clock_factory=SimulatedClock, **kwargs)


def test_rule_checks_exercise_classic_and_frost_and_restore_random_state():
    pygame.init()
    pygame.display.set_mode((1, 1))
    state = random.getstate()

    checks = run_checks(SCENARIOS)

    assert len(checks) == 5
    assert all(check["seed"] == 20261109 and check["status"] == "passed"
               for check in checks), checks
    assert random.getstate() == state


def test_irrelevant_and_cancelled_checks_are_marked_as_not_run():
    def unexpected_game_creation(**kwargs):
        raise AssertionError("Ausgelassene Prüfungen dürfen keine Spielinstanz starten")

    unrelated = run_checks(("portal",), game_factory=unexpected_game_creation)
    cancelled = run_rule_checks(SCENARIOS, 20261109, skip_reason="Simulation abgebrochen.")

    assert all(check["status"] == "not_run" for check in unrelated)
    assert all(check["status"] == "not_run" and check["detail"] == "Simulation abgebrochen."
               for check in cancelled)


def test_missing_projectile_hit_is_a_rule_failure(monkeypatch):
    pygame.init()
    pygame.display.set_mode((1, 1))
    monkeypatch.setattr(Game, "_resolve_classic_boss_projectile_hits", lambda game: None)

    checks = run_checks(("2p",))

    failures = [check for check in checks if check["status"] == "failed"]
    assert [failure["id"] for failure in failures] == ["classic_boss_shot_once"]
    assert "(90, 100)" in failures[0]["detail"]
    assert "(100, 100)" in failures[0]["detail"]
    assert all(check["status"] in ("not_run", "failed") for check in checks)


def test_internal_assertion_is_a_technical_exception_and_restores_random_state():
    state = random.getstate()

    def broken_game(**kwargs):
        random.random()
        random.randrange(10)
        raise AssertionError("Interner Defekt")

    checks = run_checks(("1p",), game_factory=broken_game)

    exceptions = [check for check in checks if check["status"] == "exception"]
    assert len(exceptions) == 1
    assert exceptions[0]["exception"] == "AssertionError"
    assert "Interner Defekt" in exceptions[0]["stacktrace"]
    assert all(check["status"] in ("not_run", "exception") for check in checks)
    assert random.getstate() == state
