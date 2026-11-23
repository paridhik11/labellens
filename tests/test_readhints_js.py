"""Tests for ui/pro/readhints.js (rules that suggest fields from the text lines the label reader found).

The rules run in node, so the test is skipped where node is not installed. The lines below are written by hand in
the way device labels are usually printed; they are not a measurement on real photos.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

JS = Path(__file__).resolve().parents[1] / "ui" / "pro" / "readhints.js"
pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


def run(expr: str) -> object:
    """Evaluate a JavaScript expression with window.ReadHints loaded and return it as JSON."""
    script = (f"global.window = {{}}; require({json.dumps(str(JS))}); const H = window.ReadHints; "
              f"console.log(JSON.stringify({expr}));")
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def ls(*texts: str) -> str:
    return json.dumps([{"text": t, "conf": 0.95} for t in texts])


@pytest.mark.parametrize(("line", "value"), [
    ("STERILE EO", "EO"), ("Sterilized using ethylene oxide", "EO"), ("STERILE R", "R"),
    ("Sterilized by gamma irradiation", "gamma"), ("Sterile", "Sterile"), ("NON-STERILE", "Non-sterile"),
    ("Sterilized with steam", "steam"),
])
def test_sterilization_reads_common_wordings(line: str, value: str) -> None:
    assert run(f"H.sterilization({ls(line)})")["value"] == value


def test_sterilization_ignores_other_lines() -> None:
    assert run(f"H.sterilization({ls('Golden Pump', 'LOT1', 'Store dry')})") is None


@pytest.mark.parametrize("line", [
    "Store at 2-8 °C", "Storage: keep dry", "Keep away from sunlight", "Protect from moisture", "Store below 25°C",
])
def test_storage_finds_storage_lines(line: str) -> None:
    assert run(f"H.storage({ls(line)})") is not None


def test_storage_drops_the_label_word_and_skips_sterile_lines() -> None:
    assert run(f"H.storage({ls('Storage: keep dry')})")["value"] == "keep dry"
    assert run(f"H.storage({ls('Store sterile in original pack')})") is None


def test_unassigned_keeps_the_line_no_field_accounts_for() -> None:
    texts = ["Golden Pump", "GP-100", "LOT1", "DRAFT, not for production", "TESTDATA|DRAFT"]
    barcode = {"raw": "0100000000000000173006301 0LOT1"}
    ex = {"ocr_blocks": [{"text": t, "conf": 1.0} for t in texts], "barcodes": [barcode]}
    form = {"name": "Golden Pump", "lot": "LOT1", "expiry": "2030-06-30"}
    got = run(f"H.unassigned({json.dumps(ex)}, {json.dumps(form)})")
    assert [x["text"] for x in got] == ["GP-100"]


def test_model_candidate_needs_exactly_one_model_shaped_line() -> None:
    one = [{"text": "GP-100", "conf": 0.99}, {"text": "28件", "conf": 0.2}]
    assert run(f"H.modelCandidate({json.dumps(one)})")["text"] == "GP-100"
    two = [{"text": "GP-100", "conf": 0.99}, {"text": "AB-7", "conf": 0.99}]
    assert run(f"H.modelCandidate({json.dumps(two)})") is None
    assert run(f"H.modelCandidate({json.dumps([{'text': '2030-06-30', 'conf': 1}])})") is None


def test_merge_prefers_a_clear_reading_and_reports_disagreement() -> None:
    a = {"fields": {"product_name": "Golden Pmp", "lot": "LOT1"}, "unclear_fields": ["product_name"],
         "barcodes": [{"raw": "X1"}], "ocr_blocks": [{"text": "Golden Pmp", "conf": 0.5}], "warnings": ["w1"]}
    b = {"fields": {"product_name": "Golden Pump", "expiry": "2030-06-30"}, "unclear_fields": [],
         "barcodes": [{"raw": "X1"}, {"raw": "X2"}],
         "ocr_blocks": [{"text": "Golden Pump", "conf": 0.9}, {"text": "golden pmp", "conf": 0.4}], "warnings": []}
    got = run(f"H.merge([{json.dumps(a)}, {json.dumps(b)}])")
    assert got["fields"] == {"product_name": "Golden Pump", "lot": "LOT1", "expiry": "2030-06-30"}
    assert got["unclear_fields"] == []
    assert list(got["conflicts"]) == ["product_name"]
    assert [x["raw"] for x in got["barcodes"]] == ["X1", "X2"]
    assert len(got["ocr_blocks"]) == 2  # "golden pmp" repeats the first line without case or spaces
    assert got["warnings"] == ["Image 1: w1"]


def test_merge_of_one_reading_is_unchanged() -> None:
    a = {"fields": {"lot": "L"}, "unclear_fields": [], "barcodes": [], "ocr_blocks": []}
    assert run(f"H.merge([{json.dumps(a)}])") == a
