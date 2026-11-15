"""Rule behaviour on oracle extractions (perfect CV), one injected error at a time."""
import pytest

from src.checker.retrieval import build_retriever, module_chunks
from src.checker.runner import run_checks
from src.checker.settings import CheckerSettings, RetrievalSettings
from src.checker.synthetic import extraction_from_truth, payload_from_ais, record_from_truth
from src.common.schemas import BarcodeResult, OcrBlock

FIELDS = {
    "product_name": "TEST DEVICE", "manufacturer": "Example Manufacturer", "manufacturer_address": "123 Example Road",
    "model": "REF: TEST-M001", "lot": "LOT: TESTLOT001", "expiry": "EXP: 2027-12-31",
}
AIS = {"01": "00000000000000", "17": "271231", "10": "TESTLOT001", "21": "TESTSER001"}
ALL_RULES = {"X-HEALTH", "P-NAME", "P-REF", "P-MFR", "P-ADDR", "P-UDI", "B-READ", "B-GS1", "B-LOT", "B-EXP",
             "D-FMT", "R-UDI", "R-NAMEPLACE", "R-RX", "S-MFR", "S-EXP"}


@pytest.fixture(scope="module")
def env():
    chunks = module_chunks("device")
    return chunks, build_retriever(RetrievalSettings(method="bm25"), chunks)


def check(env, fields=None, *, rx=False, settings=None, **kw):
    """Run the checker on a label whose printed fields are changed; the record keeps the true values."""
    chunks, retriever = env
    x = extraction_from_truth("test_label", {**FIELDS, **(fields or {})}, AIS, **kw)
    rec = record_from_truth(FIELDS, AIS, rx_only=rx)
    return run_checks(x, rec, settings=settings, retriever=retriever, chunks=chunks), x, rec


def rules(result):
    return {f.rule_id: f for f in result.findings}


def outcome(result, rule_id):
    return next(o for o in result.coverage if o.rule_id == rule_id).outcome


def test_clean_label_has_only_the_symbol_outcomes_pending(env) -> None:
    result, _, _ = check(env)
    assert result.findings == [] and result.passed and result.critical_count == 0
    assert {o.rule_id for o in result.coverage if o.outcome == "needs_human"} == {"S-MFR", "S-EXP"}
    assert result.needs_human_count == 2
    assert outcome(result, "R-RX") == "not_applicable"


def test_every_rule_appears_once_in_coverage(env) -> None:
    result, _, _ = check(env)
    ids = [o.rule_id for o in result.coverage]
    assert len(ids) == len(set(ids)) and set(ids) == ALL_RULES


def test_wrong_product_name_is_critical_with_no_citation(env) -> None:
    result, _, _ = check(env, {"product_name": "TEST DEVICF"})
    f = rules(result)["P-NAME"]
    assert (f.severity, f.needs_human, f.observed, f.expected) == ("critical", False, "TEST DEVICF", "TEST DEVICE")
    assert f.evidence_chunk_ids == [] and not result.passed


def test_low_confidence_name_mismatch_needs_human(env) -> None:
    result, _, _ = check(env, {"product_name": "TEST DEVICF"}, conf=0.5)
    got = rules(result)["P-NAME"]
    assert got.severity == "review" and got.needs_human


def test_barcode_expiry_mismatch_is_critical_and_cited(env) -> None:
    result, _, _ = check(env, {"expiry": "EXP: 2027-12-30"})
    f = rules(result)["B-EXP"]
    assert f.severity == "critical" and not f.needs_human and f.expected == "2027-12-31"
    cite = f.citations[0]
    assert cite.section == "801.40" and cite.quote in env[0][cite.chunk_id].text


def test_barcode_lot_mismatch(env) -> None:
    result, _, _ = check(env, {"lot": "LOT: TESTLOT999"})
    assert rules(result)["B-LOT"].severity == "critical"


def test_wrong_date_format_raises_one_flag_not_two(env) -> None:
    result, _, _ = check(env, {"expiry": "EXP: 31/12/2027"})
    got = rules(result)
    assert got["D-FMT"].severity == "critical" and got["D-FMT"].citations[0].section == "801.18"
    assert "B-EXP" not in got and outcome(result, "B-EXP") == "not_checked"


def test_confusable_date_is_not_a_format_verdict(env) -> None:
    result, _, _ = check(env, {"expiry": "EXP: 2O27-12-31"})
    got = rules(result)["D-FMT"]
    assert got.needs_human and got.severity == "review"


def test_impossible_date_is_a_format_failure(env) -> None:
    result, _, _ = check(env, {"expiry": "EXP: 2027-02-30"})
    assert rules(result)["D-FMT"].severity == "critical"


def test_missing_symbol_is_needs_human_never_a_fail(env) -> None:
    result, _, _ = check(env, symbols=("manufacturer",))
    f = rules(result)["S-EXP"]
    assert f.needs_human and f.severity == "review" and f.kind == "missing_symbol"
    assert result.passed


def test_missing_symbol_is_a_fail_only_with_a_trusted_detector(env) -> None:
    result, _, _ = check(env, symbols=("manufacturer",), settings=CheckerSettings(symbol_detector_trusted=True))
    assert not rules(result)["S-EXP"].needs_human and outcome(result, "S-MFR") == "pass"


def test_barcode_unreadable_needs_human_and_skips_dependents(env) -> None:
    chunks, retriever = env
    x = extraction_from_truth("test_label", FIELDS, AIS).model_copy(update={"barcodes": []})
    result = run_checks(x, record_from_truth(FIELDS, AIS), retriever=retriever, chunks=chunks)
    assert rules(result)["B-READ"].needs_human
    assert {outcome(result, r) for r in ("B-GS1", "B-LOT", "B-EXP", "P-UDI", "R-UDI")} == {"not_checked"}


def test_bad_check_digit_is_critical(env) -> None:
    chunks, retriever = env
    x = extraction_from_truth("test_label", FIELDS, AIS)
    bad = BarcodeResult(type="DataMatrix", raw=payload_from_ais({**AIS, "01": "00000000000001"}), parsed={})
    result = run_checks(x.model_copy(update={"barcodes": [bad]}), record_from_truth(FIELDS, AIS),
                        retriever=retriever, chunks=chunks)
    f = rules(result)["B-GS1"]
    assert f.severity == "critical" and "check digit" in f.message and f.citations[0].section == "830.20"


def test_record_udi_di_mismatch_and_missing(env) -> None:
    chunks, retriever = env
    x = extraction_from_truth("test_label", FIELDS, AIS)
    rec = record_from_truth(FIELDS, AIS).model_copy(update={"udi_di": "09506000134352"})
    f = rules(run_checks(x, rec, retriever=retriever, chunks=chunks))["P-UDI"]
    assert f.severity == "critical" and f.observed == "00000000000000" and f.expected == "09506000134352"
    empty = rec.model_copy(update={"udi_di": ""})
    f = rules(run_checks(x, empty, retriever=retriever, chunks=chunks))["P-UDI"]
    assert f.needs_human and f.severity == "review"


def test_short_udi_di_is_zero_padded(env) -> None:
    chunks, retriever = env
    x = extraction_from_truth("test_label", FIELDS, {**AIS, "01": "09506000134352"})
    rec = record_from_truth(FIELDS, AIS).model_copy(update={"udi_di": "9506000134352"})
    assert "P-UDI" not in rules(run_checks(x, rec, retriever=retriever, chunks=chunks))


def test_missing_manufacturer_is_reported_once(env) -> None:
    chunks, retriever = env
    fields = {k: v for k, v in FIELDS.items() if k != "manufacturer"}
    x = extraction_from_truth("test_label", fields, AIS)
    result = run_checks(x, record_from_truth(FIELDS, AIS), retriever=retriever, chunks=chunks)
    got = rules(result)
    assert [r for r in got if r in {"P-MFR", "R-NAMEPLACE"}] == ["R-NAMEPLACE"]
    assert got["R-NAMEPLACE"].needs_human and got["R-NAMEPLACE"].citations[0].section == "801.1"


def test_rx_statement(env) -> None:
    result, x, _ = check(env, rx=True)
    assert rules(result)["R-RX"].needs_human and rules(result)["R-RX"].citations[0].section == "801.109"
    chunks, retriever = env
    block = OcrBlock(text="Rx only", bbox=(0, 0, 1, 1), conf=0.95)
    with_rx = x.model_copy(update={"ocr_blocks": [*x.ocr_blocks, block]})
    rec = record_from_truth(FIELDS, AIS, rx_only=True)
    assert "R-RX" not in rules(run_checks(with_rx, rec, retriever=retriever, chunks=chunks))


def test_unreliable_extraction_skips_text_rules_with_one_flag(env) -> None:
    result, _, _ = check(env, warnings=["OCR_FAILED: boom"])
    got = rules(result)
    assert got["X-HEALTH"].needs_human and got["X-HEALTH"].evidence_chunk_ids == []
    assert outcome(result, "P-NAME") == "not_checked" and outcome(result, "B-GS1") == "pass"


def test_no_citation_forces_needs_human(env) -> None:
    class Nothing:
        name = "none"

        def search(self, query, k=10):
            return []

    chunks, _ = env
    x = extraction_from_truth("test_label", {**FIELDS, "expiry": "EXP: 31/12/2027"}, AIS)
    result = run_checks(x, record_from_truth(FIELDS, AIS), retriever=Nothing(), chunks=chunks)
    f = rules(result)["D-FMT"]
    assert f.needs_human and f.severity == "review" and f.evidence_chunk_ids == []
    assert "No supporting regulation passage" in f.message


def test_findings_sorted_critical_first_and_config_echoed(env) -> None:
    result, _, _ = check(env, {"product_name": "TEST DEVICF"}, symbols=())
    rank = {"critical": 0, "review": 1}
    assert [f.severity for f in result.findings] == sorted((f.severity for f in result.findings), key=rank.get)
    assert result.retrieval_config["method"] == "hybrid_rrf"


def test_untrusted_symbol_detector_needs_human_in_both_directions(env) -> None:
    """While symbol_detector_trusted is False a detection is not a pass and a non-detection is not a fail."""
    assert CheckerSettings().symbol_detector_trusted is False
    result, _, _ = check(env, symbols=("manufacturer",))
    assert outcome(result, "S-MFR") == "needs_human"  # detected: no flag, but not confirmed as a pass
    assert "S-MFR" not in rules(result)
    missing = rules(result)["S-EXP"]  # not detected: a needs_human flag, never a fail
    assert missing.needs_human and missing.severity == "review" and missing.kind == "missing_symbol"
    both_missing, _, _ = check(env, symbols=())
    assert all(rules(both_missing)[rid].needs_human for rid in ("S-MFR", "S-EXP"))
    both_found, _, _ = check(env)
    assert {outcome(both_found, r) for r in ("S-MFR", "S-EXP")} == {"needs_human"}
