import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Dark_Snake"))

import developer_simulator as simulator
from developer_simulator import (SimulatedClock, SimulationControl,
                                 format_text_report, run_simulation, save_report)
from modules import simulation_checks


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
    assert report["outcome"]["status"] == "completed"
    assert report["summary"]["rule_checks_passed"] == 5
    assert report["summary"]["rule_checks_not_run"] == 0


def test_single_scenario_report_is_saved_in_both_formats(tmp_path, monkeypatch):
    commit = "a" * 40
    monkeypatch.setattr(simulator, "_source_commit", lambda: commit)
    report = run_simulation(rounds=1, steps=3, base_seed=20260913, scenarios=["portal"])

    assert report["summary"]["technical_exceptions"] == 0
    assert report["summary"]["rule_checks_passed"] == 0
    assert report["summary"]["rule_checks_not_run"] == 5
    assert {check["status"] for check in report["rule_checks"]} == {"not_run"}
    assert datetime.fromisoformat(report["metadata"]["created_at"]).tzinfo is not None
    assert report["summary"]["duration_seconds"] > 0

    txt, saved_json = save_report(report, tmp_path, scenario="portal")
    saved = json.loads(saved_json.read_text(encoding="utf-8"))
    assert saved["metadata"]["source_commit"] == commit
    assert saved["configuration"]["scenarios"] == ["portal"]
    assert saved["configuration"]["base_seed"] == 20260913
    assert "Spielregelprüfungen nicht ausgeführt: 5" in txt.read_text(encoding="utf-8")


def test_rule_failure_and_technical_exception_are_counted_separately(monkeypatch):
    def bad_rule(game, clock):
        raise simulation_checks.RuleCheckFailure("erwartet 10 HP, erhalten 20 HP")

    def broken_check(game, clock):
        raise RuntimeError("Testaufbau fehlgeschlagen")

    monkeypatch.setattr(simulation_checks, "CHECKS", (
        ("damage", "Schaden", ("boss",), bad_rule),
        ("setup", "Aufbau", ("boss",), broken_check),
    ))
    report = run_simulation(rounds=1, steps=3, base_seed=101, scenarios=["boss"])

    assert report["completion"]["complete"]
    assert report["failure_groups"] == {}
    assert report["summary"]["rule_checks_failed"] == 1
    assert report["summary"]["technical_exceptions"] == 1
    assert [check["status"] for check in report["rule_checks"]] == ["failed", "exception"]
    assert report["outcome"]["status"] == "exception"
    text = format_text_report(report)
    assert "erwartet 10 HP, erhalten 20 HP" in text
    assert "RuntimeError: Testaufbau fehlgeschlagen" in text


def test_cli_fails_and_exports_report_for_game_rule_regression(tmp_path, monkeypatch):
    def bad_rule(game, clock):
        raise simulation_checks.RuleCheckFailure("Schaden zu hoch")

    monkeypatch.setattr(simulation_checks, "CHECKS", (("damage", "Schaden", ("boss",), bad_rule),))
    code = simulator.main(["--rounds", "1", "--profile", "smoke", "--scenario", "boss",
                           "--seed", "42", "--output", str(tmp_path)])
    assert code == 1
    report_path, = tmp_path.glob("*.json")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["outcome"]["status"] == "rule_failed"
    assert report["summary"]["rule_checks_failed"] == 1
    assert report["summary"]["technical_exceptions"] == 0
    assert report_path.with_suffix(".txt").is_file()


def test_timeout_is_not_a_technical_exception_or_complete_run():
    report = run_simulation(rounds=1, steps=3, scenarios=["1p"], base_seed=7,
                            max_simulation_time=1 / 60)
    assert report["outcome"]["status"] == "timeout"
    assert report["abort_reason"]
    assert report["summary"]["timeouts"] == 1
    assert report["summary"]["technical_exceptions"] == 0
    assert not report["completion"]["complete"]
    assert report["summary"]["rule_checks_not_run"] == 5


def test_cancellation_before_first_run_is_reported():
    control = SimulationControl()
    control.cancel()
    report = run_simulation(rounds=1, steps=3, scenarios=["1p"], control=control)
    assert report["outcome"]["status"] == "cancelled"
    assert report["abort_reason"]
    assert report["runs"] == []
    assert report["summary"]["rule_checks_not_run"] == 5
    assert not report["completion"]["complete"]


def test_standalone_exe_uses_embedded_source_commit(tmp_path, monkeypatch):
    commit = "a" * 40
    (tmp_path / "build-commit.txt").write_text(commit, encoding="ascii")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(simulator, "application_root", lambda: tmp_path)
    assert simulator._source_commit() == commit
