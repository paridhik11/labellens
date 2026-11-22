"""The NDC glue of the public scan (no OCR, no network): barcode first, printed NDC next, method E otherwise."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from src.api import medicine, ndc_glue

CODE = "69367035901"  # recorded: package NDC of one corpus product
CATALOG = medicine.MedicineCatalog()
SETID = next(iter(ndc_glue.resources()["table"][CODE]))
NAME = next(p.name for p in CATALOG.products.values() if p.setid == SETID)
SERVICE = SimpleNamespace(catalog=CATALOG, matcher=SimpleNamespace(threshold=0.65))
PHOTO = Path("unused.jpg")


def never(*_: Any) -> Any:
    raise AssertionError("must not run")


def e_none(reading: dict[str, Any]) -> dict[str, Any]:
    return {"outcome": "no_reference_match", "reason": "no_match", "best": None, "tried": 0, "timed_out": False}


def test_barcode_ndc_ends_the_scan_before_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ndc_glue, "safe_barcode_ndcs", lambda path: [CODE])
    body, extra = ndc_glue.scan_with_ndc(PHOTO, SERVICE, never, never)
    assert body["outcome"] == "matched" and body["candidates"][0]["product_name"] == NAME
    assert body["matched_text"].startswith("NDC barcode") and extra["source"] == "ndc_barcode"


def test_printed_ndc_wins_without_method_e(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ndc_glue, "safe_barcode_ndcs", lambda path: [])
    lines = [{"text": "NDC 69367-359-01", "confidence": 0.9, "box": [0, 0, 1, 1]}]
    body, extra = ndc_glue.scan_with_ndc(PHOTO, SERVICE, lambda p: {"lines": lines, "complete": True}, never)
    assert body["outcome"] == "matched" and extra["source"] == "ndc_printed"
    assert body["read_lines"][0]["text"] == "NDC 69367-359-01"


def test_unknown_ndc_leaves_the_decision_to_method_e(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ndc_glue, "safe_barcode_ndcs", lambda path: ["00000000001"])
    lines = [{"text": "zzz qqq", "confidence": 0.9, "box": [0, 0, 1, 1]}]
    body, extra = ndc_glue.scan_with_ndc(PHOTO, SERVICE, lambda p: {"lines": lines, "complete": True}, e_none)
    assert body["outcome"] == "no_reference_match" and body["candidates"] == [] and extra["source"] == "none"
