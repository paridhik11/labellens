"""Phase 4: zero-shot CLIP on candidate crops. Choose the threshold on dev, freeze it, then score a dataset once.

    python scripts/symbols/clip_eval.py tune                  # dev only, writes results/symbols_frozen_clip.json
    python scripts/symbols/clip_eval.py score --dataset data/synthetic/styled_heldout --allow-heldout

A candidate is accepted for a name when CLIP's softmax share for that name's prompt is at least the threshold.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import markdown_table, rate  # noqa: E402
from src.cv.symbols_v2.experiment import compute_features, evaluate, guard_heldout  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from dev_table import summary  # noqa: E402

NAMES = ("manufacturer", "expiry")
FROZEN = Path("results/symbols_frozen_clip.json")


def rule(threshold: float):
    """Accept a name when CLIP's share for it reaches the threshold."""
    return lambda f: {n: (f["clip"][n] if f["clip"][n] >= threshold else 0.0) for n in NAMES}


def main() -> int:
    """Tune on dev or score a dataset with the frozen threshold."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["tune", "score"])
    parser.add_argument("--dataset", type=Path, default=Path("data/synthetic/styled_dev"))
    parser.add_argument("--allow-heldout", action="store_true")
    parser.add_argument("--group", nargs="+", default=["style"])
    parser.add_argument("--records", type=Path)
    args = parser.parse_args()
    guard_heldout(args.dataset, args.allow_heldout, f"clip_eval {args.command}")
    items, feats = compute_features(args.dataset, ("sil",), "clip", extra=("clip",), workers=1)
    if args.command == "tune":
        rows = []
        for t in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95):
            s = summary(evaluate(items, feats, rule(t)))
            rows.append((t, s))
            print(f"t={t}: recall {rate(s['m'], s['n'])} | very hard {rate(s['vm'], s['vn'])} | FP {rate(s['fp'], s['absent'])}")
        ok = [r for r in rows if r[1]["fp"] / r[1]["absent"] <= 0.02] or rows
        best = max(ok, key=lambda r: (r[1]["m"], -r[1]["fp"]))
        FROZEN.write_text(json.dumps({"clip_threshold": best[0], "model": "openai/clip-vit-base-patch32",
                                      "chosen_on": "styled_dev"}, indent=2) + "\n", encoding="utf-8")
        print("frozen threshold", best[0])
        return 0
    threshold = json.loads(FROZEN.read_text(encoding="utf-8"))["clip_threshold"]
    records = evaluate(items, feats, rule(threshold))
    print(f"### v2_clip (threshold {threshold})\n")
    print(markdown_table(records, tuple(args.group)))
    if args.records:
        args.records.write_text(json.dumps(records), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
