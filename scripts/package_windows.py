"""Package a Windows PyInstaller build for GitHub Releases."""

import argparse
import hashlib
from importlib.metadata import distribution
import json
from pathlib import Path
import re
import shutil
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
START_GUIDE = """DARK Snake – Windows Edition

1. Diese ZIP-Datei vollständig entpacken.
2. Im entpackten Ordner DARK-Snake.exe starten.

Das Spiel ist kostenlos. Python ist in der EXE enthalten.
Im Spiel zeigt das Steuerungsmenü die Tastenbelegung.
F2 öffnet und schließt den Level-Editor.

Projekt, Hilfe und Quellcode:
https://github.com/DemusOpalium/dark-snake-game

Quellcode der mitgelieferten Laufzeitkomponenten:
https://www.python.org/downloads/source/
https://github.com/pygame/pygame/tree/2.6.1
https://github.com/pygame/pygame/tree/2.6.1/docs/licenses
https://github.com/pyinstaller/pyinstaller
"""


def sha256(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def write_member(archive: ZipFile, name: str, content: bytes | Path) -> None:
    # ZIP metadata is independent of source file modification times.
    info = ZipInfo(name)
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    info.compress_type = ZIP_DEFLATED
    if isinstance(content, Path):
        with content.open("rb") as source, archive.open(info, "w") as target:
            shutil.copyfileobj(source, target)
    else:
        archive.writestr(info, content)


def package_windows(executable: Path, output: Path, source_commit: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("Die Quelle braucht einen vollständigen Git-Commit.")
    with executable.open("rb") as source:
        header = source.read(64)
        if len(header) != 64 or header[:2] != b"MZ":
            raise ValueError(f"Keine Windows-EXE: {executable}")
        source.seek(int.from_bytes(header[60:64], "little"))
        if source.read(6) != b"PE\0\0\x64\x86":
            raise ValueError(f"Keine x64-Windows-EXE: {executable}")

    packages = {name: distribution(name) for name in ("pygame", "pyinstaller", "pyinstaller-hooks-contrib")}
    build = {
        "repository": "https://github.com/DemusOpalium/dark-snake-game",
        "source_commit": source_commit,
        "python": sys.version.split()[0],
        "packages": {name: package.version for name, package in packages.items()},
        "executable": "DARK-Snake.exe",
        "executable_sha256": sha256(executable),
    }
    members = {
        "BUILD.json": (json.dumps(build, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "DARK-Snake.exe": executable,
        "LICENSE.txt": ROOT / "LICENSE",
        "Lizenzen/Python-LICENSE.txt": Path(sys.base_prefix) / "LICENSE.txt",
        "Lizenzen/pygame/LGPL.txt": ROOT / "licenses" / "pygame-LGPL.txt",
        "SPIELSTART.txt": START_GUIDE.encode("utf-8-sig"),
    }
    for name, package in packages.items():
        for file in package.files or ():
            if file.name.upper().startswith(("LICENSE", "COPYING")):
                members[f"Lizenzen/{name}/{file.name}"] = Path(package.locate_file(file))

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in sorted(members.items()):
            write_member(archive, name, content)

    with ZipFile(output) as archive:
        damaged_file = archive.testzip()
        if damaged_file:
            raise ValueError(f"Beschädigter ZIP-Eintrag: {damaged_file}")
    output.with_suffix(output.suffix + ".sha256").write_text(
        f"{sha256(output)}  {output.name}\n", encoding="utf-8", newline="\n",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("zip", type=Path)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    package_windows(args.exe, args.zip, args.source_commit)
