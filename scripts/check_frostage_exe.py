"""Verify the FrostAge catalogue and exact PNG bytes inside a PyInstaller EXE."""

import argparse
import hashlib
import json
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader


CATALOG_PATH = "assets/graphics/frostage/catalog.json"
EXPECTED_PNG_COUNT = 175


def check(executable: Path) -> None:
    archive = CArchiveReader(str(executable))
    names = {name.replace("\\", "/"): name for name in archive.toc}
    if CATALOG_PATH not in names:
        raise ValueError(f"FrostAge catalogue missing from {executable.name}.")
    entries = json.loads(archive.extract(names[CATALOG_PATH]))["assets"]
    if len(entries) != EXPECTED_PNG_COUNT:
        raise ValueError(f"Expected {EXPECTED_PNG_COUNT} catalogue entries, found {len(entries)}.")

    for entry in entries:
        path = f"assets/graphics/frostage/{entry['file']}"
        if path not in names:
            raise ValueError(f"Missing from EXE: {path}")
        digest = hashlib.sha256(archive.extract(names[path])).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"Hash mismatch in EXE: {path}")
    pyz = archive.open_embedded_archive(next(name for name in archive.toc if name.lower().endswith(".pyz")))
    if not {"modules.frostage_assets", "modules.graphic_objects"} <= pyz.toc.keys():
        raise ValueError("FrostAge runtime modules missing from EXE.")
    print(f"Verified catalogue and {len(entries)} FrostAge PNGs inside {executable.name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    check(parser.parse_args().executable)
