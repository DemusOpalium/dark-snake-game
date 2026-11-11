from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Dark_Snake"))

from modules import resources, simulation_reports


REPORT_TIME = datetime(2026, 11, 11, 18, 30, 42)


def save_sample(directory=None, *, marker="Erfolgreich"):
    return simulation_reports.save_reports(
        f"{marker}\n",
        json.dumps({"marker": marker}, ensure_ascii=False),
        scenario="classic_1p",
        seed=42,
        directory=directory,
        now=REPORT_TIME,
    )


@pytest.fixture
def frozen_layout(tmp_path, monkeypatch):
    install = tmp_path / "DARK Snake"
    bundle = tmp_path / "_MEI0001"
    data = tmp_path / "profile" / ".dark-snake"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setattr(sys, "executable", str(install / "DARK-Snake.exe"))
    monkeypatch.setattr(resources, "DATA_DIR", data)
    return install / "Entwicklerberichte", data / "Entwicklerberichte", bundle


def test_frozen_reports_use_portable_directory_not_cwd_or_bundle(frozen_layout, monkeypatch, tmp_path):
    preferred, fallback, bundle = frozen_layout
    monkeypatch.chdir(tmp_path)

    assert simulation_reports.report_directory() == preferred
    txt, json_path = save_sample(marker="Überprüfung")

    assert txt.parent == json_path.parent == preferred
    assert txt.name == "simulation-report-classic-1p-2026-11-11_18-30-42-seed-42.txt"
    assert txt.read_text(encoding="utf-8") == "Überprüfung\n"
    assert json.loads(json_path.read_text(encoding="utf-8")) == {"marker": "Überprüfung"}
    assert not fallback.exists()
    assert not bundle.exists()


def test_source_reports_default_to_user_data(tmp_path, monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(resources, "DATA_DIR", tmp_path / ".dark-snake")

    assert save_sample()[0].parent == tmp_path / ".dark-snake" / "Entwicklerberichte"


def test_open_folder_resolves_read_only_install_to_user_data(frozen_layout, monkeypatch):
    preferred, fallback, _ = frozen_layout
    original_temporary_file = simulation_reports.TemporaryFile

    def deny_portable_probe(*, dir):
        if dir == preferred:
            raise PermissionError("read-only installation")
        return original_temporary_file(dir=dir)

    monkeypatch.setattr(simulation_reports, "TemporaryFile", deny_portable_probe)

    assert simulation_reports.report_directory() == fallback


def test_failed_portable_write_removes_partial_pair_and_uses_user_data(frozen_layout, monkeypatch):
    preferred, fallback, _ = frozen_layout
    original_open = Path.open

    def deny_portable_json(path, mode="r", *args, **kwargs):
        if mode == "x" and path.parent == preferred and path.suffix == ".json":
            raise PermissionError("installation became read-only")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", deny_portable_json)

    assert save_sample()[0].parent == fallback
    assert list(preferred.iterdir()) == []
    with pytest.raises(PermissionError):
        save_sample(preferred)


def test_explicit_bundle_output_is_rejected_before_creating_a_directory(frozen_layout):
    _, _, bundle = frozen_layout
    with pytest.raises(OSError, match="PyInstaller"):
        save_sample(bundle / "Entwicklerberichte")
    assert not bundle.exists()


def test_same_timestamp_never_overwrites_an_existing_pair(tmp_path):
    txt1, json1 = save_sample(tmp_path, marker="zuerst")
    txt2, json2 = save_sample(tmp_path, marker="danach")

    assert txt1.stem == json1.stem
    assert txt2.stem == json2.stem == f"{txt1.stem}-1"
    assert txt1.read_text(encoding="utf-8") == "zuerst\n"
    assert json.loads(json1.read_text(encoding="utf-8"))["marker"] == "zuerst"


def test_concurrent_exports_reserve_distinct_complete_pairs(tmp_path):
    markers = tuple(f"Ergebnis {index}" for index in range(8))
    with ThreadPoolExecutor(max_workers=len(markers)) as executor:
        pairs = tuple(executor.map(lambda marker: save_sample(tmp_path, marker=marker), markers))

    assert len(set(pairs)) == len(markers)
    for (txt, json_path), marker in zip(pairs, markers):
        assert txt.stem == json_path.stem
        assert txt.read_text(encoding="utf-8") == f"{marker}\n"
        assert json.loads(json_path.read_text(encoding="utf-8"))["marker"] == marker


def test_latest_report_uses_complete_pairs_across_directories(frozen_layout):
    preferred, fallback, _ = frozen_layout
    assert simulation_reports.latest_report() is None
    assert not preferred.exists() and not fallback.exists()
    old_pair = save_sample(preferred)
    latest_pair = save_sample(fallback)
    for timestamp, paths in enumerate((old_pair, latest_pair), start=1_800_000_000):
        for path in paths:
            os.utime(path, (timestamp, timestamp))
    orphan = preferred / "simulation-report-incomplete.json"
    orphan.write_text("{}", encoding="utf-8")
    os.utime(orphan, (1_900_000_000, 1_900_000_000))

    assert simulation_reports.latest_report() == latest_pair
