"""The checker's settings. Retrieval config lives in exactly one object, ``RETRIEVAL``."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievalSettings:
    """Which retriever finds citations. Default is plain hybrid RRF; the frozen Session B config replaces it here."""

    method: str = "hybrid_rrf"  # bm25 | tfidf | dense | hybrid_rrf | e5b (the frozen Step 18 system)
    module: str = "device"
    k: int = 10
    rrf_k: int = 60
    stem: bool = False
    prefix: bool = False

    def echo(self) -> dict[str, object]:
        """The configuration as a dict, for echoing in responses and reports."""
        return {"method": self.method, "module": self.module, "k": self.k, "rrf_k": self.rrf_k,
                "stem": self.stem, "prefix": self.prefix}


RETRIEVAL = RetrievalSettings()


@dataclass(frozen=True)
class CheckerSettings:
    """Thresholds frozen before the final evaluation (docs/CHECKER_SPEC.md, section 2)."""

    min_ocr_confidence: float = 0.8
    symbol_detector_trusted: bool = False
    expected_symbols: tuple[str, ...] = ("manufacturer", "expiry")
    retrieval: RetrievalSettings = field(default_factory=lambda: RETRIEVAL)
