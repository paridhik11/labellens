"""Check photo reports without requiring OCR models or downloaded photo data."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.cv import eval_real


def test_photo_failures_and_unreadable_references(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep failed extractions in denominators and skip photos without readable references."""
    for name in ("a.jpg", "b.jpg", "blank.jpg", "unlabelled.jpg"):
        (tmp_path / name).write_bytes(b"mock photo")
    (tmp_path / "transcriptions.csv").write_text(
        "filename,product_name,lot,expiry\na.jpg,DEVICE,A1,\nb.jpg,DEVICE,B2,\nblank.jpg,,,\nmissing.jpg,X,,\n"
    )
    extract = Mock(side_effect=[SimpleNamespace(fields={"product_name": "DEVICE", "lot": "LOT: A1"}, barcodes=[]),
                               RuntimeError("test failure")])
    monkeypatch.setitem(sys.modules, "src.cv.extract", SimpleNamespace(extract_label=extract))
    result = eval_real.evaluate(tmp_path)
    assert result is not None
    assert extract.call_count == 2
    assert result["totals"]["lot"]["exact"] == 1
    assert result["totals"]["lot"]["photos"] == 2
    assert result["rows"][0]["scores"]["lot"]["exact"] == 1
    assert "failed" in result["rows"][1]["status"]
    assert "skipped" in result["rows"][2]["status"]
    assert result["transcribed_but_missing"] == ["missing.jpg"]
    report = eval_real.render_report(result, "LLM-labelled")
    assert "Reference source: LLM-labelled" in report
    assert "| a.jpg | ok | lot | A1 | A1 | yes |" in report
    assert "| not transcribed |  | not scored |" in report
    assert "NOT_RUN" in report
    assert "test failure" in report
    assert "missing.jpg" in report


def test_report_cell_escapes_ocr_text() -> None:
    """Prevent text containing separators or newlines from changing table structure."""
    assert eval_real.report_cell("A|B\r\nC") == r"A\|B  C"


def test_cli_writes_labelled_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Save a per-photo report carrying reference provenance without changing CSV columns."""
    result = {"photos": 1, "rows": [{"photo": "blank.jpg", "status": "no readable reference fields, skipped"}],
              "totals": {}, "transcribed_but_missing": []}
    monkeypatch.setattr(eval_real, "evaluate", lambda _: result)
    report = tmp_path / "results/report.md"
    assert eval_real.main(["--folder", str(tmp_path), "--report", str(report),
                           "--reference-source", "LLM-labelled"]) == 0
    assert "LLM-labelled" in report.read_text()
    assert report.read_text().count("not scored") == 4  # Three rows plus the explanatory sentence.
    assert "Per-photo field comparisons saved" in capsys.readouterr().out
