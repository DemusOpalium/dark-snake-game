"""Package a Windows PyInstaller build for GitHub Releases."""

import argparse
from importlib.metadata import distribution
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile


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
https://github.com/pyinstaller/pyinstaller
"""


def package_windows(executable: Path, output: Path) -> None:
    with executable.open("rb") as source:
        if source.read(2) != b"MZ":
            raise ValueError(f"Keine Windows-EXE: {executable}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(executable, "DARK-Snake.exe")
        archive.writestr("SPIELSTART.txt", START_GUIDE.encode("utf-8-sig"))
        archive.write(ROOT / "LICENSE", "LICENSE.txt")
        python_license = Path(sys.base_prefix) / "LICENSE.txt"
        archive.write(python_license, "Lizenzen/Python-LICENSE.txt")
        for name in ("pygame", "pyinstaller"):
            package = distribution(name)
            for file in package.files or ():
                if file.name.upper().startswith(("LICENSE", "COPYING")):
                    archive.write(package.locate_file(file), f"Lizenzen/{name}/{file.name}")

    with ZipFile(output) as archive:
        damaged_file = archive.testzip()
        if damaged_file:
            raise ValueError(f"Beschädigter ZIP-Eintrag: {damaged_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("zip", type=Path)
    args = parser.parse_args()
    package_windows(args.exe, args.zip)
