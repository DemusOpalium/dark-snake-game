"""Verify the FrostAge art, World Studio buttons and roof demo inside a PyInstaller EXE."""

import argparse
import hashlib
import json
from pathlib import Path

from PyInstaller.archive.readers import CArchiveReader


CATALOG_PATH = "assets/graphics/frostage/catalog.json"
ROOF_DEMO_PATH = "assets/levels/frostage_roof_demo.json"
EDITOR_UI_DIR = "assets/graphics/editor_ui/"
D20_HUD_PATH = "assets/graphics/hud/Random_D20-removebg-preview.png"
ABYSS_ART_PATH = "assets/graphics/game_over/dark_abyss.png"
ABYSS_RITES_PATH = "assets/text/game_over_rites.json"
DEATH_SOUL_PATH = "assets/graphics/death/soul_of_fallen.png"
SKINS_CATALOG_PATH = "assets/graphics/skins_catalog.json"
SKIN_REGISTRY_PATH = "assets/graphics/skin_registry.json"
DEATH_FOG_PATHS = tuple(f"assets/graphics/death/fog_{index:02}.png" for index in (1, 2, 3))
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
    editor_catalog = EDITOR_UI_DIR + "catalog.json"
    if editor_catalog not in names:
        raise ValueError("World Studio button catalogue missing from EXE.")
    editor_data = json.loads(archive.extract(names[editor_catalog]))
    buttons = editor_data["buttons"]
    if not buttons:
        raise ValueError("World Studio button catalogue is empty.")
    aliases = editor_data.get("aliases", {})
    if not isinstance(aliases, dict) or any(
        action in buttons or not isinstance(target, str) or target not in buttons
        for action, target in aliases.items()
    ):
        raise ValueError("World Studio button catalogue contains invalid artwork aliases.")
    expected_buttons = {EDITOR_UI_DIR + entry["file"] for entry in buttons.values()}
    packaged_buttons = {name for name in names if name.startswith(EDITOR_UI_DIR) and name.endswith(".png")}
    if expected_buttons != packaged_buttons:
        raise ValueError("Packaged World Studio buttons differ from the catalogue.")
    for entry in buttons.values():
        path = EDITOR_UI_DIR + entry["file"]
        if hashlib.sha256(archive.extract(names[path])).hexdigest() != entry["sha256"]:
            raise ValueError(f"Hash mismatch in EXE: {path}")
    if D20_HUD_PATH not in names:
        raise ValueError("Random D20 HUD artwork missing from Windows EXE.")
    original = Path(__file__).resolve().parents[1] / "Dark_Snake" / D20_HUD_PATH
    actual_hash = hashlib.sha256(archive.extract(names[D20_HUD_PATH])).hexdigest()
    expected_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError("Random D20 HUD artwork in EXE does not match source.")
    # Dark Abyss is a real offline, bundled Game Over background, not GamePICs staging.
    for asset in (ABYSS_ART_PATH, ABYSS_RITES_PATH):
        if asset not in names:
            raise ValueError(f"Dark Abyss runtime asset missing from EXE: {asset}")
        original = Path(__file__).resolve().parents[1] / "Dark_Snake" / asset
        digest = hashlib.sha256(archive.extract(names[asset])).hexdigest()
        if digest != hashlib.sha256(original.read_bytes()).hexdigest():
            raise ValueError(f"Dark Abyss asset in EXE differs: {asset}")
    if not json.loads(archive.extract(names[ABYSS_RITES_PATH])).get("common"):
        raise ValueError("Dark Abyss epitaph library must be non-empty.")
    if DEATH_SOUL_PATH not in names:
        raise ValueError("Soul of the Fallen missing from bundled Windows EXE.")
    original_soul = Path(__file__).resolve().parents[1] / "Dark_Snake" / DEATH_SOUL_PATH
    if (hashlib.sha256(archive.extract(names[DEATH_SOUL_PATH])).hexdigest()
            != hashlib.sha256(original_soul.read_bytes()).hexdigest()):
        raise ValueError("Packaged Soul of the Fallen PNG does not match runtime asset.")
    for fog_path in DEATH_FOG_PATHS:
        if fog_path not in names:
            raise ValueError(f"Death Transition fog missing from Windows EXE: {fog_path}")
        original_fog = Path(__file__).resolve().parents[1] / "Dark_Snake" / fog_path
        actual_hash = hashlib.sha256(archive.extract(names[fog_path])).hexdigest()
        expected_hash = hashlib.sha256(original_fog.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"Death Transition fog PNG differs in EXE: {fog_path}")
    # The new Snake Gallery must use bundled runtime sprites, never GamePICs/.
    if SKINS_CATALOG_PATH not in names:
        raise ValueError("Skin provenance catalogue missing from Windows EXE.")
    skin_catalog = json.loads(archive.extract(names[SKINS_CATALOG_PATH]))
    candidates = skin_catalog.get("candidates", [])
    if len(candidates) != 68:
        raise ValueError(f"Expected 68 staged skin candidates, found {len(candidates)}.")
    runtime_skins = [skin for skin in candidates if skin["runtime_asset"]]
    if len(runtime_skins) != 64:
        raise ValueError(f"Expected 64 available staged sprites, found {len(runtime_skins)}.")
    for skin in runtime_skins:
        archive_path = "assets/" + skin["runtime_asset"]
        if archive_path not in names:
            raise ValueError(f"Skin missing from bundled EXE: {archive_path}")
        content = archive.extract(names[archive_path])
        digest = hashlib.sha1(
            f"blob {len(content)}".encode("ascii") + bytes([0]) + content
        ).hexdigest()
        if digest != skin["git_blob_sha"]:
            raise ValueError(f"Skin source differs in EXE: {archive_path}")
    print(f"Verified {len(runtime_skins)} staged Head/Body sprites in Windows EXE.")
    if SKIN_REGISTRY_PATH not in names:
        raise ValueError("Skin unlock registry missing from Windows EXE.")
    registry_data = json.loads(archive.extract(names[SKIN_REGISTRY_PATH]))
    if registry_data.get("schema_version") != 1:
        raise ValueError("Unexpected unlock registry schema in Windows EXE.")
    skins = registry_data.get("skins", [])
    if len(skins) != 92:
        raise ValueError(f"Expected 92 registered Snake skins, found {len(skins)}.")
    known = set()
    for skin in skins:
        folder = ("SnakeHeadsbibliothek" if skin["type"] == "head"
                  else "SnakeBodysBibliothek")
        archive_path = f"assets/graphics/{folder}/{skin['filename']}"
        if archive_path in known or archive_path not in names:
            raise ValueError(f"Duplicate/missing unlocked Snake runtime asset: {archive_path}")
        known.add(archive_path)
    if sum(s["group"] == "starter" for s in skins) != 6:
        raise ValueError("Incorrect number of default-free Snake skins.")
    print("Verified 92 registered runtime Snake Heads/Bodies and unlock metadata.")

    if ROOF_DEMO_PATH not in names:
        raise ValueError(f"Roof demo missing from {executable.name}.")
    demo = json.loads(archive.extract(names[ROOF_DEMO_PATH]))
    if not demo.get("roofs") or not demo.get("collision"):
        raise ValueError("Packaged roof demo has no roof or collision layer.")
    pyz = archive.open_embedded_archive(next(name for name in archive.toc if name.lower().endswith(".pyz")))
    if not {"modules.frostage_assets", "modules.graphic_objects", "modules.roof_render",
            "modules.roof_settings", "modules.roof_editor_settings"} <= pyz.toc.keys():
        raise ValueError("FrostAge runtime modules missing from EXE.")
    if not {"modules.border_builder", "modules.border_builder_ui", "modules.editor_buttons"} <= pyz.toc.keys():
        raise ValueError("World Studio runtime modules missing from EXE.")
    print(f"Verified {len(entries)} FrostAge PNGs, {len(buttons)} editor button PNGs "
          f"({len(buttons) + len(aliases)} actions) and roof demo inside {executable.name}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    check(parser.parse_args().executable)
