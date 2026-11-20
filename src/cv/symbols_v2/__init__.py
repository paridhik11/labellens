"""Symbol detector v2 for the manufacturer and use-by pictograms.

``detect_symbols_v2(image)`` has the same call shape and return type as ``src.cv.symbols.detect_symbols_blind``:
an upright RGB label in, a list of ``SymbolDetection`` (at most one per pictogram) out.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from src.common.schemas import SymbolDetection
from src.cv.symbols_v2.detector import Config, detect

CONFIGS: dict[str, Config] = {
    "v2_sil": Config(method="sil"),
    "v2_sift": Config(method="sift"),
    "v2_orb": Config(method="orb"),
    "v2_fuse": Config(method="fuse"),
}


def get_detector(name: str) -> Callable[[np.ndarray], list[SymbolDetection]]:
    """Return a configured v2 detector by name."""
    config = CONFIGS[name]
    return lambda image: detect(image, config)


def detect_symbols_v2(image: np.ndarray, *, variant: str = "v2_sil") -> list[SymbolDetection]:
    """Search the whole upright label for the two pictograms (same shape as ``detect_symbols_blind``)."""
    return get_detector(variant)(image)
