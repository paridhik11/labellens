"""The evaluation tables of src/checker/eval_injected.py, on hand-made result rows (no images, no CV libraries)."""
import numpy as np
import pytest

from src.checker import eval_injected as ev
from src.checker.gs1 import check_digit_ok


def row(kind: str, cond: str, expected: list[str], flags: dict[str, bool], error: str | None = None) -> dict:
    """One result row; flags maps rule id to needs_human."""
    return {"stem": f"{kind}_{cond}", "kind": kind, "condition": cond, "expected": expected, "error": error,
            "flags": {r: {"needs_human": nh, "severity": "review", "cited": True} for r, nh in flags.items()},
            "n_flags": len(flags)}


def test_wilson_cell_format() -> None:
    assert ev.wilson(0, 0) == "n=0"
    cell = ev.wilson(5, 10)
    assert cell.startswith("5/10 = 0.50 [0.24, 0.76]")


def test_recall_counts_flagged_and_confident_separately() -> None:
    rows = [row("wrong_name", "clean", ["P-NAME"], {"P-NAME": False}),
            row("wrong_name", "clean", ["P-NAME"], {"P-NAME": True}),
            row("wrong_name", "clean", ["P-NAME"], {}),
            row("wrong_name", "clean", ["P-NAME"], {}, error="boom")]
    line = next(x for x in ev._recall_table(rows, ("clean",)) if x.startswith("| wrong_name | clean"))
    cells = [c.strip() for c in line.split("|")[1:-1]]
    assert cells[2] == "4" and cells[3].startswith("2/4") and cells[4].startswith("1/4") and cells[5] == "1"


def test_precision_counts_group_flags_on_other_labels_as_false_positives() -> None:
    rows = [row("barcode_mismatch", "clean", ["B-LOT"], {"B-LOT": False}),
            row("barcode_mismatch", "clean", ["B-LOT"], {"B-LOT": False, "B-EXP": False}),  # B-EXP is a wrong-rule flag
            row("clean", "clean", [], {"B-LOT": True})]
    line = next(x for x in ev._precision_table(rows, ("clean",)) if x.startswith("| barcode_mismatch | clean"))
    cells = [c.strip() for c in line.split("|")[1:-1]]
    assert (cells[2], cells[3]) == ("2", "2") and cells[4].startswith("2/4")


def test_false_alarm_tables_report_per_rule_and_per_condition() -> None:
    rows = [row("clean", "hard", [], {"S-EXP": True}), row("clean", "hard", [], {}),
            row("clean", "clean", [], {}), row("clean", "hard", [], {"P-NAME": False})]
    text = "\n".join(ev._false_alarm_tables(rows, ("clean", "hard")))
    hard = next(x for x in text.splitlines() if x.startswith("| hard |"))
    assert "2/3 = 0.67" in hard and "1/3 = 0.33" in hard  # any finding, any confident finding
    assert "| S-EXP | 0/1 = 0.00" in text and "| P-NAME |" in text


def test_expected_rules_and_record_side_injections() -> None:
    side = {"expected": [], "true_fields": {"product_name": "N", "manufacturer": "M", "manufacturer_address": "A",
                                            "model": "REF: X"}, "ais": {"01": "00000000000000"}}
    assert ev._expected(side, "udi_mismatch") == ["P-UDI"] and ev._expected(side, "rx_missing") == ["R-RX"]
    assert ev._record(side, "udi_mismatch").udi_di == ev.OTHER_UDI_DI != "00000000000000"
    assert check_digit_ok(ev.OTHER_UDI_DI)
    assert ev._record(side, "rx_missing").extra == {"rx_only": "true"} and ev._record(side, "clean").extra == {}


def test_variants_cover_every_injection_and_stay_ascii_and_safe() -> None:
    pytest.importorskip("cv2")  # the generator module imports the CV libraries
    out = ev._variants(3, np.random.default_rng(1))
    assert set(out["variants"]) == set(ev.IMAGE_KINDS)
    printed = out["variants"]["wrong_name"]["field_values"]["product_name"]
    assert printed != out["fields"]["product_name"] and len(printed) == len(out["fields"]["product_name"])
    assert out["variants"]["expiry_format"]["field_values"]["expiry"].startswith("EXP: ")
