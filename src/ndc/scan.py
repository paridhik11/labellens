"""NDC-first identification of a medicine photo (protocol: results/ndc_scan/protocol.md).

``decide`` is pure: it gets the barcode NDCs, the OCR text, the exact NDC table, a BM25 text ranking and a function
that returns method E's result (called only when no NDC decides, so a barcode hit skips OCR matching entirely).
Nothing here confirms a product: ``matched`` still goes through the confirm step ("Is this X?").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.ndc.codes import lookup, printed_ndcs

CONFIG_PATH = Path(__file__).with_name("ndc_config.json")


@dataclass(frozen=True)
class NdcConfig:
    """``tau``: BM25 score a text-rank review suggestion needs (None switches the suggestion off)."""

    tau: float | None = None
    top: int = 3


def load_config(path: Path = CONFIG_PATH) -> NdcConfig:
    """The frozen configuration (defaults when missing)."""
    if not path.exists():
        return NdcConfig()
    return NdcConfig(**json.loads(path.read_text(encoding="utf-8")))


def outside_corpus_lookup(ndc11: str) -> dict[str, Any] | None:
    """Hook for the live DailyMed lookup by NDC (products outside the corpus).

    The live-dailymed branch is not merged into main, so this returns None. When it is merged, call its
    lookup-by-NDC here and show the result as a reference-less "this looks like X" (never a corpus summary).
    """
    return None


def decide(
    barcode_ndcs: list[str], text: str, table: dict[str, list[str]], text_rank: list[tuple[str, float]],
    run_e: Callable[[], dict[str, Any]], config: NdcConfig,
) -> dict[str, Any]:
    """Result ``{outcome, setids, source, evidence, e}``; outcome is matched, needs_review or no_reference_match.

    Order: NDC exact match (barcode, printed) wins outright; otherwise method E unchanged; otherwise (only when E
    found nothing and did not time out) a BM25 review suggestion at or above ``config.tau``.
    """
    from_barcode = lookup(barcode_ndcs, table)
    from_text = lookup(printed_ndcs(text), table)
    ids = {s for v in (*from_barcode.values(), *from_text.values()) for s in v}
    unmatched = [c for c in barcode_ndcs if c not in table]
    evidence = {"barcode_ndcs": barcode_ndcs, "printed_hits": list(from_text), "barcode_hits": list(from_barcode),
                "barcode_ndc_not_in_corpus": unmatched}
    if ids:
        source = ("ndc_both" if from_barcode and from_text else "ndc_barcode" if from_barcode else "ndc_printed")
        outcome = "matched" if len(ids) == 1 else "needs_review"
        return {"outcome": outcome, "setids": sorted(ids), "source": source, "evidence": evidence, "e": None}
    e = run_e()
    if e["outcome"] != "no_reference_match" or e.get("reason") == "timeout":
        return {**e_to_result(e), "evidence": evidence, "e": e}
    if config.tau is not None and text_rank and text_rank[0][1] >= config.tau:
        return {"outcome": "needs_review", "setids": [s for s, _ in text_rank[: config.top]], "source": "text_rank",
                "evidence": evidence, "e": e}
    return {"outcome": "no_reference_match", "setids": [], "source": "none", "evidence": evidence, "e": e}


def e_to_result(e: dict[str, Any]) -> dict[str, Any]:
    """Method E's outcome and candidate set ids in the same shape (E decides, nothing is changed)."""
    return {"outcome": e["outcome"], "setids": list(e.get("setids", [])),
            "source": "e" if e["outcome"] != "no_reference_match" else "e_none"}
