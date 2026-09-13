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


def bundled_path(*parts: str) -> str:
    return str(ROOT.joinpath(*parts))


def user_data_path(filename: str) -> str:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return str(DATA_DIR / filename)
    except OSError:
        # Read-only or restricted home directories still permit portable use.
        return bundled_path(filename)
