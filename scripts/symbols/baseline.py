"""Phase 0 baseline: the blind symbol detector on the fresh seeds 100 to 102, pooled over seeds, per condition.

    python scripts/symbols/baseline.py --detector v1_blind > results/logs/baseline_v1.md

Prints the main-set recall per condition and, for the negative and variation sets, recall (present symbols found,
IoU >= 0.5) and false positives (absent symbols reported) per case, with Wilson 95% intervals.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import CONDITIONS, load_dataset, markdown_table, named_detector, run_detector  # noqa: E402


def main() -> int:
    """Run and print the tables."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--detector", default="v1_blind")
    parser.add_argument("--seeds", nargs="+", default=["100", "101", "102"])
    parser.add_argument("--data", type=Path, default=Path("data/synthetic"))
    args = parser.parse_args()
    detector = named_detector(args.detector)
    main_records, neg_records = [], []
    for seed in args.seeds:
        main_records += run_detector(load_dataset(args.data / f"fresh{seed}"), detector)
        neg_records += run_detector(load_dataset(args.data / f"freshneg{seed}"), detector)
    print(f"### {args.detector}, main sets (both symbols present), seeds {', '.join(args.seeds)}\n")
    print(markdown_table(main_records, ("condition",), order={"condition": CONDITIONS}))
    print(f"\n### {args.detector}, negative and variation sets, seeds {', '.join(args.seeds)}\n")
    print(markdown_table(neg_records, ("case",)))
    absent = [r for r in neg_records if r["case"] in ("missing_manufacturer", "missing_expiry", "wrong_symbol")]
    print("\n### pooled false positives on absent symbols (missing_manufacturer, missing_expiry, wrong_symbol)\n")
    print(markdown_table([{**r, "case": "absent_pool"} for r in absent], ("case",)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
