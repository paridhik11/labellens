"""Glue between the public photo scan and the NDC signal (src/ndc, protocol results/ndc_scan/protocol.md).

``scan_with_ndc`` runs the barcode first (about a second); a table NDC from the barcode ends the scan without OCR.
Otherwise the OCR lines are read, a printed table NDC wins, else method E decides unchanged, and only when E finds
nothing a BM25 text-rank review may be added. A result is always "Is this X?" with the evidence in ``matched_text``;
nothing here confirms a product.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable

from src.ndc import scan as ndc_scan
from src.ndc.barcode import read_payloads
from src.ndc.package_text import load_texts, make_retriever
from src.ndc.table import load_table

_CACHE: dict[str, Any] = {}


class _NeedOcr(Exception):
    """The barcode did not decide, so the OCR lines are needed."""


def resources() -> dict[str, Any]:
    """Table, BM25 text index and frozen config, built once."""
    if not _CACHE:
        texts = load_texts()
        _CACHE.update(table=load_table(), texts=texts, bm25=make_retriever(texts), config=ndc_scan.load_config())
    return _CACHE


def safe_barcode_ndcs(path: Path) -> list[str]:
    """NDC readings of every barcode in the photo; any decoder failure means no reading."""
    try:
        return [c for b in read_payloads(path) for c in b["ndcs"]]
    except Exception:
        return []


def text_rank(res: dict[str, Any], text: str) -> list[tuple[str, float]]:
    """BM25 ranking of the corpus products (set id, score) for all OCR text."""
    return [(h.doc_id, h.score) for h in res["bm25"].search(text, k=len(res["texts"])) if h.score > 0]


def decision_found(catalog: Any, decision: dict[str, Any], threshold: float) -> dict[str, Any]:
    """The ``found`` dict ``public_scan.match_body`` expects, built from an NDC or text-rank decision."""
    by_setid = {p.setid: pid for pid, p in catalog.products.items()}
    candidates = [(by_setid[s], 1.0 if decision["source"].startswith("ndc") else 0.0) for s in decision["setids"]]
    return {"outcome": decision["outcome"], "score_name": "ndc_exact" if decision["source"].startswith("ndc")
            else "bm25_package_text", "score": candidates[0][1] if candidates else 0.0, "threshold": threshold,
            "candidates": candidates}


def evidence_text(decision: dict[str, Any]) -> str:
    """The evidence line shown to the person: which NDC was read, from which source."""
    ev = decision["evidence"]
    if decision["source"] == "text_rank":
        return "Package text similarity (no NDC read)"
    parts = []
    if ev["barcode_hits"]:
        parts.append("barcode " + ", ".join(ev["barcode_hits"]))
    if ev["printed_hits"]:
        parts.append("printed line " + ", ".join(ev["printed_hits"]))
    return "NDC " + "; ".join(parts)


def scan_with_ndc(
    path: Path, service: Any, read: Callable[..., dict[str, Any]], run_e: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(body, extra)``. ``run_e(reading)`` is method E's identify result on the OCR reading
    (unchanged public_scan code)."""
    from src.api import medicine, public_scan

    res = resources()
    started = time.monotonic()
    barcode = safe_barcode_ndcs(path)
    extra: dict[str, Any] = {"barcode_ndcs": barcode, "barcode_seconds": round(time.monotonic() - started, 2)}
    catalog, threshold = service.catalog, service.matcher.threshold

    def finish(lines: list[dict], decision: dict[str, Any]) -> dict[str, Any]:
        found = decision_found(catalog, decision, threshold)
        result = {"outcome": decision["outcome"], "reason": None,
                  "best": {"found": found, "text": evidence_text(decision), "lines": ()}}
        extra["source"] = decision["source"]
        return public_scan.result_body(catalog, service.matcher, lines, result, medicine)

    def refuse() -> dict[str, Any]:
        raise _NeedOcr

    try:
        early = ndc_scan.decide(barcode, "", res["table"], [], refuse, res["config"])
    except _NeedOcr:
        early = None
    if early is not None:
        return finish([], early), extra
    reading = read(path)
    lines = reading["lines"]
    text = " ".join(x["text"] for x in lines)
    e_cache: dict[str, Any] = {}

    def e_result() -> dict[str, Any]:
        e_cache["result"] = run_e(reading)
        result = e_cache["result"]
        cands = result["best"]["found"]["candidates"] if result["best"] else []
        by_pid = {pid: p.setid for pid, p in catalog.products.items()}
        return {"outcome": result["outcome"], "reason": result["reason"], "setids": [by_pid[c[0]] for c in cands]}

    decision = ndc_scan.decide(barcode, text, res["table"], text_rank(res, text), e_result, res["config"])
    extra["source"] = decision["source"]
    if decision["source"] in ("e", "e_none", "none"):
        return public_scan.result_body(catalog, service.matcher, lines, e_cache["result"], medicine), extra
    return finish(lines, decision), extra
