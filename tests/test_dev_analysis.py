"""Offline technical analysis never invents a player's emotions."""
from modules.dev_analysis import analyze_report, render_html


def _record():
    return {
        "round_id": "abcd", "started_at": "2026-11-20T00:00:00+00:00",
        "finished_at": "2026-11-20T00:01:00+00:00", "finish_reason": "life_depleted",
        "context": {"players": 1, "grid": [45, 31],
                    "world": "FrostAge", "vision_blockers": [[4, 4]]},
        "events": [
            {"ms": 0, "type": "boss_spawn", "data": {"boss": "guardian", "level": 3, "hp": 84}},
            {"ms": 4000, "type": "boss_phase_active", "data": {"phase": 2}},
            {"ms": 12000, "type": "boss_world_scan_warning", "data": {}},
            {"ms": 15000, "type": "boss_teleport_warning", "data": {"stage": 3}},
            {"ms": 16000, "type": "boss_teleport_aborted", "data": {"reason": "landing_occupied"}},
            {"ms": 20000, "type": "boss_damage", "data": {"damage": 15}},
            {"ms": 23000, "type": "boss_defeated", "data": {"boss": "guardian"}},
        ],
        "positions": [
            {"ms": 200, "level": 3, "heads": {"1": [1, 2]},
             "boss": {"cell": [5, 5], "hp": 84}, "world": "FrostAge"},
            {"ms": 450, "level": 3, "heads": {"1": [1, 2]},
             "boss": {"cell": [6, 5], "hp": 70}, "world": "FrostAge"},
        ],
        "feedback": [{"subject": "boss:guardian:1", "rating": 4,
                      "note": "<script>alert(1)</script>", "item_verdict": []}],
        "dropped_events": 0, "dropped_samples": 0,
    }


def test_fight_timeline_and_map_counts():
    result = analyze_report(_record())
    assert result["fights"][0]["duration_ms"] == 23000
    assert result["fights"][0]["teleport_aborts"] == 1
    assert result["fights"][0]["teleport_arrivals"] == 0
    assert result["fights"][0]["damage_to_boss"] == 15
    assert result["heatmap"]["p1"] == [{"x": 1, "y": 2, "samples": 2}]
    assert result["fights"][0]["phase_events"][0]["phase"] == 2


def test_html_is_static_and_escapes_player_notes():
    html = render_html(_record())
    assert "<svg" in html
    assert "FrostAge" in html
    assert "&lt;script&gt;" in html
    assert "<script>" not in html
    assert "iframe" not in html


def test_missing_partial_data_handled():
    result = analyze_report({"events": [], "positions": [], "context": {}})
    assert result["fights"] == []
    assert result["sample_count"] == 0
