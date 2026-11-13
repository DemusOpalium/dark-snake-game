"""Generate and verify the FrostAge source catalogue and runtime PNG copies."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "GamePICs" / "Incoming" / "Frost_Tiles"
RUNTIME = ROOT / "Dark_Snake" / "assets" / "graphics" / "frostage"

SOURCE_COUNTS = {
    "10x1": 5, "1x1": 35, "1x10": 5, "2x1": 11, "2x2": 17, "4x4": 21,
    "5x5": 4, "6x6": 3, "8x8": 17, "aoe": 11, "Buttons": 12, "Dach": 8,
    "gegner": 8, "items": 5, "projectile": 13,
}
OTHER_CATEGORIES = {
    "aoe": ("aoe", (1, 1)), "Buttons": ("menu", (3, 1)), "Dach": ("roof", (4, 4)),
    "gegner": ("enemies", (1, 1)), "items": ("items", (1, 1)), "projectile": ("projectiles", (1, 1)),
}
GROUP_IDS = {"Dach": "roof", "gegner": "enemy", "projectile": "projectile", "Buttons": "menu", "items": "item"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def image_metadata(data):
    if len(data) < 33 or data[:8] != PNG_SIGNATURE or data[8:16] != b"\x00\x00\x00\x0dIHDR":
        raise ValueError("Ungültiger PNG-Kopf")
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    image = pygame.image.load(io.BytesIO(data), "image.png")
    if image.get_size() != (width, height):
        raise ValueError("PNG-Kopf und dekodierte Grafik haben verschiedene Abmessungen")
    orientation = "landscape" if width > height else "portrait" if height > width else "square"
    has_alpha = color_type in (4, 6) or image.get_colorkey() is not None or bool(image.get_masks()[3])
    return {
        "width": width,
        "height": height,
        "orientation": orientation,
        "bit_depth": depth,
        "color_type": color_type,
        "has_alpha": has_alpha,
        "transparent_pixels": pygame.mask.from_surface(image, 254).count() < width * height,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def asset_identity(group, stem):
    if match := re.search(r"\((\d+)\)$", stem):
        number = int(match.group(1))
        return f"frostage_{GROUP_IDS.get(group, group)}_{number:03}", number
    prefix = {"Buttons": "Frostbuttons ", "items": "Frost Items "}.get(group)
    if prefix is None or not stem.startswith(prefix):
        raise ValueError(f"Unerwarteter Dateiname: {group}/{stem}")
    name = re.sub(r"[^a-z0-9]+", "_", stem.removeprefix(prefix).lower()).strip("_")
    name = {"singleplayer": "single_player", "statisktic": "statistics", "herz": "heart", "truhe": "chest",
            "froststar": "frost_star"}.get(name, name)
    return f"frostage_{GROUP_IDS[group]}_{name}", None


def placement(group, number, orientation):
    if group in OTHER_CATEGORIES:
        return OTHER_CATEGORIES[group]

    width, height = map(int, group.split("x"))
    if ((width > height and orientation == "portrait")
            or (width < height and orientation == "landscape")):
        width, height = height, width

    # Source families mix surface graphics and props. Their category reflects the motif only.
    if group in {"1x10", "10x1"} or group == "1x1" and 14 <= number <= 26 or group == "2x2" and number == 9:
        category = "walls"
    elif (group in {"2x1", "5x5", "6x6"} or group == "1x1" and number >= 27
          or group == "2x2" and number >= 11 or group == "4x4" and number >= 15
          or group == "8x8" and number >= 9):
        category = "objects"
    else:
        category = "ground"
    return category, (width, height)


def records(source):
    groups = {}
    for path in source.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".png":
            relative = path.relative_to(source)
            if len(relative.parts) != 2:
                raise ValueError(f"Unerwarteter FrostAge-Pfad: {relative}")
            groups.setdefault(relative.parts[0], []).append(path)
    counts = {group: len(paths) for group, paths in groups.items()}
    if counts != SOURCE_COUNTS:
        raise ValueError(f"Die FrostAge-Gruppen weichen vom erwarteten Bestand ab: {counts}")

    ids = set()
    for group, paths in sorted(groups.items()):
        for path in sorted(paths):
            asset_id, number = asset_identity(group, path.stem)
            if asset_id in ids:
                raise ValueError(f"Doppelte FrostAge-ID: {asset_id}")
            ids.add(asset_id)
            data = path.read_bytes()
            try:
                metadata = image_metadata(data)
            except (ValueError, pygame.error) as error:
                raise ValueError(f"{path.name}: {error}") from error
            category, cells = placement(group, number, metadata["orientation"])
            entry = {
                "id": asset_id,
                "source": path.relative_to(ROOT).as_posix(),
                "file": f"{asset_id}.png",
                "category": category,
                "cells": list(cells),
                **metadata,
            }
            yield entry, data


def synchronize(check):
    expected_files = {"catalog.json"}
    entries = []
    failures = []
    if not check:
        RUNTIME.mkdir(parents=True, exist_ok=True)
    for entry, data in records(SOURCE):
        filename = entry["file"]
        expected_files.add(filename)
        entries.append(entry)
        path = RUNTIME / filename
        if not path.is_file() or path.read_bytes() != data:
            if check:
                failures.append(f"Fehlende oder abweichende Laufzeitgrafik: {filename}")
            else:
                path.write_bytes(data)

    manifest = {"version": 1, "assets": sorted(entries, key=lambda entry: entry["id"])}
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    path = RUNTIME / "catalog.json"
    if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
        if check:
            failures.append("Der FrostAge-Katalog entspricht nicht den Quelldateien.")
        else:
            path.write_text(rendered, encoding="utf-8", newline="\n")

    if RUNTIME.is_dir():
        extras = sorted(path.name for path in RUNTIME.iterdir() if path.name not in expected_files)
        if extras:
            failures.append(f"Nicht katalogisierte Dateien im Laufzeitordner: {', '.join(extras)}")
    if failures:
        raise ValueError("\n".join(failures))
    return len(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="Katalog und Laufzeitdateien prüfen")
    action.add_argument("--write", action="store_true", help="Katalog und Laufzeitdateien erzeugen")
    args = parser.parse_args()
    try:
        count = synchronize(check=args.check)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"{count} FrostAge PNG geprüft.")


if __name__ == "__main__":
    main()
