"""NDC signal tests: recorded values only (no network, no images, no OCR)."""

from __future__ import annotations

from src.ndc.codes import barcode_ndcs, check_digit_ok, from_segments, lookup, printed_ndcs, ten_digit_readings
from src.ndc.package_text import load_texts, make_retriever
from src.ndc.scan import NdcConfig, decide
from src.ndc.table import load_table

TABLE = load_table()
CODE = "69367035901"  # recorded: 69367-359-01 (5-3-2) is a package NDC of one corpus product
SETID = TABLE[CODE][0]


def upc_a(ten: str) -> str:
    """UPC-A text "3" + 10 NDC digits + check digit."""
    body = "3" + ten
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(body)))
    return body + str((10 - total % 10) % 10)


def test_layouts_normalise_to_eleven_digits() -> None:
    assert from_segments("1234", "5678", "90") == "01234567890"
    assert from_segments("12345", "678", "90") == "12345067890"
    assert from_segments("12345", "6789", "0") == "12345678900"
    assert from_segments("12345", "6789", "01") == "12345678901"
    assert from_segments("123", "4567", "89") is None


def test_printed_text_finds_hyphenated_and_dashed_ndc() -> None:
    assert CODE in printed_ndcs("Rx only NDC 69367-359-01 30 tablets")
    assert CODE in printed_ndcs("NDC 69367 – 359 – 01")
    assert printed_ndcs("lot 12345 expiry 2027") == []


def test_ten_digit_is_ambiguous_but_only_one_reading_is_in_the_table() -> None:
    readings = ten_digit_readings("6936735901")
    assert len(readings) == 3 and CODE in readings
    assert [r for r in readings if r in TABLE] == [CODE]


def test_barcode_needs_a_valid_check_digit_and_the_ndc_prefix() -> None:
    good = upc_a("6936735901")
    assert check_digit_ok(good) and CODE in barcode_ndcs(good)
    assert barcode_ndcs(good[:-1] + str((int(good[-1]) + 1) % 10)) == []
    assert barcode_ndcs("012345678905") == []  # a normal UPC (starts with 0), not an NDC barcode
    ean = "0" + good
    assert CODE in barcode_ndcs(ean) or not check_digit_ok(ean)
    gtin = "0" + "03" + "6936735901"
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(gtin)))
    gtin += str((10 - total % 10) % 10)
    assert CODE in barcode_ndcs("(01)" + gtin)


def test_lookup_is_exact() -> None:
    assert lookup([CODE, "69367035902"], TABLE) == {CODE: TABLE[CODE]}


def test_table_has_every_pinned_product_and_no_shared_ndc() -> None:
    assert len({s for v in TABLE.values() for s in v}) == 30
    assert all(len(v) == 1 for v in TABLE.values())


def e_result(outcome: str, reason: str | None = None, setids: list[str] | None = None) -> dict:
    return {"outcome": outcome, "reason": reason, "setids": setids or []}


def test_ndc_match_wins_and_skips_e() -> None:
    def boom() -> dict:
        raise AssertionError("E must not run when an NDC decides")

    out = decide([CODE], "", TABLE, [], boom, NdcConfig())
    assert out["outcome"] == "matched" and out["setids"] == [SETID] and out["source"] == "ndc_barcode"
    out = decide([], "NDC 69367-359-01", TABLE, [], boom, NdcConfig())
    assert out["source"] == "ndc_printed"


def test_two_products_from_two_signals_need_review() -> None:
    other = next(c for c, v in TABLE.items() if v[0] != SETID)
    out = decide([CODE], f"NDC {other}", TABLE, [], lambda: e_result("no_reference_match"), NdcConfig())
    assert out["outcome"] == "needs_review" and len(out["setids"]) == 2


def test_unknown_ndc_identifies_nothing_and_e_stands() -> None:
    out = decide(["00000000001"], "", TABLE, [], lambda: e_result("needs_review", None, ["x"]), NdcConfig())
    assert out["outcome"] == "needs_review" and out["source"] == "e"
    assert out["evidence"]["barcode_ndc_not_in_corpus"] == ["00000000001"]


def test_text_rank_only_adds_a_review_and_never_after_a_timeout() -> None:
    rank = [("a", 9.0), ("b", 5.0), ("c", 4.0), ("d", 1.0)]
    none = e_result("no_reference_match", "no_match")
    assert decide([], "", TABLE, rank, lambda: none, NdcConfig(tau=8.0))["outcome"] == "needs_review"
    assert decide([], "", TABLE, rank, lambda: none, NdcConfig(tau=10.0))["outcome"] == "no_reference_match"
    assert decide([], "", TABLE, rank, lambda: none, NdcConfig())["outcome"] == "no_reference_match"
    slow = e_result("no_reference_match", "timeout")
    assert decide([], "", TABLE, rank, lambda: slow, NdcConfig(tau=0.0))["source"] == "e_none"
    out = decide([], "", TABLE, rank, lambda: e_result("matched", None, ["z"]), NdcConfig(tau=0.0))
    assert out["outcome"] == "matched" and out["source"] == "e"


def test_bm25_text_rank_finds_the_product_by_its_label_words() -> None:
    texts = load_texts()
    retriever = make_retriever(texts)
    name = next(v["name"] for v in texts.values() if "Rosuvastatin" in v["name"])
    top = retriever.search("rosuvastatin calcium tablets NDC", k=1)[0]
    assert texts[top.doc_id]["name"] == name
