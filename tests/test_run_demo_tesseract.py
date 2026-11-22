"""run_demo finds Tesseract in a standard Windows folder when it is not on PATH."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_demo  # noqa: E402


def test_folder_with_tesseract_is_added_to_path(tmp_path, monkeypatch) -> None:
    name = "tesseract.exe" if os.name == "nt" else "tesseract"
    exe = tmp_path / name
    exe.write_text("")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(run_demo, "Path", Path)
    # on Windows the check looks for tesseract.exe, elsewhere the test only covers the missing case
    if os.name == "nt":
        assert run_demo.ensure_tesseract((str(tmp_path),)) is True
        assert shutil.which("tesseract") is not None


def test_missing_tesseract_returns_false(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PATH", "")
    assert run_demo.ensure_tesseract((str(tmp_path),)) is False
