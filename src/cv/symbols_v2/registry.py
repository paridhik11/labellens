"""Names for the extra featurizers that ``experiment`` can compute in worker processes."""

from __future__ import annotations

from src.cv.symbols_v2.detector import Featurizer


def extra_featurizers(names: tuple[str, ...]) -> dict[str, Featurizer]:
    """Return the featurizers called ``names`` (``cnn``, which needs trained weights, and ``clip``, which needs the downloaded CLIP model)."""
    out: dict[str, Featurizer] = {}
    for name in names:
        if name == "cnn":
            from src.cv.symbols_v2.cnn import cnn_featurizer

            out[name] = cnn_featurizer()
        elif name == "clip":
            from src.cv.symbols_v2.clip_zero_shot import clip_featurizer

            out[name] = clip_featurizer()
        else:
            raise ValueError(f"Unknown featurizer: {name}")
    return out
