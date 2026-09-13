"""Fail fast when unresolved Git merge markers enter tracked text files."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml"}
MARKERS = ("<" * 7, "=" * 7, ">" * 7)


def tracked_text_files(root=ROOT):
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    for raw_name in result.stdout.split(b"\0"):
        if not raw_name:
            continue
        path = root / raw_name.decode("utf-8")
        if path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def find_conflict_markers(root=ROOT):
    findings = []
    for path in tracked_text_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as error:
            findings.append(f"{path.relative_to(root)}: nicht lesbar ({error})")
            continue
        for line_number, line in enumerate(lines, 1):
            if line.startswith(MARKERS):
                findings.append(f"{path.relative_to(root)}:{line_number}: {line}")
    return findings


def main():
    findings = find_conflict_markers()
    if findings:
        print("Nicht aufgelöste Git-Konfliktmarkierungen gefunden:")
        print("\n".join(findings))
        return 1
    print("Keine Git-Konfliktmarkierungen in getrackten Textdateien gefunden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
