"""External check on the original artwork: the frozen v2 detectors on seeds 100 to 102 (main sets and negative sets).

    python scripts/symbols/ext_eval.py

This is the artwork the old detector was built from plus the independent filled drawing (alt_style). It was not used to
tune anything. Requires cached features (tag cnn_mined, see ``experiment features``). Same tables as ``baseline.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import CONDITIONS, markdown_table  # noqa: E402
from src.cv.symbols_v2.detector import Config, make_rule  # noqa: E402
from src.cv.symbols_v2.experiment import compute_features, evaluate  # noqa: E402

NAMES = ("manufacturer", "expiry")


def main() -> int:
    """Print the tables for the silhouette and CNN detectors."""
    cfg = json.loads(Path("results/symbols_frozen_config.json").read_text(encoding="utf-8"))["detectors"]
    sil = make_rule(Config(method="sil", sil_threshold=cfg["v2_sil"]["sil_threshold"], sil_margin=cfg["v2_sil"]["sil_margin"]))
    threshold = cfg["v2_cnn"]["threshold"]

    def cnn(f):
        return {n: (f["cnn"][n] if f["cnn"][n] >= threshold else 0.0) for n in NAMES}

    for name, rule in (("v2_sil", sil), ("v2_cnn", cnn)):
        main_records, neg_records = [], []
        for seed in ("100", "101", "102"):
            for prefix, bucket in (("fresh", main_records), ("freshneg", neg_records)):
                root = Path("data/synthetic") / f"{prefix}{seed}"
                items, feats = compute_features(root, ("sil",), "cnn_mined", extra=("cnn",))
                bucket += evaluate(items, feats, rule)
        print(f"### {name}, main sets (original artwork), seeds 100 to 102\n")
        print(markdown_table(main_records, ("condition",), order={"condition": CONDITIONS}))
        print(f"\n### {name}, negative and variation sets\n")
        print(markdown_table(neg_records, ("case",)))
        absent = [{**r, "case": "absent_pool"} for r in neg_records
                  if r["case"] in ("missing_manufacturer", "missing_expiry", "wrong_symbol")]
        print("\n" + markdown_table(absent, ("case",)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
