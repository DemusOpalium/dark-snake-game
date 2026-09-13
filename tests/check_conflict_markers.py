"""Reject unresolved merge artifacts in Python source files."""

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
MARKERS = ("<" * 7, "=" * 7, ">" * 7)
BRANCH_LINE = re.compile(r"^(?:codex/\S+|main)$")


def find_artifacts(root=ROOT):
    for path in root.rglob("*.py"):
        if any(part in {".git", ".venv", "venv"} for part in path.parts):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if any(stripped.startswith(marker) for marker in MARKERS) or BRANCH_LINE.fullmatch(stripped):
                yield path.relative_to(root), number, stripped


def main() -> int:
    artifacts = list(find_artifacts())
    for path, number, line in artifacts:
        print(f"{path}:{number}: verdächtiges Konfliktartefakt: {line}")
    return bool(artifacts)


if __name__ == "__main__":
    sys.exit(main())
