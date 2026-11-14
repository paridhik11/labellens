"""Tests for src.ir.step15_report (ablation tables, Holm families)."""
from __future__ import annotations

from src.ir.step15_ablation import variant_names
from src.ir.step15_report import ABLATIONS, ablations_report, comparison_rows, module_ablation_data
from tests.test_step15_ablation import _chunks, _Fake


def _module(tmp_path, module: str):  # type: ignore[no-untyped-def]
    from src.ir.eval import QueryRow
    from src.ir.step15_ablation import build_variants

    chunks = [c.model_copy(update={"module": module}) for c in _chunks()]
    variants = build_variants(chunks, model=_Fake(), cache_dir=tmp_path)
    rows = [
        QueryRow("q1", "label warning", module, "direct"),
        QueryRow("q2", "sterile storage", module, "direct"),
        QueryRow("q3", "barcode", module, "no_answer"),
    ]
    qrels = {
        "q1": {c.chunk_id: (2 if i == 0 else 0) for i, c in enumerate(chunks)},
        "q2": {c.chunk_id: (1 if i == 3 else 0) for i, c in enumerate(chunks)},
        "q3": {c.chunk_id: 0 for c in chunks},
    }
    return module_ablation_data(chunks, variants, rows, qrels)


def test_ablations_cover_11_distinct_variants() -> None:
    pairs = [v for _, (_, ps) in ABLATIONS.items() for v, _ in ps]
    assert len(pairs) == 11
    assert len(set(pairs)) == 11
    assert set(pairs) <= set(variant_names())


def test_report_and_holm_families(tmp_path) -> None:  # type: ignore[no-untyped-def]
    data = {"device": _module(tmp_path / "a", "device"), "medicine": _module(tmp_path / "b", "medicine")}
    # no_answer query is excluded, so 2 scored queries per module
    assert len(data["device"]["qids"]) == 2
    rows = comparison_rows(data)
    assert len(rows) == 2 * 2 * 11  # modules x levels x variants
    for r in rows:
        assert r["p"] <= r["p_holm_abl"] <= 1.0
        assert r["p"] <= r["p_holm_all"] <= 1.0
    text = ablations_report(data)
    assert "provisional until the depth-20 pool is graded" in text
    assert "Holm (all 22)" in text
    assert "unjudged@10" in text
    assert text.count("## Ablation:") == 4


def test_unjudged_counts_present(tmp_path) -> None:  # type: ignore[no-untyped-def]
    md = _module(tmp_path, "device")
    assert set(md["unjudged"]) == set(variant_names())
    assert all(set(v) == {"chunk", "section", "r11_20"} for v in md["unjudged"].values())
