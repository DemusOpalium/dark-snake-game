"""Irians Auge C: post-run, read-only interpretation and static bossfight map.

Never infer player emotions from telemetry: only voluntary ratings can
describe experience. Positions sampled every 250 ms are not hitbox evidence.
"""
from __future__ import annotations

from collections import Counter
from html import escape
from math import log1p


RELEVANT_EVENTS = {
    "round_start", "round_finished", "level_up",
    "boss_spawn", "boss_damage", "boss_defeated",
    "boss_phase_warning", "boss_phase_active",
    "boss_world_scan_warning", "boss_world_scan_complete",
    "boss_teleport_warning", "boss_teleport_arrived", "boss_teleport_aborted",
    "boss_shield_raised", "boss_shield_blocked",
    "medusa_frost_warning", "medusa_frost_hit",
    "portal_activated", "item_pickup", "item_applied",
    "enemy_spawn", "player_feedback",
}


def _point(cell, width, height):
    try:
        x, y = int(cell[0]), int(cell[1])
    except (ValueError, TypeError, IndexError, KeyError):
        return None
    return (x, y) if 0 <= x < width and 0 <= y < height else None


def analyze_report(report: dict):
    """Compute honest counts and coarse grid visits without changing source."""
    events = report.get("events") or []
    samples = report.get("positions") or []
    context = report.get("context") or {}
    grid = context.get("grid") or [45, 31]
    try:
        width, height = int(grid[0]), int(grid[1])
    except (TypeError, ValueError, IndexError):
        width, height = 45, 31
    width, height = max(1, min(200, width)), max(1, min(200, height))
    counts = Counter(e.get("type") for e in events if isinstance(e, dict))
    visits = {"p1": Counter(), "p2": Counter(), "boss": Counter()}
    zones = Counter()
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        heads = sample.get("heads") or {}
        if isinstance(heads, dict):
            for index, key in (("1", "p1"), ("2", "p2")):
                cell = _point(heads.get(index), width, height) if index in heads else None
                if cell is not None:
                    visits[key][cell] += 1
        boss = sample.get("boss")
        if isinstance(boss, dict):
            cell = _point(boss.get("cell"), width, height)
            if cell is not None:
                visits["boss"][cell] += 1
        world = sample.get("world")
        if world:
            zones[str(world)[:80]] += 1
    fights = []
    active = None
    for event in events:
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        data = event.get("data") or {}
        if not isinstance(data, dict):
            data = {}
        ms = event.get("ms", 0)
        if not isinstance(ms, (int, float)):
            continue
        if kind == "boss_spawn":
            if active:
                active["outcome"] = "unvollständig (neuer Boss)"
                fights.append(active)
            active = {
                "boss": data.get("boss", "unbekannt"),
                "level": data.get("level"),
                "started_ms": ms,
                "ended_ms": None,
                "duration_ms": None,
                "outcome": "nicht abgeschlossen",
                "hp_start": data.get("hp"),
                "phase_events": [],
                "damage_events": 0,
                "damage_to_boss": 0,
                "teleport_warnings": 0,
                "teleport_arrivals": 0,
                "teleport_aborts": 0,
                "world_scans": 0,
            }
            continue
        if active is None:
            continue
        if kind in ("boss_phase_warning", "boss_phase_active"):
            active["phase_events"].append({
                "ms": ms, "type": kind, "phase": data.get("phase"),
            })
        elif kind == "boss_damage":
            active["damage_events"] += 1
            amount = data.get("damage", 0)
            if isinstance(amount, (int, float)) and amount > 0:
                active["damage_to_boss"] += amount
        elif kind == "boss_teleport_warning":
            active["teleport_warnings"] += 1
        elif kind == "boss_teleport_arrived":
            active["teleport_arrivals"] += 1
        elif kind == "boss_teleport_aborted":
            active["teleport_aborts"] += 1
        elif kind == "boss_world_scan_warning":
            active["world_scans"] += 1
        elif kind == "boss_defeated":
            active["outcome"] = "besiegt"
            active["ended_ms"] = ms
            active["duration_ms"] = max(0, int(ms - active["started_ms"]))
            fights.append(active)
            active = None
    if active:
        active["outcome"] = "offen / Runde beendet"
        if events:
            end_ms = events[-1].get("ms", active["started_ms"])
            if isinstance(end_ms, (int, float)):
                active["duration_ms"] = max(0, int(end_ms - active["started_ms"]))
        fights.append(active)
    items = {}
    for event in events:
        if not isinstance(event, dict) or event.get("type") != "item_applied":
            continue
        data = event.get("data") or {}
        item = str(data.get("item", "unbekannt"))
        summary = items.setdefault(item, {
            "applied": 0, "last_before": None, "last_after": None,
            "source_code": "Dark_Snake/modules/game.py::Game.handle_item_pickup",
        })
        summary["applied"] += 1
        summary["last_before"] = data.get("before")
        summary["last_after"] = data.get("after")
    heatmap = {}
    for key, counter in visits.items():
        heatmap[key] = [
            {"x": x, "y": y, "samples": count}
            for (x, y), count in sorted(counter.items(), key=lambda pair: (pair[0][1], pair[0][0]))
        ]
    return {
        "schema_version": 1,
        "grid": [width, height],
        "sample_interval_ms": 250,
        "sample_count": len(samples),
        "event_count": len(events),
        "dropped_events": report.get("dropped_events", 0),
        "dropped_samples": report.get("dropped_samples", 0),
        "event_counts": dict(sorted(counts.items())),
        "fights": fights,
        "zones_sampled": dict(sorted(zones.items())),
        "items": items,
        "heatmap": heatmap,
        "feedback": report.get("feedback", []),
        "warnings": [
            "Rasterkarte basiert auf 250-ms-Stichproben, nicht auf jedem Frame.",
            "Phasen-/Teleportdauer aus zeitgestempelten Events; keine automatische Qualitätswertung.",
            "Subjektives Spielerlebnis ausschließlich aus freiwilligem Feedback.",
            "Bei verlorenen Events/Samples sind Aussagen unvollständig.",
        ],
    }


def _html(value):
    return escape(str(value), quote=True)


def _heatmap_svg(report, analysis):
    w, h = analysis["grid"]
    source = (report.get("context") or {}).get("vision_blockers") or []
    obstacles = []
    for cell in source[:5000]:
        point = _point(cell, w, h)
        if point is not None:
            obstacles.append(f'<rect x="{point[0]}" y="{point[1]}" width="1" height="1" fill="#273c53" opacity=".85"/>')
    layers = []
    for key, color in (("p1", "#72e4ac"), ("p2", "#8cddff"), ("boss", "#d18dff")):
        cells = analysis["heatmap"][key]
        peak = max((c["samples"] for c in cells), default=1)
        for c in cells:
            opacity = min(.92, .18 + .74 * log1p(c["samples"]) / log1p(peak))
            layers.append(
                f'<rect x="{c["x"]}" y="{c["y"]}" width="1" height="1" '
                f'fill="{color}" opacity="{opacity:.2f}"/>'
            )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="Raster-Heatmap der aufgezeichneten Aufenthaltsproben" '
            f'viewBox="0 0 {w} {h}" preserveAspectRatio="xMidYMid meet">'
            f'<defs><pattern id="grid" width="1" height="1" patternUnits="userSpaceOnUse">'
            f'<path d="M 1 0 L 0 0 0 1" fill="none" stroke="#516177" stroke-width=".035"/>'
            f'</pattern></defs><rect width="{w}" height="{h}" fill="#0b1425"/>'
            + "".join(obstacles) + "".join(layers)
            + f'<rect width="{w}" height="{h}" fill="url(#grid)"/></svg>')


def render_html(report, analysis=None):
    """Static, entirely local HTML with escaped comments; no external requests."""
    if analysis is None:
        analysis = analyze_report(report)
    rid = _html(report.get("round_id", "?"))
    context = report.get("context") or {}
    fight_html = []
    for i, fight in enumerate(analysis["fights"], 1):
        phases = ", ".join(
            f'{p["phase"]}@{p["ms"] / 1000:.2f}s'
            for p in fight["phase_events"] if p["type"] == "boss_phase_active"
        ) or "keine Phasenaktivierung im Log"
        duration = (f'{fight["duration_ms"] / 1000:.2f}s'
                    if fight["duration_ms"] is not None else "unbekannt")
        fight_html.append(
            "<section class='card'><h3>" + _html(f'Boss {i}: {fight["boss"]}')
            + "</h3><p>" + _html(f'Level {fight["level"]} · {fight["outcome"]} · {duration}')
            + "</p><p>Phasen: " + _html(phases)
            + "</p><p>" + _html(
                f'Teleport: {fight["teleport_arrivals"]}/{fight["teleport_warnings"]} Ankünfte/Warnungen; '
                f'{fight["teleport_aborts"]} Abbrüche; {fight["world_scans"]} Welt-Suchen.'
            ) + "</p><p>" + _html(f'Boss-Schadensereignisse: {fight["damage_events"]}, '
                                    f'Gesamtschaden: {fight["damage_to_boss"]}') + "</p></section>"
        )
    feedback_html = []
    for item in analysis["feedback"]:
        if not isinstance(item, dict):
            continue
        feedback_html.append("<li><b>" + _html(item.get("subject", "?"))
                             + "</b> · Bewertung " + _html(item.get("rating", "–"))
                             + "/5 · " + _html(item.get("note", ""))
                             + " · " + _html(", ".join(item.get("item_verdict") or []))
                             + "</li>")
    events_html = []
    for event in (report.get("events") or []):
        if not isinstance(event, dict) or event.get("type") not in RELEVANT_EVENTS:
            continue
        if len(events_html) >= 200:
            break
        ms = event.get("ms", 0)
        events_html.append("<tr><td>" + _html(f'{ms / 1000:.2f}s' if isinstance(ms, (float, int)) else ms)
                           + "</td><td>" + _html(event.get("type"))
                           + "</td><td><code>" + _html(event.get("data", {}))
                           + "</code></td></tr>")
    items_html = []
    for item, details in analysis["items"].items():
        items_html.append("<li><b>" + _html(item) + "</b>: "
                          + _html(details["applied"]) + "× angewendet; "
                          + _html(details["source_code"]) + "</li>")
    style = """body{margin:0;background:#091324;color:#d9ebf1;font:16px system-ui,sans-serif}
    main{max-width:1100px;margin:auto;padding:24px}h1,h2{color:#9edee6}
    .card{background:#14233a;border:1px solid #467c91;border-radius:10px;padding:14px;margin:12px 0}
    .map{background:#0b1425;border:1px solid #476075;border-radius:8px;padding:8px}
    svg{width:100%;height:auto;image-rendering:pixelated;max-height:650px}
    table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #35506b;padding:8px;text-align:left;vertical-align:top}
    code{overflow-wrap:anywhere;font-size:12px} .muted{color:#acc2d1}
    .legend span{margin-right:16px} @media(max-width:600px){main{padding:10px}table{font-size:12px}}"""
    return ("<!doctype html><html lang='de'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Irians Auge · Rundenanalyse</title><style>" + style + "</style>"
            "<main><h1>Irians Auge · DEV+ Rundenanalyse</h1><p class='muted'>"
            + "Runden-ID: " + rid + " · Start " + _html(report.get("started_at"))
            + " · Ende " + _html(report.get("finished_at"))
            + " · Status " + _html(report.get("finish_reason")) + "</p>"
            + "<section class='card'><b>Rundenkontext</b><p>" +
            _html(f'Classic · {context.get("players", "?")} Spieler · '
                  f'Welt {context.get("world") or "Standard"} · '
                  f'{analysis["event_count"]} Events · {analysis["sample_count"]} Positionsproben')
            + "</p></section><h2>Bosskämpfe</h2>"
            + "".join(fight_html or ["<p>Keine Boss-Spawn-Ereignisse im Bericht.</p>"])
            + "<h2>Bewegungskarte / Aufenthaltsproben</h2><p class='legend'>"
            "<span style='color:#72e4ac'>■ Spieler 1</span>"
            "<span style='color:#8cddff'>■ Spieler 2</span>"
            "<span style='color:#d18dff'>■ Boss</span>"
            "<span style='color:#8b99a7'>■ Sichtblocker</span></p>"
            "<div class='map'>" + _heatmap_svg(report, analysis) + "</div>"
            "<p class='muted'>Stichprobe alle 250 ms, keine Echtzeit-Hitbox-Karte. "
            "Graue Zellen sind Sichtblocker, nicht zwingend physische Wände.</p>"
            "<h2>Spielerfeedback</h2><ul>" + "".join(feedback_html or ["<li>Keine freiwillige Bewertung.</li>"])
            + "</ul><h2>Item-Wirkungen</h2><ul>" + "".join(items_html or ["<li>Keine Item-Anwendungen aufgezeichnet.</li>"])
            + "</ul><h2>Ereignis-Zeitachse (Auszug)</h2><table><thead><tr>"
            "<th>Zeit</th><th>Ereignis</th><th>Daten</th></tr></thead><tbody>"
            + "".join(events_html) + "</tbody></table>"
            + "<h2>Datenqualität</h2><p>" + _html(
                f'Verworfene alte Events: {analysis["dropped_events"]}; '
                f'verworfene Positionsproben: {analysis["dropped_samples"]}. '
                'Keine KI-Fühlensbehauptung, nur explizite Spielerbewertungen.')
            + "</p><p class='muted'>Lokaler Entwicklerbericht – keine Cookies, "
            "kein JavaScript, kein Tracking oder Upload.</p></main></html>")
