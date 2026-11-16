"""Dev-set table of every detector idea: pick each idea's best setting on dev (false positives <= 2%), report it.

    python scripts/symbols/dev_table.py --out results/logs/dev_table.md

Settings are chosen on the dev styles only (cached features of ``styled_dev``); the held-out styles are not touched.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import CONDITIONS, rate, tally  # noqa: E402
from src.cv.symbols_v2.detector import Config, make_rule  # noqa: E402
from src.cv.symbols_v2.experiment import compute_features, evaluate  # noqa: E402

NAMES = ("manufacturer", "expiry")


def merge(first: list[list], second: list[list]) -> list[list]:
    """Combine the features of two caches of the same dataset (same candidates, same order)."""
    for a, b in zip(first, second, strict=True):
        for x, y in zip(a, b, strict=True):
            x.feats.update(y.feats)
    return first


def summary(records: list[dict]) -> dict:
    """Pooled recall and false-positive counts, plus very-hard recall."""
    table = tally(records, ("case",))
    styled = table[("styled",)]
    fp = sum(c["false_positive"] for k, c in table.items() if k[0] != "styled")
    absent = sum(c["absent"] for k, c in table.items() if k[0] != "styled")
    vh = tally([r for r in records if r["case"] == "styled"], ("condition",))[("very_hard",)]
    return {
        "m": styled["matched"], "n": styled["expected"], "fp": fp, "absent": absent,
        "vm": vh["matched"], "vn": vh["expected"],
    }


def main() -> int:
    """Build the table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("data/synthetic/styled_dev"))
    parser.add_argument("--cnn-tag", default="cnn_mined")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--freeze", type=Path, default=None, help="Write the chosen settings as JSON here")
    args = parser.parse_args()
    items, feats = compute_features(args.dataset, ("sil", "sift", "orb"), "base")
    _, cnn_feats = compute_features(args.dataset, ("sil",), args.cnn_tag, extra=("cnn",))
    feats = merge(feats, cnn_feats)

    def cnn_rule(t: float) -> Callable:
        return lambda f: {n: (f["cnn"][n] if f["cnn"][n] >= t else 0.0) for n in NAMES}

    grids: dict[str, list[tuple[dict, Callable]]] = {
        "sil": [({"t": t, "m": m}, make_rule(Config(method="sil", sil_threshold=t, sil_margin=m)))
                for t, m in itertools.product((0.65, 0.7, 0.75, 0.8), (0.0, 0.03, 0.06, 0.1))],
        "sift": [({"n": n, "m": m}, make_rule(Config(method="sift", kp_inliers=n, kp_margin=m)))
                 for n, m in itertools.product((6, 8, 10, 12, 16), (0, 3, 6))],
        "orb": [({"n": n, "m": m}, make_rule(Config(method="orb", kp_inliers=n, kp_margin=m)))
                for n, m in itertools.product((6, 8, 10, 12, 16), (0, 3, 6))],
        "cnn": [({"t": t}, cnn_rule(t)) for t in (0.5, 0.7, 0.8, 0.9, 0.95)],
    }
    best: dict[str, tuple[dict, dict, Callable]] = {}
    for method, grid in grids.items():
        scored = [(params, summary(evaluate(items, feats, rule)), rule) for params, rule in grid]
        ok = [s for s in scored if s[1]["fp"] / s[1]["absent"] <= 0.02] or scored
        best[method] = max(ok, key=lambda s: (s[1]["m"], -s[1]["fp"]))

    def either(a: Callable, b: Callable) -> Callable:
        return lambda f: {n: max(a(f)[n], b(f)[n]) for n in NAMES}

    def both(a: Callable, b: Callable) -> Callable:
        return lambda f: {n: (min(a(f)[n], b(f)[n]) if min(a(f)[n], b(f)[n]) > 0 else 0.0) for n in NAMES}

    combos = {
        "sil OR sift": either(best["sil"][2], best["sift"][2]),
        "sil OR cnn": either(best["sil"][2], best["cnn"][2]),
        "sil AND cnn": both(best["sil"][2], best["cnn"][2]),
    }
    rows = [(f"{m} {json.dumps(best[m][0])}", best[m][1]) for m in best]
    rows += [(name, summary(evaluate(items, feats, rule))) for name, rule in combos.items()]
    lines = ["| idea (setting chosen on dev) | recall, all conditions | recall, very hard | false positives |",
             "| --- | --- | --- | --- |"]
    for name, s in rows:
        lines.append(f"| {name} | {rate(s['m'], s['n'])} | {rate(s['vm'], s['vn'])} | {rate(s['fp'], s['absent'])} |")
    text = "\n".join(lines)
    print(text)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    if args.freeze:
        args.freeze.write_text(json.dumps({m: best[m][0] for m in best}, indent=2) + "\n", encoding="utf-8")
    conditions = tally(
        [r for r in evaluate(items, feats, best["sil"][2]) if r["case"] == "styled"], ("condition",)
    )
    print({k[0]: f"{v['matched']}/{v['expected']}" for k, v in conditions.items()}, CONDITIONS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
