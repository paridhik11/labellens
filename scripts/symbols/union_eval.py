"""Dev-only measurement of the union rule: accept a symbol when v1 or v2 finds it.

    python scripts/symbols/union_eval.py

Uses the dev styles only (``styled_dev``) and the frozen settings in ``results/symbols_frozen_config.json``.
A symbol counts as found when either detector has a box of that name at IoU >= 0.5 with the truth. An absent symbol
counts as a false positive when either detector reports it (once per name, not once per detector).
Per-condition recall and false positives with Wilson 95% intervals, for v1, v2 (silhouette), v2 (CNN) and both unions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.cv.symbol_eval import CONDITIONS, box_iou, rate, run_detector  # noqa: E402
from src.cv.symbols import detect_symbols_blind  # noqa: E402
from src.cv.symbols_v2.detector import Config, make_rule  # noqa: E402
from src.cv.symbols_v2.experiment import compute_features, evaluate  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from dev_table import merge  # noqa: E402

NAMES = ("manufacturer", "expiry")


def found(record: dict, present: dict) -> set[str]:
    """Names with a detection at IoU >= 0.5 with the truth box."""
    return {n for n, box in present.items()
            if any(d["name"] == n and box_iou(tuple(d["box"]), box) >= 0.5 for d in record["detections"])}


def reported(record: dict) -> set[str]:
    """Names the detector reported anywhere."""
    return {d["name"] for d in record["detections"]}


def main() -> int:
    """Print the per-condition table."""
    cfg = json.loads(Path("results/symbols_frozen_config.json").read_text(encoding="utf-8"))["detectors"]
    root = Path("data/synthetic/styled_dev")
    items, feats = compute_features(root, ("sil",), "base")
    _, cnn_feats = compute_features(root, ("sil",), "cnn_mined", extra=("cnn",))
    feats = merge(feats, cnn_feats)
    sil = make_rule(Config(method="sil", sil_threshold=cfg["v2_sil"]["sil_threshold"], sil_margin=cfg["v2_sil"]["sil_margin"]))
    t = cfg["v2_cnn"]["threshold"]

    def cnn(f):
        return {n: (f["cnn"][n] if f["cnn"][n] >= t else 0.0) for n in NAMES}

    runs = {"v1": run_detector(items, detect_symbols_blind), "v2 silhouette": evaluate(items, feats, sil),
            "v2 CNN": evaluate(items, feats, cnn)}
    table: dict[tuple[str, str], dict[str, int]] = {}

    def add(name: str, condition: str, expected: int, hit: int, absent: int, fp: int) -> None:
        cell = table.setdefault((name, condition), {"e": 0, "h": 0, "a": 0, "f": 0})
        cell["e"] += expected
        cell["h"] += hit
        cell["a"] += absent
        cell["f"] += fp

    for index, item in enumerate(items):
        condition = item.meta["condition"]
        for name in ("v1", "v2 silhouette", "v2 CNN"):
            r = runs[name][index]
            add(name, condition, len(item.present), len(found(r, item.present)), len(item.absent),
                len(reported(r) & set(item.absent)))
        for label, other in (("v1 or v2 silhouette", "v2 silhouette"), ("v1 or v2 CNN", "v2 CNN")):
            a, b = runs["v1"][index], runs[other][index]
            add(label, condition, len(item.present), len(found(a, item.present) | found(b, item.present)),
                len(item.absent), len((reported(a) | reported(b)) & set(item.absent)))
    print("| detector | " + " | ".join(f"{c} recall" for c in CONDITIONS) + " | all recall | false positives, all |")
    print("| --- | " + " | ".join("---" for _ in CONDITIONS) + " | --- | --- |")
    for name in ("v1", "v2 silhouette", "v2 CNN", "v1 or v2 silhouette", "v1 or v2 CNN"):
        cells = [table[(name, c)] for c in CONDITIONS]
        e = sum(c["e"] for c in cells)
        h = sum(c["h"] for c in cells)
        a = sum(c["a"] for c in cells)
        f = sum(c["f"] for c in cells)
        print(f"| {name} | " + " | ".join(rate(c["h"], c["e"]) if c["e"] else "-" for c in cells)
              + f" | {rate(h, e)} | {rate(f, a)} |")
    print("\nFalse positives per condition (absent symbols reported):")
    for name in ("v1", "v2 silhouette", "v2 CNN", "v1 or v2 silhouette", "v1 or v2 CNN"):
        print(f"- {name}: " + ", ".join(f"{c} {rate(table[(name, c)]['f'], table[(name, c)]['a'])}" for c in CONDITIONS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
