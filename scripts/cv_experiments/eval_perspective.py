"""Generate fresh fixed-seed labels and score standalone template-ratio flattening."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.cv.perspective import evaluate_dataset
from src.gen.generate_dataset import generate_dataset


def main(argv: list[str] | None = None) -> int:
    """Run the three-seed benchmark, keeping missing detections in denominators."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic/perspective_task7a"))
    parser.add_argument("--seeds", nargs="+", type=int, default=[7001, 7002, 7003])
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args(argv)
    if len(args.seeds) != len(set(args.seeds)):
        parser.error("Seeds must be distinct")
    template = json.loads(Path("src/gen/templates/test_device.json").read_text())
    ratio = template["size_mm"]["w"] / template["size_mm"]["h"]
    runs = []
    totals = {condition: {"images": 0, "detected": 0, "within_10px": 0}
              for condition in ("clean", "moderate", "hard")}
    for seed in args.seeds:
        folder = args.output / f"seed_{seed}"
        generate_dataset(folder, seed=seed, labels_per_condition=args.count)
        results = evaluate_dataset(folder, ratio)
        runs.append({"seed": seed, "conditions": results})
        for condition, metrics in results.items():
            for key in totals[condition]:
                totals[condition][key] += metrics[key]
    report = {"criterion": "all four corners within 10 source pixels", "aspect_ratio": ratio,
              "per_seed": runs, "totals": totals,
              "limits": "synthetic, one template family; upright rotation; no real-photo accuracy claim"}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "evaluation.json").write_text(json.dumps(report, indent=2) + "\n")
    for condition, metrics in totals.items():
        print(f"{condition}: detected={metrics['detected']}/{metrics['images']}, "
              f"within_10px={metrics['within_10px']}/{metrics['images']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
