"""Directory selection and paired TXT/JSON export for developer simulations."""

from datetime import datetime
from itertools import count
from pathlib import Path
import re
from stat import S_ISREG
from tempfile import TemporaryFile

from modules.resources import is_temporary_bundle_path, simulation_report_directories


def _validated_directory(directory: Path) -> Path:
    path = directory.expanduser().resolve()
    if is_temporary_bundle_path(path):
        raise OSError(f"Temporärer PyInstaller-Ordner: {path}")
    return path


def _prepare_directory(directory: Path) -> Path:
    path = _validated_directory(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path


def report_directory() -> Path:
    """Return a usable default directory, checking permissions by writing."""
    last_error = None
    for candidate in simulation_report_directories():
        try:
            directory = _prepare_directory(candidate)
            with TemporaryFile(dir=directory) as probe:
                probe.write(b"\0")
            return directory
        except OSError as error:
            last_error = error
    raise OSError(f"Kein beschreibbarer Berichtsordner verfügbar ({last_error})") from last_error


def _report_path_pairs(directory: Path, scenario: str, seed: int, now):
    stamp = (now or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")
    slug = re.sub(r"[^a-z0-9-]+", "-", scenario.lower()).strip("-")
    if slug in ("", "alle"):
        slug = "all"
    stem = f"simulation-report-{slug}-{stamp}-seed-{seed}"
    for suffix in count():
        name = stem if suffix == 0 else f"{stem}-{suffix}"
        yield directory / f"{name}.txt", directory / f"{name}.json"


def unique_report_paths(directory: Path, scenario: str, seed: int, now=None):
    """Preview an unused path pair. Saving reserves the paths separately."""
    return next(paths for paths in _report_path_pairs(directory, scenario, seed, now)
                if not any(path.exists() for path in paths))


def _write_pair(paths: tuple[Path, Path], text_report: str, json_report: str):
    txt, json_path = paths
    created = []
    try:
        with txt.open("x", encoding="utf-8") as text_file:
            created.append(txt)
            with json_path.open("x", encoding="utf-8") as json_file:
                created.append(json_path)
                text_file.write(text_report)
                json_file.write(json_report)
    except BaseException:
        for path in created:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def save_reports(
    text_report: str,
    json_report: str,
    *,
    scenario: str,
    seed: int,
    directory: Path | None = None,
    now: datetime | None = None,
) -> tuple[Path, Path]:
    """Save one pair with a shared name, never overwriting existing files."""
    candidates = (Path(directory),) if directory is not None else simulation_report_directories()
    last_error = None
    for candidate in candidates:
        try:
            output = _prepare_directory(candidate)
            for paths in _report_path_pairs(output, scenario, seed, now):
                try:
                    _write_pair(paths, text_report, json_report)
                except FileExistsError:
                    continue
                return paths
        except OSError as error:
            if directory is not None:
                raise
            last_error = error
    raise OSError(f"Kein Berichtsordner konnte verwendet werden ({last_error})") from last_error


def latest_report() -> tuple[Path, Path] | None:
    """Find the newest complete pair, including reports from earlier sessions."""
    latest = None
    latest_key = None
    for candidate in simulation_report_directories():
        try:
            directory = _validated_directory(candidate)
            files = directory.glob("simulation-report-*.json")
            for json_path in files:
                txt = json_path.with_suffix(".txt")
                try:
                    stats = (txt.stat(), json_path.stat())
                except OSError:
                    continue
                if not all(S_ISREG(info.st_mode) and info.st_size for info in stats):
                    continue
                key = (max(info.st_mtime_ns for info in stats), json_path.name)
                if latest_key is None or key > latest_key:
                    latest_key = key
                    latest = (txt, json_path)
        except OSError:
            continue
    return latest
