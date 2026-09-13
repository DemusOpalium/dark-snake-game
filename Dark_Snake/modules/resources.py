"""Central paths for source checkouts and frozen PyInstaller builds."""

from pathlib import Path
import sys


def application_root() -> Path:
    """Return the directory containing bundled game data."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


ROOT = application_root()
ASSETS = ROOT / "assets"
DATA_DIR = Path.home() / ".dark-snake"


def asset_path(*parts: str) -> str:
    return str(ASSETS.joinpath(*parts))


def asset_roots() -> tuple[Path, ...]:
    """Return existing asset roots in lookup order (frozen and source builds)."""
    candidates = [ASSETS]
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        candidates.insert(0, Path(frozen_root) / "assets")
    source_assets = Path(__file__).resolve().parents[1] / "assets"
    candidates.append(source_assets)
    return tuple(dict.fromkeys(path.resolve() for path in candidates))


def find_asset(*parts: str) -> Path:
    """Resolve an asset across PyInstaller and repository layouts."""
    for root in asset_roots():
        candidate = root.joinpath(*parts)
        if candidate.is_file():
            return candidate
    return asset_roots()[0].joinpath(*parts)


def find_asset_directory(*parts: str) -> Path:
    """Resolve a bundled directory without relying on the working directory."""
    for root in asset_roots():
        candidate = root.joinpath(*parts)
        if candidate.is_dir():
            return candidate
    return asset_roots()[0].joinpath(*parts)


def bundled_path(*parts: str) -> str:
    return str(ROOT.joinpath(*parts))


def user_data_path(filename: str) -> str:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return str(DATA_DIR / filename)
    except OSError:
        # Read-only or restricted home directories still permit portable use.
        return bundled_path(filename)
