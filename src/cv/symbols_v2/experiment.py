"""Cache raw detector features for a dataset once, then evaluate many decision rules cheaply.

    python -m src.cv.symbols_v2.experiment features --dataset data/synthetic/styled_dev --methods sil sift orb

Features are stored in ``<dataset>/_feats/<tag>.pkl`` (inside gitignored ``data/``). The held-out dataset is
refused unless ``--allow-heldout`` is given, and every such use is appended to ``results/heldout_log.jsonl``,
so the number of looks at held-out styles can be audited.
"""

from __future__ import annotations

import argparse
import json
import pickle
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

from src.common.schemas import SymbolDetection
from src.cv.symbol_eval import Item, load_dataset, score_detections
from src.cv.symbols_v2.detector import Rule, Scored, decide, featurize

ROOT = Path(__file__).resolve().parents[3]
HELDOUT_LOG = ROOT / "results" / "heldout_log.jsonl"


def guard_heldout(root: Path, allow: bool, note: str) -> None:
    """Refuse held-out datasets unless explicitly allowed, and log every allowed use."""
    if "heldout" not in root.name and "real" not in root.name:
        return
    if not allow:
        raise SystemExit(f"{root.name} is held out: pass --allow-heldout (the use is logged)")
    HELDOUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with HELDOUT_LOG.open("a", encoding="utf-8") as handle:
        entry = {"dataset": root.name, "note": note, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        handle.write(json.dumps(entry) + "\n")


def _one(job: tuple[str, tuple[str, ...], dict[str, Any]]) -> list[Scored]:
    """Featurize one cached straightened label (worker for the process pool)."""
    path, methods, options = job
    data = np.load(path)
    extra = None
    if options.get("extra"):
        from src.cv.symbols_v2.registry import extra_featurizers

        extra = extra_featurizers(options["extra"])
    return featurize(data["corrected"], methods=methods, extra=extra, **options.get("kwargs", {}))


def compute_features(
    root: Path, methods: tuple[str, ...], tag: str, *, workers: int = 4, extra: tuple[str, ...] = (),
    kwargs: dict[str, Any] | None = None,
) -> tuple[list[Item], list[list[Scored]]]:
    """Return the dataset items and their cached (or freshly computed) candidate features."""
    items = load_dataset(root, workers=workers)
    cache = root / "_feats" / f"{tag}.pkl"
    if cache.exists():
        return items, pickle.loads(cache.read_bytes())
    cache.parent.mkdir(parents=True, exist_ok=True)
    jobs = [
        (str(root / "_corrected" / (item.key.replace("/", "__") + ".npz")), methods,
         {"extra": extra, "kwargs": kwargs or {}})
        for item in items
    ]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        feats = list(pool.map(_one, jobs, chunksize=2))
    cache.write_bytes(pickle.dumps(feats))
    return items, feats


def evaluate(
    items: list[Item], feats: list[list[Scored]], rule: Rule, anchors: list[dict] | None = None
) -> list[dict[str, Any]]:
    """Apply a decision rule to cached features (and optional per-image anchor lines) and score the detections."""
    detections: list[list[SymbolDetection]] = [
        decide(scored, rule, None if anchors is None else anchors[index]) for index, scored in enumerate(feats)
    ]
    return score_detections(items, detections)


def _ocr_one(path: str) -> list[dict]:
    """Read the text of one cached straightened label (worker for the process pool)."""
    from src.cv.ocr import read_text_default

    return [block.model_dump() for block in read_text_default(np.load(path)["corrected"])]


def compute_anchors(root: Path, items: list[Item], *, workers: int = 3) -> list[dict]:
    """OCR every straightened label once (cached) and return its anchor lines per pictogram."""
    from src.common.schemas import OcrBlock
    from src.cv.symbols_v2.anchors import anchor_lines

    cache = root / "_feats" / "ocr.pkl"
    if cache.exists():
        blocks = pickle.loads(cache.read_bytes())
    else:
        paths = [str(root / "_corrected" / (item.key.replace("/", "__") + ".npz")) for item in items]
        with ProcessPoolExecutor(max_workers=workers) as pool:
            blocks = list(pool.map(_ocr_one, paths, chunksize=2))
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(pickle.dumps(blocks))
    return [anchor_lines([OcrBlock(**block) for block in per_image]) for per_image in blocks]


def main(argv: list[str] | None = None) -> int:
    """Compute and cache features for one dataset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["features", "ocr"])
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--methods", nargs="+", default=["sil"])
    parser.add_argument("--extra", nargs="*", default=[])
    parser.add_argument("--tag", default=None)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--allow-heldout", action="store_true")
    args = parser.parse_args(argv)
    guard_heldout(args.dataset, args.allow_heldout, f"{args.command} {args.methods} {args.extra}")
    if args.command == "ocr":
        anchors = compute_anchors(args.dataset, load_dataset(args.dataset), workers=args.workers)
        print(f"anchors found: expiry {sum(bool(a['expiry']) for a in anchors)}, "
              f"manufacturer {sum(bool(a['manufacturer']) for a in anchors)} of {len(anchors)} images")
        return 0
    tag = args.tag or "_".join([*args.methods, *args.extra])
    started = time.time()
    items, feats = compute_features(
        args.dataset, tuple(args.methods), tag, workers=args.workers, extra=tuple(args.extra)
    )
    print(f"{len(items)} images, {sum(len(f) for f in feats)} candidates, {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
