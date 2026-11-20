"""Sweep decision-rule settings on cached features of one dataset and print recall and false positives.

    python scripts/symbols/sweep.py --dataset data/synthetic/styled_dev --tag base

Run from the repo root. Reports pooled recall over the styled case and pooled false positives over the empty and
distractor cases, over all four conditions. Never use it to tune on the held-out dataset.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import tally  # noqa: E402
from src.cv.symbols_v2.detector import Config, make_rule  # noqa: E402
from src.cv.symbols_v2.experiment import compute_features, evaluate  # noqa: E402


def summarise(records: list[dict]) -> tuple[int, int, int, int]:
    """Return (matched, expected, false positives, absent) pooled over conditions."""
    table = tally(records, ("case",))
    styled = table.get(("styled",), {"matched": 0, "expected": 0})
    fp = sum(cell["false_positive"] for key, cell in table.items() if key[0] != "styled")
    absent = sum(cell["absent"] for key, cell in table.items() if key[0] != "styled")
    return styled["matched"], styled["expected"], fp, absent


def main() -> int:
    """Run the grids."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--tag", default="base")
    args = parser.parse_args()
    items, feats = compute_features(args.dataset, ("sil", "sift", "orb"), args.tag)
    rows = []
    for threshold, margin in itertools.product((0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85), (0.0, 0.03, 0.06, 0.1)):
        config = Config(method="sil", sil_threshold=threshold, sil_margin=margin)
        rows.append((f"sil t={threshold} m={margin}", *summarise(evaluate(items, feats, make_rule(config)))))
    for method in ("sift", "orb"):
        for inliers, margin in itertools.product((6, 8, 10, 12, 16, 20), (0, 3, 6)):
            config = Config(method=method, kp_inliers=inliers, kp_margin=margin)
            rows.append((f"{method} n={inliers} m={margin}", *summarise(evaluate(items, feats, make_rule(config)))))
    print("| rule | recall | false positives |\n| --- | --- | --- |")
    for name, matched, expected, fp, absent in sorted(rows, key=lambda r: (r[3] / max(r[4], 1) > 0.02, -r[1])):
        print(f"| {name} | {matched}/{expected} ({100 * matched / expected:.1f}%) |"
              f" {fp}/{absent} ({100 * fp / absent:.1f}%) |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
