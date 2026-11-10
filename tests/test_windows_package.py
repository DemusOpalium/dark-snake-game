import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from scripts import package_windows


def test_zip_is_stable_and_contains_verifiable_provenance(tmp_path, monkeypatch):
    exe = tmp_path / "game.exe"
    image = b"MZ" + bytes(58) + (64).to_bytes(4, "little") + b"PE\0\0\x64\x86"
    exe.write_bytes(image)
    python_license = tmp_path / "LICENSE.txt"
    python_license.write_text("Test Python license", encoding="utf-8")
    monkeypatch.setattr(package_windows.sys, "base_prefix", str(tmp_path))
    monkeypatch.setattr(package_windows, "distribution", lambda name: SimpleNamespace(version="1.0", files=[]))

    source_commit = "0" * 40
    first = tmp_path / "a" / "DARK-Snake.zip"
    second = tmp_path / "b" / first.name
    package_windows.package_windows(exe, first, source_commit)
    os.utime(exe, (1_700_000_000, 1_700_000_000))
    package_windows.package_windows(exe, second, source_commit)

    assert first.read_bytes() == second.read_bytes()
    digest = hashlib.sha256(first.read_bytes()).hexdigest()
    assert first.with_suffix(".zip.sha256").read_bytes() == f"{digest}  {first.name}\n".encode()
    with ZipFile(first) as archive:
        assert archive.testzip() is None
        assert archive.read("DARK-Snake.exe") == image
        assert archive.read("LICENSE.txt") == (Path(package_windows.ROOT) / "LICENSE").read_bytes()
        assert b"LESSER GENERAL PUBLIC LICENSE" in archive.read("Lizenzen/pygame/LGPL.txt")
        manifest = json.loads(archive.read("BUILD.json"))
        assert manifest["source_commit"] == source_commit
        assert manifest["executable_sha256"] == hashlib.sha256(image).hexdigest()


def test_package_rejects_a_non_x64_image(tmp_path):
    executable = tmp_path / "wrong.exe"
    executable.write_bytes(b"MZ" + bytes(58) + (64).to_bytes(4, "little") + b"PE\0\0\x4c\x01")
    with pytest.raises(ValueError, match="x64"):
        package_windows.package_windows(executable, tmp_path / "wrong.zip", "0" * 40)
