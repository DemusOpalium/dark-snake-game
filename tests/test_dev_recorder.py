"""Irians Auge A: no gameplay mutation, bounded and crash-safe telemetry."""
import json
from pathlib import Path

from modules.dev_recorder import DeveloperRecorder, MAX_EVENTS, MAX_SAMPLES


def _token():
    return {"round_id": "a" * 32, "mode": "classic",
            "players": 1, "started_at": "2026-11-20T00:00:00+00:00"}


def test_off_by_default_creates_no_report(tmp_path):
    recorder = DeveloperRecorder(directory=tmp_path)
    assert not recorder.begin_round(_token(), context={})
    recorder.event("boss_phase_active", phase=2)
    assert not recorder.checkpoint()
    assert list(tmp_path.iterdir()) == []


def test_json_milestones_and_final_status(tmp_path):
    ticks = iter([0, 0, 0.3, 0.6, 0.7, 1])
    recorder = DeveloperRecorder(directory=tmp_path, clock=lambda: next(ticks))
    assert recorder.configure(True)
    assert recorder.begin_round(_token(), context={"map": "FrostAge"})
    recorder.event("boss_spawn", boss="guardian", hp=84)
    recorder.sample(level=3, player_heads={1: [1, 2]}, boss={"x": 3},
                    enemies=2, items=1, portal=None, world="FrostAge")
    assert recorder.checkpoint("boss_spawn")
    assert recorder.finish("life_depleted")
    result = json.loads((tmp_path / ("dev-round-" + "a" * 32 + ".json")).read_text(encoding="utf-8"))
    assert result["schema_version"] == 1
    assert result["finish_reason"] == "life_depleted"
    assert result["events"][-1]["type"] == "round_finished"
    assert result["positions"][0]["boss"]["x"] == 3
    assert result["source_guide"]["boss_teleport"].endswith("boss_teleport.py")


def test_memory_limits_and_feedback_validation(tmp_path):
    recorder = DeveloperRecorder(directory=tmp_path)
    recorder.configure(True)
    recorder.begin_round(_token(), context={})
    for _ in range(MAX_EVENTS + 50):
        recorder.event("projectile_fired")
    assert len(recorder.events) == MAX_EVENTS
    assert not recorder.add_feedback(subject="boss", prompt="?", rating=8)
    assert recorder.add_feedback(subject="boss", prompt="Fair?", rating=4, note="Gut")
    assert recorder.report["feedback"][0]["rating"] == 4
    recorder.finish()
    result = json.loads(next(tmp_path.glob("dev-round-*.json")).read_text(encoding="utf-8"))
    assert result["dropped_events"] >= 50


def test_failed_writes_never_affect_round(tmp_path):
    occupied = tmp_path / "not_a_directory"
    occupied.write_text("blocked")
    recorder = DeveloperRecorder(directory=occupied)
    recorder.configure(True)
    recorder.begin_round(_token(), context={})
    recorder.event("boss_damage", amount=10)
    assert not recorder.checkpoint("boss")
    assert recorder.error
    assert not recorder.finish()


def test_recorder_toggle_refused_during_active_round(tmp_path):
    recorder = DeveloperRecorder(directory=tmp_path)
    recorder.configure(True)
    recorder.begin_round(_token(), context={})
    assert not recorder.configure(False)
    assert recorder.enabled
    recorder.finish()
    assert recorder.configure(False)
