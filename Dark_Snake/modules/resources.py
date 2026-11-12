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


def installation_root() -> Path:
    """Locate the portable game directory or the source project directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[2]


def simulation_report_directories() -> tuple[Path, ...]:
    """Prefer the portable EXE directory, with a user data fallback."""
    fallback = DATA_DIR / "Entwicklerberichte"
    if getattr(sys, "frozen", False):
        return (installation_root() / "Entwicklerberichte", fallback)
    return (fallback,)


def is_temporary_bundle_path(path: Path) -> bool:
    """Identify paths inside PyInstaller's temporary resource directory."""
    bundle = getattr(sys, "_MEIPASS", None)
    return bool(bundle and path.resolve().is_relative_to(Path(bundle).resolve()))


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


def custom_level_path(*, for_write: bool = False) -> str:
    saved = Path(user_data_path("custom_level.json"))
    if for_write or saved.is_file():
        return str(saved)
    return asset_path("levels", "custom_level.json")


def level_drafts_directory() -> Path:
    """Keep named drafts in persistent user data, independent of Classic's map."""
    directory = (DATA_DIR / "levels").resolve()
    if is_temporary_bundle_path(directory):
        raise OSError("Levelentwürfe können nicht im temporären Spielordner gespeichert werden.")
    return directory
