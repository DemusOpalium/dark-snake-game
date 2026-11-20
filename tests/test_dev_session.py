"""Global opt-in session is bounded, crash-safe and independent of rounds."""
import json

from modules.dev_session import DeveloperSession, MAX_EVENTS


def test_multiple_rounds_in_one_session(tmp_path):
    session = DeveloperSession(directory=tmp_path)
    assert session.start()
    session.event("navigation", source="INTRO", destination="SETTINGS")
    session.event("navigation", source="SETTINGS", destination="INTRO")
    for n in range(2):
        token = {"round_id": str(n + 1) * 32,
                 "players": n + 1, "started_at": "2026-11-20T12:00:00+00:00"}
        session.round_start(token)
        session.round_end(token, "life_depleted", report_saved=True)
    assert session.has_data
    assert session.checkpoint("manual")
    assert session.active  # Manual save must not stop further recording.
    session.event("tester_marker", screen="INTRO")
    assert session.end("disabled")
    saved = json.loads(next(tmp_path.glob("dev-session-*.json")).read_text(encoding="utf-8"))
    assert len(saved["rounds"]) == 2
    assert saved["rounds"][0]["round_id"] == "1" * 32
    assert saved["rounds"][1]["round_id"] == "2" * 32
    assert saved["events"][-1]["type"] == "session_finished"
    assert not saved["active"]  # stored status reflects intentional close


def test_session_missing_directory_cannot_kill_ui(tmp_path):
    blocked = tmp_path / "file"
    blocked.write_text("occupied")
    session = DeveloperSession(directory=blocked)
    assert session.start()
    assert session.error
    session.event("studio_toggle", active=True)
    assert not session.checkpoint("manual")
    assert session.dirty
    assert not session.end()
    assert session.active  # failed flush cannot silently turn recording off


def test_only_known_events_and_no_frame_disk_churn(tmp_path):
    session = DeveloperSession(directory=tmp_path)
    session.start()
    for i in range(MAX_EVENTS + 15):
        session.event("navigation", source="INTRO", destination="SETTINGS")
    assert len(session.events) == MAX_EVENTS
    assert session.dropped >= 15
    assert not session.event("raw_keystroke", password="PRIVATE")
    assert not session.maybe_autosave()
    assert len(list(tmp_path.glob("dev-session-*.json"))) == 1
