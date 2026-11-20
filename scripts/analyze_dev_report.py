"""Create a local static report from an Irians Auge JSON; no game required.

Example:
  python scripts/analyze_dev_report.py path/to/dev-round-<id>.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))
from modules.dev_analysis import analyze_report, render_html


def main():
    parser = argparse.ArgumentParser(description="Irians Auge – offline Bossfight map")
    parser.add_argument("report", type=Path, help="Dev-Runden-JSON")
    parser.add_argument("--html", type=Path, default=None, help="Optional HTML-Ziel")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    output = args.html or args.report.with_suffix(".html")
    output.write_text(render_html(report, analyze_report(report)), encoding="utf-8")
    print(f"Offline-Analyse erstellt: {output}")


if __name__ == "__main__":
    main()
