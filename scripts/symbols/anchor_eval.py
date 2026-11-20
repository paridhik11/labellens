"""Phase 5: how the text-anchor rule combines with the silhouette and CNN scorers, on one styled dataset.

    python scripts/symbols/anchor_eval.py --dataset data/synthetic/styled_dev_anch --freeze results/logs/dev_best.json

Needs cached features (``experiment features``, tags ``base`` and ``cnn_mined``) and cached OCR (``experiment ocr``).
Settings come from the frozen dev choices; the relaxed rule used by ``boost`` is fixed in advance (silhouette 0.6,
CNN probability 0.2). Held-out datasets need ``--allow-heldout`` (logged).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import rate  # noqa: E402
from src.cv.symbols_v2.detector import Config, make_anchor_rule, make_rule  # noqa: E402
from src.cv.symbols_v2.experiment import compute_anchors, compute_features, evaluate, guard_heldout  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from dev_table import merge, summary  # noqa: E402

NAMES = ("manufacturer", "expiry")


def cnn_rule(threshold: float):
    """Accept a candidate when the CNN probability for a name reaches the threshold."""
    return lambda f: {n: (f["cnn"][n] if f["cnn"][n] >= threshold else 0.0) for n in NAMES}


def main() -> int:
    """Print the table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--cnn-tag", default="cnn_mined")
    parser.add_argument("--reach", type=float, default=3.0)
    parser.add_argument("--allow-heldout", action="store_true")
    args = parser.parse_args()
    guard_heldout(args.dataset, args.allow_heldout, "anchor_eval")
    chosen = json.loads(args.freeze.read_text(encoding="utf-8"))
    items, feats = compute_features(args.dataset, ("sil", "sift", "orb"), "base")
    _, cnn_feats = compute_features(args.dataset, ("sil",), args.cnn_tag, extra=("cnn",))
    feats = merge(feats, cnn_feats)
    anchors = compute_anchors(args.dataset, items)
    found = {n: sum(bool(a[n]) for a in anchors) for n in NAMES}
    sil = make_rule(Config(method="sil", sil_threshold=chosen["sil"]["t"], sil_margin=chosen["sil"]["m"]))
    sil_loose = make_rule(Config(method="sil", sil_threshold=0.6, sil_margin=0.0))
    cnn, cnn_loose = cnn_rule(chosen["cnn"]["t"]), cnn_rule(0.2)
    variants = {
        "silhouette": (sil, None),
        "silhouette + anchor boost": (make_anchor_rule(sil, sil_loose, "boost", args.reach), anchors),
        "silhouette + anchor gate": (make_anchor_rule(sil, sil_loose, "gate", args.reach), anchors),
        "CNN": (cnn, None), "CNN + anchor boost": (make_anchor_rule(cnn, cnn_loose, "boost", args.reach), anchors),
        "CNN + anchor gate": (make_anchor_rule(cnn, cnn_loose, "gate", args.reach), anchors),
    }
    print(f"anchor lines found: {found} in {len(items)} images")
    print("| variant | recall, all conditions | recall, very hard | false positives |\n| --- | --- | --- | --- |")
    for name, (rule, anchor_data) in variants.items():
        s = summary(evaluate(items, feats, rule, anchor_data))
        print(f"| {name} | {rate(s['m'], s['n'])} | {rate(s['vm'], s['vn'])} | {rate(s['fp'], s['absent'])} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
