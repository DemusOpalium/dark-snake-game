import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

from developer_simulator import (SimulatedClock, SimulationControl,
                                 format_text_report, run_simulation)


def test_simulated_clock_advances_without_waiting():
    clock = SimulatedClock(10.0)
    clock.advance(125.5)
    assert clock.time() == 135.5


def test_text_report_groups_and_describes_failures():
    failure = {
        "seed": 42,
        "scenario": "portal",
        "game_time": 61.0,
        "game_state": "GAME",
        "level": 2,
        "score": 100,
        "exception": "AttributeError",
        "code_line": "game.py:883",
        "stacktrace": "Traceback: kaputt\n",
    }
    report = {
        "configuration": {"base_seed": 42},
        "runs": [failure],
        "failure_groups": {"AttributeError@game.py:883": [failure]},
    }

    text = format_text_report(report)

    assert "AttributeError@game.py:883 (1 Vorkommen)" in text
    assert "Seed=42 Szenario=portal Spielzeit=61.000" in text
    assert "GameState=GAME Level=2 Score=100" in text
    assert "Traceback: kaputt" in text


def test_simulation_control_can_pause_resume_and_cancel():
    control = SimulationControl()
    assert not control.paused and control.checkpoint()
    control.toggle_pause()
    assert control.paused
    control.toggle_pause()
    assert control.checkpoint()
    control.cancel()
    assert control.cancelled and not control.checkpoint()


def test_all_headless_scenarios_complete_with_offscreen_rendering():
    report = run_simulation(rounds=1, steps=3, step_seconds=1.0, base_seed=20260913)

    assert report["failure_groups"] == {}
    assert report["completion"] == {
        "planned_runs": 10, "completed_runs": 10, "executed_runs": 10,
        "complete": True,
    }
    assert {run["scenario"] for run in report["runs"]} == {
        "1p", "2p", "boss", "boss_final_fireball", "portal", "aoe", "projectiles", "bolbu",
        "restart", "game_over",
    }
    # Terminal scenarios may finish before the tick budget is exhausted.  Every
    # valid run must nevertheless have driven the game and produced real input.
    assert all(0 < run["steps_completed"] <= 3 for run in report["runs"])
    assert all(run["bot_actions"] for run in report["runs"])
    assert all(run["virtual_game_time"] > 0 for run in report["runs"])
