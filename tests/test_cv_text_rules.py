"""Tests for the CV text rules and evaluation maths. These need no CV libraries."""

from __future__ import annotations

from src.common.schemas import BarcodeResult, Flag, LabelExtraction, OcrBlock, SymbolDetection
from src.cv import eval_v2
from src.cv.consistency import check_extraction
from src.cv.fields import (
    map_fields_by_layout,
    normalise_field,
    reconcile_with_barcode,
    snap_to_vocabulary,
    split_key_value,
    strip_key,
)


def _blocks() -> list[OcrBlock]:
    """Text lines of a test label in reading order, with a junk line read from a barcode."""
    return [
        OcrBlock(text="TEST DATA | DRAFT", bbox=(60, 40, 380, 44), conf=0.98),
        OcrBlock(text="TEST SENSOR 001", bbox=(60, 140, 410, 50), conf=0.97),
        OcrBlock(text="Example Labs 001", bbox=(60, 232, 310, 40), conf=0.99),
        OcrBlock(text="101 Example Road", bbox=(60, 304, 275, 38), conf=0.97),
        OcrBlock(text="REF:TEST-M001", bbox=(60, 388, 275, 38), conf=0.96),
        OcrBlock(text="LOT: TESTLOT0016232", bbox=(60, 470, 380, 38), conf=0.95),
        OcrBlock(text="EXP: 2028-11-O1", bbox=(60, 552, 300, 38), conf=0.94),
        OcrBlock(text="X2", bbox=(830, 370, 290, 30), conf=0.2),
    ]


def test_split_key_value_variants() -> None:
    assert split_key_value("REF: TEST-M001") == ("model", "REF", "TEST-M001")
    assert split_key_value("LOT:TESTLOT001") == ("lot", "LOT", "TESTLOT001")
    assert split_key_value("EXP 2027-01-01") == ("expiry", "EXP", "2027-01-01")
    # One wrong letter in a key of three letters is repaired when a separator follows.
    assert split_key_value("REE: TEST-M001") == ("model", "REF", "TEST-M001")
    assert split_key_value("Example Labs 001") == (None, "", "Example Labs 001")
    # Without a separator only an exact key counts, so ordinary words are not keys.
    assert split_key_value("LOW battery")[0] is None


def test_normalise_field_only_applies_format_rules() -> None:
    assert normalise_field("model", "REF:TEST-M001") == "REF: TEST-M001"
    assert normalise_field("lot", " LOT :  TESTLOT1 ") == "LOT: TESTLOT1"
    assert normalise_field("expiry", "EXP:2028-11-O1") == "EXP: 2028-11-01"
    # A value that is not a date after the digit mapping is left alone.
    assert normalise_field("expiry", "EXP: soon") == "EXP: soon"
    # Names get whitespace cleanup only; a wrong character stays wrong.
    assert normalise_field("product_name", "  TEST  SENSOR O01 ") == "TEST SENSOR O01"
    assert strip_key("REF: TEST-M001") == "TEST-M001"


def test_layout_mapping_uses_text_not_positions() -> None:
    fields, warnings = map_fields_by_layout(_blocks())
    assert fields == {
        "model": "REF:TEST-M001",
        "lot": "LOT: TESTLOT0016232",
        "expiry": "EXP: 2028-11-O1",
        "manufacturer_address": "101 Example Road",
        "manufacturer": "Example Labs 001",
        "product_name": "TEST SENSOR 001",
    }
    assert any(warning.startswith("OCR_BLOCKS_IGNORED") for warning in warnings)
    # Moving every line by the same offset changes nothing: no slot positions are used.
    shifted = [block.model_copy(update={"bbox": (block.bbox[0] + 300, block.bbox[1] + 90, *block.bbox[2:])})
               for block in _blocks()]
    assert map_fields_by_layout(shifted)[0] == fields


def test_layout_mapping_prefers_missing_over_wrong() -> None:
    """When the product name is unreadable an ordinary line must not be promoted to it."""
    blocks = [block for block in _blocks() if block.text not in {"TEST SENSOR 001", "101 Example Road"}]
    fields, warnings = map_fields_by_layout(blocks)
    assert "product_name" not in fields and "manufacturer" not in fields
    assert "FIELD_MISSING: product_name" in warnings


def test_reconcile_snaps_only_confusable_differences() -> None:
    parsed = {"10": "TESTLOT0016232", "17": "281101"}
    fields = {"lot": "LOT: TESTLOTO016232", "expiry": "EXP: 2028-11-01"}
    fixed, notes = reconcile_with_barcode(fields, parsed)
    assert fixed["lot"] == "LOT: TESTLOT0016232" and len(notes) == 1
    # A real mismatch is not hidden.
    wrong = {"lot": "LOT: TESTLOT0016233", "expiry": "EXP: 2028-11-02"}
    assert reconcile_with_barcode(wrong, parsed) == (wrong, [])


def test_snap_to_vocabulary() -> None:
    names = ["TEST SENSOR 001", "TEST DEVICE 002", "TEST KIT 003"]
    assert snap_to_vocabulary("TESTSENSORO01", names) == "TEST SENSOR 001"
    assert snap_to_vocabulary("SOMETHING ELSE", names) == "SOMETHING ELSE"


def _extraction(
    lot: str = "LOT: TESTLOT0016232",
    symbols: tuple[str, ...] = ("manufacturer", "expiry"),
    lot_conf: float | None = 0.95,
    lot_read: str | None = None,
) -> LabelExtraction:
    """Build an extraction whose OCR lines carry the given lot confidence (None: no lot line)."""
    blocks = [OcrBlock(text="EXP: 2028-11-01", bbox=(0, 50, 100, 20), conf=0.95)]
    if lot_conf is not None:
        blocks.append(OcrBlock(text=lot if lot_read is None else lot_read, bbox=(0, 20, 100, 20), conf=lot_conf))
    return LabelExtraction(
        label_id="test_label_001",
        fields={"lot": lot, "expiry": "EXP: 2028-11-01"},
        barcodes=[BarcodeResult(type="DataMatrix", raw="x", parsed={"10": "TESTLOT0016232", "17": "281101"})],
        symbols=[SymbolDetection(name=name, bbox=(0, 0, 10, 10), conf=0.9) for name in symbols],
        ocr_blocks=blocks,
    )


def test_consistency_flags() -> None:
    assert check_extraction(_extraction()) == []
    # 0 read as O is not a mismatch.
    assert check_extraction(_extraction(lot="LOT: TESTLOTO016232")) == []
    mismatch = check_extraction(_extraction(lot="LOT: TESTLOT0016233"))
    assert [flag.kind for flag in mismatch] == ["barcode_mismatch"]
    assert isinstance(mismatch[0], Flag) and mismatch[0].needs_human and mismatch[0].expected == "TESTLOT0016232"
    missing = check_extraction(_extraction(symbols=("manufacturer",)))
    assert [(flag.kind, flag.expected) for flag in missing] == [("missing_symbol", "expiry")]
    unreadable = _extraction()
    unreadable.barcodes = []
    assert [flag.kind for flag in check_extraction(unreadable)] == ["barcode_unreadable"]


def test_uncertain_reading_needs_human_not_mismatch() -> None:
    """A disagreement read with low OCR confidence is a review request, not a mismatch."""
    from src.cv.consistency import DEFAULT_MIN_OCR_CONFIDENCE, field_confidence

    low = check_extraction(_extraction(lot="LOT: TESTLOT0016233", lot_conf=0.42))
    assert [flag.kind for flag in low] == ["needs_human_review"]
    assert low[0].severity == "review" and low[0].needs_human and low[0].confidence == 0.42
    assert low[0].observed == "TESTLOT0016233" and low[0].expected == "TESTLOT0016232"
    # No OCR line can be matched to the field: confidence is unknown, so also a review request.
    unknown = check_extraction(_extraction(lot="LOT: TESTLOT0016233", lot_conf=None))
    assert [flag.kind for flag in unknown] == ["needs_human_review"] and unknown[0].confidence == 0.0
    # The threshold is inclusive: exactly at the threshold counts as confident.
    edge = check_extraction(_extraction(lot="LOT: TESTLOT0016233", lot_conf=DEFAULT_MIN_OCR_CONFIDENCE))
    assert [flag.kind for flag in edge] == ["barcode_mismatch"]
    assert check_extraction(_extraction(lot="LOT: TESTLOT0016233", lot_conf=0.42), min_ocr_confidence=0.4)[0].kind == (
        "barcode_mismatch"
    )
    # Agreement never produces a flag, however low the confidence.
    assert check_extraction(_extraction(lot_conf=0.1)) == []
    # A post-corrected field (key spacing fixed) is still matched to its raw OCR line.
    corrected = _extraction(lot="LOT: TESTLOT0016233", lot_conf=0.9, lot_read="LOT:TESTLOT0016233")
    assert field_confidence(corrected, "lot") == 0.9
    assert field_confidence(corrected, "model") is None


def _record(condition: str, lot_read: str, parsed: list[dict[str, str]]) -> dict:
    truth = {
        "condition": condition,
        "fields": {field: "AB" for field in eval_v2.FIELDS} | {"lot": "LOT: A1"},
        "barcode_ais": {"10": "A1"},
        "label_quad_px": [[0, 0], [100, 0], [100, 50], [0, 50]],
        "symbols": [{"name": "expiry", "quad_px": [[10, 10], [20, 10], [20, 20], [10, 20]]}],
    }
    result = {
        "fields": {field: "AB" for field in eval_v2.FIELDS} | {"lot": lot_read},
        "raw_fields": {field: "AB" for field in eval_v2.FIELDS} | {"lot": "LOT:A1"},
        "barcodes": parsed,
        "barcode_method": "original_image",
        "symbols": [{"name": "expiry", "bbox": [10, 10, 10, 10], "conf": 0.9},
                    {"name": "manufacturer", "bbox": [50, 10, 10, 10], "conf": 0.8}],
        "flags": [],
    }
    return {"image": "x.png", "truth": truth, "corners": [[1, 1], [100, 0], [100, 50], [0, 50]],
            "corner_method": "contour", "template": result, "blind": result}


def test_eval_counts_and_merge() -> None:
    assert eval_v2.edit_distance("LOT: A1", "LOT:A1") == 1
    assert eval_v2.box_iou((0, 0, 10, 10), (5, 0, 10, 10)) == 1 / 3
    run = {"generator": "src.gen.generate_dataset", "seed": 1,
           "records": [_record("hard", "LOT: A1", [{"10": "A1"}]), _record("hard", "LOT: A1", [])]}
    table = eval_v2.summarise(run)
    cell = table["hard|blind"]
    assert cell["images"] == 2 and cell["gs1_exact"] == 1 and cell["corners_10px"] == 2
    assert cell["symbols_matched"] == 2 and cell["symbols_expected"] == 2
    # The manufacturer detection is not on the label, so it is a false positive each time.
    assert cell["symbol_false_positives"] == 2
    assert cell["raw"]["lot"] == [2, 14] and cell["post"]["lot"] == [0, 14]
    merged = eval_v2.merge_counts([table, table])
    assert merged["hard|blind"]["images"] == 4 and merged["hard|blind"]["raw"]["lot"] == [4, 28]
    text = "\n".join(eval_v2.render_main(merged, "Seeds 1, 1"))
    assert "| hard | 4 | 2/4 (50.0%)" in text


def test_eval_negative_counts() -> None:
    truth = {
        "case": "missing_expiry", "condition": "hard", "expected_symbols": ["manufacturer", "expiry"],
        "present_symbols": [{"name": "manufacturer", "quad_px": [[0, 0], [10, 0], [10, 10], [0, 10]]}],
    }
    result = {
        "symbols": [{"name": "manufacturer", "bbox": [0, 0, 10, 10], "conf": 0.9},
                    {"name": "expiry", "bbox": [30, 0, 10, 10], "conf": 0.8}],
        "flags": [], "barcodes": [{"10": "A1"}],
    }
    run = {"generator": "src.gen.generate_negatives", "seed": 1,
           "records": [{"image": "x.png", "truth": truth, "template": result, "blind": result}]}
    cell = eval_v2.summarise(run)["missing_expiry|hard|blind"]
    assert cell["absent_total"] == 1 and cell["absent_reported"] == 1 and cell["missing_flagged"] == 0
    assert cell["present_matched"] == 1 and cell["barcode_decoded"] == 1


def test_product_record_from_extraction() -> None:
    from src.cv.integration import to_product_record

    extraction = _extraction()
    extraction.fields.update(
        product_name="TEST SENSOR 001", model="REF: TEST-M001", manufacturer="Example Labs 001",
        manufacturer_address="101 Example Road",
    )
    extraction.barcodes[0].parsed["01"] = "00000000000000"
    record = to_product_record(extraction)
    assert record.model == "TEST-M001" and record.name == "TEST SENSOR 001"
    assert record.udi_di == "00000000000000"
    assert record.extra == {"lot": "TESTLOT0016232", "expiry": "2028-11-01"}
    # No barcode, no identifier: the UDI-DI is never made up.
    extraction.barcodes = []
    assert to_product_record(extraction).udi_di == ""


def test_real_photo_harness_without_photos(tmp_path) -> None:
    from src.cv import eval_real

    assert eval_real.evaluate(tmp_path) is None
    assert eval_real.main(["--folder", str(tmp_path)]) == 0
    csv_path = tmp_path / "transcriptions.csv"
    csv_path.write_text("filename,product_name,lot\nphoto_01.jpg,TEST KIT 001, TESTLOT1 \nphoto_02.jpg,,\n",
                        encoding="utf-8")
    rows = eval_real.load_transcriptions(csv_path)
    assert rows == {"photo_01.jpg": {"product_name": "TEST KIT 001", "lot": "TESTLOT1"}, "photo_02.jpg": {}}
    # A CSV alone, with no photos, still produces no numbers.
    assert eval_real.evaluate(tmp_path) is None
    scored = eval_real.score(rows["photo_01.jpg"], {"product_name": "TEST KIT 001", "lot": "LOT: TESTLOT7"})
    assert scored["product_name"] == {"edits": 0, "characters": 12, "exact": 1, "present": 1}
    assert scored["lot"]["edits"] == 1 and scored["lot"]["exact"] == 0
    assert eval_real.score({"lot": "A1"}, {})["lot"] == {"edits": 2, "characters": 2, "exact": 0, "present": 0}


def test_wilson_interval_and_cell_annotation() -> None:
    import pytest

    from src.cv.intervals import annotate_cell, annotate_table, wilson_interval

    low, high = wilson_interval(51, 51)
    assert high == 1.0 and round(100 * low, 1) == 93.0
    low, high = wilson_interval(45, 51)
    assert (round(100 * low, 1), round(100 * high, 1)) == (76.6, 94.5)
    assert wilson_interval(0, 34)[0] == 0.0
    with pytest.raises(ValueError):
        wilson_interval(3, 2)
    assert annotate_cell(" 45/51 (88.2%) ") == " 45/51 (88.2%; 95% CI 76.6 to 94.5%) "
    assert annotate_cell(" 51/51 ") == " 51/51 (100.0%; 95% CI 93.0 to 100.0%) "
    assert annotate_cell(" 0/0 ") == " 0/0 "
    assert annotate_cell(" n/a ") == " n/a "
    once = annotate_cell(" 45/51 (88.2%) ")
    assert annotate_cell(once) == once
    lines = ["| A | B |", "| --- | --- |", "| x | 1/2 |", "", "| A | B |"]
    assert annotate_table(lines, "| A |", (1,)) == 1
    assert "95% CI" in lines[2] and lines[4] == "| A | B |"


def test_damaged_reading_needs_human_not_mismatch() -> None:
    """A lot or expiry that lost its key or is not a valid date is a review request even when OCR is confident."""
    from src.cv.consistency import format_problem

    assert format_problem("lot", "LOT: TESTLOT0016232") is None
    assert format_problem("expiry", "EXP: 2028-11-01") is None
    assert format_problem("expiry", "EXP: 2028-13-01") is not None  # month 13 does not exist
    assert format_problem("expiry", "EXP: 2028-02-30") is not None  # nor does 30 February
    assert format_problem("expiry", "EXP: 2O28-11-01") is not None  # a letter O in the year
    assert format_problem("expiry", "2028-11-01") is not None  # key lost
    assert format_problem("lot", "TESTLOT0016232") is not None  # key lost
    assert format_problem("lot", "LOT: TEST@LOT") is not None
    lost_key = check_extraction(_extraction(lot="TESTLOT0016233", lot_conf=0.99))
    assert [flag.kind for flag in lost_key] == ["needs_human_review"]
    assert "damaged" in lost_key[0].message
    bad_date = _extraction()
    bad_date.fields["expiry"] = "EXP: 2028-13-01"
    assert [flag.kind for flag in check_extraction(bad_date)] == ["needs_human_review"]
    # A well-formed, confident, different reading is still a mismatch.
    assert [flag.kind for flag in check_extraction(_extraction(lot="LOT: TESTLOT0016233", lot_conf=0.99))] == [
        "barcode_mismatch"
    ]
    wrong_date = _extraction()
    wrong_date.fields["expiry"] = "EXP: 2028-11-02"
    wrong_date.ocr_blocks.append(OcrBlock(text="EXP: 2028-11-02", bbox=(0, 50, 100, 20), conf=0.95))
    assert [flag.kind for flag in check_extraction(wrong_date)] == ["barcode_mismatch"]
