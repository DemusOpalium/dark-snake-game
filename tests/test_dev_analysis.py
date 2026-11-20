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


def test_feedback_post_gameover_persists_and_refreshes_map(tmp_path):
    import json
    from modules.dev_recorder import DeveloperRecorder

    recorder = DeveloperRecorder(directory=tmp_path)
    recorder.configure(True)
    recorder.begin_round({
        "round_id": "b" * 32, "mode": "classic",
        "players": 2, "started_at": "2026-11-20T00:00:00+00:00",
    }, context={"grid": [45, 31], "players": 2})
    assert recorder.finish("life_depleted")
    assert recorder.add_feedback(
        subject="item:PROJECTILE_SHOOT", prompt="War das Item gut?",
        rating=4, note="Hilfreich", item_verdict=["Hilft"],
    )
    report_file = next(tmp_path.glob("dev-round-*.json"))
    html_file = report_file.with_suffix(".html")
    data = json.loads(report_file.read_text(encoding="utf-8"))
    assert data["finish_reason"] == "life_depleted"
    assert data["feedback"][0]["rating"] == 4
    assert data["analysis"]["feedback"][0]["note"] == "Hilfreich"
    assert "Hilfreich" in html_file.read_text(encoding="utf-8")


def test_active_boss_time_subtracts_feedback_pause():
    report = _record()
    report["events"] = [
        {"ms": 1000, "type": "boss_spawn", "data": {"boss": "hunter", "hp": 70}},
        {"ms": 61000, "type": "feedback_pause_end", "data": {"seconds": 40}},
        {"ms": 71000, "type": "boss_defeated", "data": {"boss": "hunter"}},
        {"ms": 80000, "type": "round_finished", "data": {}},
    ]
    battle = analyze_report(report)["fights"][0]
    assert battle["duration_wall_ms"] == 70000
    assert battle["duration_ms"] == 30000


def test_unfinished_boss_ends_at_round_finish_not_later_feedback():
    report = _record()
    report["events"] = [
        {"ms": 100000, "type": "boss_spawn", "data": {"boss": "medusa"}},
        {"ms": 105610, "type": "round_finished", "data": {}},
        {"ms": 180000, "type": "player_feedback", "data": {"rating": 3}},
    ]
    battle = analyze_report(report)["fights"][0]
    assert battle["duration_ms"] == 5610
    assert battle["ended_ms"] == 105610


def test_boss_entry_health_and_lives_are_explicit_not_guessed():
    report = _record()
    report["events"] = [
        {"ms": 0, "type": "vitals_snapshot", "data": {"boundary": "round_start",
            "state": {"players": {"1": {"hp": 100}}, "lives_remaining": 3}}},
        {"ms": 1500, "type": "vitals_change",
         "data": {"source": "aoe_damage", "hp_changes": [
             {"player": 1, "hp_before": 100, "hp_after": 45, "delta_hp": -55}],
             "lives_before": 3, "lives_after": 3, "lives_delta": 0}},
        {"ms": 2000, "type": "boss_spawn", "data": {"boss": "medusa", "hp": 82}},
        {"ms": 2001, "type": "vitals_snapshot", "data": {"boundary": "boss_entry",
            "state": {"players": {"1": {"hp": 45}}, "lives_remaining": 1}}},
        {"ms": 2500, "type": "round_finished", "data": {}},
    ]
    result = analyze_report(report)
    assert result["fights"][0]["player_entry"]["players"]["1"]["hp"] == 45
    assert result["fights"][0]["player_entry"]["lives_remaining"] == 1
    assert result["health_summary"]["hp_lost"] == 55
    assert result["health_summary"]["lives_lost"] == 0  # no fabricated loss


def test_older_player_snapshots_with_dict_placeholders_do_not_break_analysis():
    """Recover existing reports without inventing unknown boss-entry HP."""
    report = _record()
    report["events"] = [
        {"ms": 1000, "type": "boss_spawn",
         "data": {"boss": "guardian", "level": 3, "hp": 84}},
        {"ms": 1000, "type": "vitals_snapshot",
         "data": {"boundary": "boss_entry", "state": {
             "players": {"1": "dict", "2": "dict"},
             "lives_remaining": 1, "boss": {"key": "guardian", "hp": 84}}}},
        {"ms": 2000, "type": "vitals_change",
         "data": {"source": "boss_body_contact", "hp_changes": [
             {"player": 1, "hp_before": 30, "hp_after": 20, "delta_hp": -10}],
             "lives_before": 1, "lives_after": 1, "lives_delta": 0}},
        {"ms": 4000, "type": "boss_defeated", "data": {"boss": "guardian"}},
    ]
    result = analyze_report(report)
    assert result["fights"][0]["player_entry"]["lives_remaining"] == 1
    assert result["health_summary"]["hp_lost"] == 10
    html = render_html(report)
    assert "nicht erfasst" in html
    assert "guardian" in html
