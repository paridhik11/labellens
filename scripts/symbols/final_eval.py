"""One-time final evaluation of the frozen detectors on a held-out or real-artwork dataset.

    python scripts/symbols/final_eval.py --dataset data/synthetic/styled_heldout --allow-heldout --group style condition

Settings are read from ``results/symbols_frozen_config.json`` (written before this script was run on held-out data).
Prints one table per detector: recall and false positives per group, with Wilson 95% intervals. The use is logged in
``results/heldout_log.jsonl``. v1 is run through the symbol harness on the same straightened labels.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import CONDITIONS, markdown_table, run_detector  # noqa: E402
from src.cv.symbols import detect_symbols_blind  # noqa: E402
from src.cv.symbols_v2.detector import Config, make_rule  # noqa: E402
from src.cv.symbols_v2.experiment import compute_features, evaluate, guard_heldout  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from dev_table import merge  # noqa: E402

NAMES = ("manufacturer", "expiry")


def main() -> int:
    """Run every frozen detector and print the tables."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--group", nargs="+", default=["style", "condition"])
    parser.add_argument("--allow-heldout", action="store_true")
    parser.add_argument("--no-v1", action="store_true")
    parser.add_argument("--records", type=Path, help="Write all scored records as JSON here")
    args = parser.parse_args()
    cfg = json.loads(Path("results/symbols_frozen_config.json").read_text(encoding="utf-8"))["detectors"]
    guard_heldout(args.dataset, args.allow_heldout, "final_eval " + " ".join(args.group))
    items, feats = compute_features(args.dataset, ("sil", "sift", "orb"), "base")
    _, cnn_feats = compute_features(args.dataset, ("sil",), "cnn_mined", extra=("cnn",))
    feats = merge(feats, cnn_feats)
    sil = make_rule(Config(method="sil", sil_threshold=cfg["v2_sil"]["sil_threshold"], sil_margin=cfg["v2_sil"]["sil_margin"]))
    threshold = cfg["v2_cnn"]["threshold"]

    def cnn(f):
        return {n: (f["cnn"][n] if f["cnn"][n] >= threshold else 0.0) for n in NAMES}

    def both(f):
        a, b = sil(f), cnn(f)
        return {n: (min(a[n], b[n]) if min(a[n], b[n]) > 0 else 0.0) for n in NAMES}

    rules = {
        "v2_sil": sil, "v2_cnn": cnn, "v2_sil_and_cnn": both,
        "v2_sift": make_rule(Config(method="sift", kp_inliers=cfg["v2_sift"]["kp_inliers"], kp_margin=cfg["v2_sift"]["kp_margin"])),
        "v2_orb": make_rule(Config(method="orb", kp_inliers=cfg["v2_orb"]["kp_inliers"], kp_margin=cfg["v2_orb"]["kp_margin"])),
    }
    all_records: dict[str, list[dict]] = {}
    if not args.no_v1:
        all_records["v1_blind"] = run_detector(items, detect_symbols_blind)
    for name, rule in rules.items():
        all_records[name] = evaluate(items, feats, rule)
    for name, records in all_records.items():
        print(f"\n### {name}\n")
        print(markdown_table(records, tuple(args.group), order={"condition": CONDITIONS}))
    if args.records:
        args.records.write_text(json.dumps(all_records), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
