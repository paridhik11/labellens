"""Detector v2: propose pictogram-sized blobs anywhere on the label, then classify each against the reference bank.

The work is split in two so thresholds can be swept without redoing the slow part:

* ``featurize`` finds candidates and computes raw features per candidate (``sil``: best silhouette IoU per class,
  ``sift`` and ``orb``: RANSAC inlier counts per class, plus any extra featurizer such as the CNN),
* ``decide`` turns features into at most one detection per pictogram with a rule (see ``make_rule``).

Two names never claim overlapping boxes. Confidence is a score of agreement with the references (or the
classifier's probability), not a calibrated probability.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import numpy as np

from src.common.schemas import SymbolDetection
from src.cv.symbols_v2.candidates import Candidate, prepare, propose
from src.cv.symbols_v2.matchers import SYMBOL_NAMES, class_scores, keypoint_scores
from src.cv.symbols_v2.refs import Bank, build_bank, silhouette

Features = dict[str, dict[str, float]]
Rule = Callable[[Features], dict[str, float]]
Featurizer = Callable[[Candidate, np.ndarray], dict[str, float]]


@dataclass
class Scored:
    """One candidate box (original-image coordinates of the straightened label) with its raw features."""

    box: tuple[float, float, float, float]
    feats: Features = field(default_factory=dict)


@dataclass(frozen=True)
class Config:
    """Frozen settings of one detector variant."""

    method: str = "sil"
    sil_threshold: float = 0.70
    sil_margin: float = 0.03
    kp_inliers: float = 12.0
    kp_margin: float = 3.0
    work_short_side: int = 600
    style_ids: tuple[str, ...] | None = None


def featurize(
    image: np.ndarray,
    *,
    methods: tuple[str, ...] = ("sil",),
    work_short_side: int = 600,
    style_ids: tuple[str, ...] | None = None,
    extra: dict[str, Featurizer] | None = None,
) -> list[Scored]:
    """Find candidates on an upright RGB label and compute the requested raw features for each."""
    gray, factor = prepare(image, work_short_side)
    bank: Bank = build_bank(style_ids)
    scored = []
    for candidate in propose(gray):
        x, y, w, h = candidate.box
        item = Scored((x / factor, y / factor, w / factor, h / factor))
        if "sil" in methods:
            item.feats["sil"] = class_scores(silhouette(candidate.ink), bank)
        for kind in ("sift", "orb"):
            if kind in methods:
                item.feats[kind] = keypoint_scores(candidate.ink, bank, kind)
        for name, function in (extra or {}).items():
            item.feats[name] = function(candidate, gray)
        scored.append(item)
    return scored


def make_rule(config: Config) -> Rule:
    """Build the decision rule of a ``Config`` (silhouette, keypoints, or either)."""

    def rule(feats: Features) -> dict[str, float]:
        result = {name: 0.0 for name in SYMBOL_NAMES}
        if config.method in ("sil", "fuse") and "sil" in feats:
            scores = feats["sil"]
            for name in SYMBOL_NAMES:
                rivals = max(v for k, v in scores.items() if k != name)
                if scores[name] >= config.sil_threshold and scores[name] - rivals >= config.sil_margin:
                    result[name] = max(result[name], scores[name])
        for kind in ("sift", "orb"):
            if config.method in (kind, "fuse") and kind in feats:
                scores = feats[kind]
                for name in SYMBOL_NAMES:
                    rivals = max(v for k, v in scores.items() if k != name)
                    if scores[name] >= config.kp_inliers and scores[name] - rivals >= config.kp_margin:
                        result[name] = max(result[name], min(1.0, scores[name] / (2 * config.kp_inliers)) + 0.5)
        return result

    return rule


def make_anchor_rule(strict: Rule, relaxed: Rule, mode: str, reach: float = 3.0):
    """Combine two rules with the text-anchor signal (see ``anchors``).

    ``boost``: a candidate passes the strict rule, or passes the relaxed rule while lying near its anchor line.
    ``gate``: a candidate passes the strict rule and lies near its anchor line (when the label has any anchor
    line for that pictogram; otherwise the strict rule alone decides).
    """
    from src.cv.symbols_v2.anchors import near_anchor

    def rule(feats: Features, box, anchors) -> dict[str, float]:
        hard = strict(feats)
        loose = relaxed(feats)
        out = {}
        for name in SYMBOL_NAMES:
            near = near_anchor(name, box, anchors, reach)
            if mode == "boost":
                out[name] = hard[name] if hard[name] > 0 else (loose[name] if near else 0.0)
            else:
                out[name] = hard[name] if (near or not anchors.get(name)) else 0.0
        return out

    rule.uses_anchor = True  # type: ignore[attr-defined]
    return rule


def decide(scored: list[Scored], rule: Rule, anchors: dict | None = None) -> list[SymbolDetection]:
    """Keep the best-scoring candidate per pictogram under a rule, then drop overlapping claims.

    A rule made by ``make_anchor_rule`` is also given the box and the anchor lines (``anchors``, from OCR text).
    """
    best: dict[str, SymbolDetection] = {}
    for item in scored:
        if getattr(rule, "uses_anchor", False):
            scores = rule(item.feats, item.box, anchors or {})
        else:
            scores = rule(item.feats)
        for name, score in scores.items():
            if score > 0 and (name not in best or score > best[name].conf):
                best[name] = SymbolDetection(name=name, iso_ref="", conf=float(score), bbox=item.box)
    return drop_overlaps(list(best.values()))


def detect(image: np.ndarray, config: Config | None = None) -> list[SymbolDetection]:
    """Search a whole upright RGB label for the two pictograms and return at most one box per name."""
    config = config or Config()
    methods = {"sil": ("sil",), "sift": ("sift",), "orb": ("orb",), "fuse": ("sil", "sift")}[config.method]
    scored = featurize(
        image, methods=methods, work_short_side=config.work_short_side, style_ids=config.style_ids
    )
    return decide(scored, make_rule(config))


def drop_overlaps(found: list[SymbolDetection]) -> list[SymbolDetection]:
    """Keep the better of two names that claim overlapping boxes; order by name."""
    kept: list[SymbolDetection] = []
    for candidate in sorted(found, key=lambda item: -item.conf):
        x1, y1, w1, h1 = candidate.bbox
        clash = False
        for other in kept:
            x2, y2, w2, h2 = other.bbox
            inter = max(0.0, min(x1 + w1, x2 + w2) - max(x1, x2)) * max(0.0, min(y1 + h1, y2 + h2) - max(y1, y2))
            clash = clash or inter / (w1 * h1 + w2 * h2 - inter) > 0.3
        if not clash:
            kept.append(candidate)
    return sorted(kept, key=lambda item: SYMBOL_NAMES.index(item.name))
