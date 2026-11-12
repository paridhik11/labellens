"""Fixed-seed development / held-out split of the answerable queries (Step 17a).

WHY SPLIT?
Step 17 tries three retrieval tweaks and tunes their settings (weights, cut-offs).
If we tune and report on the same 57 queries, the result is flattering: the
settings are fitted to those very queries. So:
  - dev:      we may look at it, tune on it, and read failures from it.
  - held-out: scored ONCE, after every setting is frozen. This is the headline.

HOW THE SPLIT IS MADE
Queries are grouped by type (direct, field_req, ...). Inside each type they are
ordered by module and then shuffled with a fixed seed, and dealt alternately to
dev and held-out like cards. Dealing from a module-sorted list keeps both
modules spread across both halves. When a type has an odd count the extra query
goes to dev for the first odd type, held-out for the next, and so on, so the two
halves end up the same size within one query.

no_answer queries have no relevant chunk, so nDCG is undefined for them (Step
10b). They are listed separately and belong to neither half.

Run:  python -m src.ir.split --queries data/eval/queries_t1.tsv \
          --out data/eval/split_t1.json
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from src.ir.eval import NO_ANSWER, QueryRow, load_query_rows

SEED = 42


def make_split(rows: list[QueryRow], seed: int = SEED) -> dict:
    """Splits answerable queries into dev and held-out, stratified by type.

    Args:
        rows: all query rows (qid, query, module, qtype).
        seed: fixed random seed so the split is reproducible.

    Returns:
        Dict with keys seed, dev, heldout, no_answer (each a sorted list of
        qids except seed).
    """
    rng = random.Random(seed)
    by_type: dict[str, list[QueryRow]] = defaultdict(list)
    no_answer: list[str] = []
    for row in rows:
        if row.qtype == NO_ANSWER:
            no_answer.append(row.qid)
        else:
            by_type[row.qtype].append(row)

    dev: list[str] = []
    heldout: list[str] = []
    extra_to_dev = True  # who gets the extra query of the next odd-sized type
    for qtype in sorted(by_type):
        group = sorted(by_type[qtype], key=lambda r: r.qid)
        rng.shuffle(group)
        group.sort(key=lambda r: r.module)  # stable: shuffled order kept per module
        start_with_dev = True
        if len(group) % 2 == 1:
            start_with_dev = extra_to_dev
            extra_to_dev = not extra_to_dev
        for i, row in enumerate(group):
            to_dev = (i % 2 == 0) == start_with_dev
            (dev if to_dev else heldout).append(row.qid)

    return {
        "seed": seed,
        "dev": sorted(dev),
        "heldout": sorted(heldout),
        "no_answer": sorted(no_answer),
    }


def load_split(path: str | Path) -> dict:
    """Loads a split file written by make_split."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def summarize(split: dict, rows: list[QueryRow]) -> str:
    """Counts per half, per type and per module, as plain text."""
    info = {r.qid: r for r in rows}
    lines = [f"seed {split['seed']}: dev {len(split['dev'])}, "
             f"heldout {len(split['heldout'])}, no_answer {len(split['no_answer'])}"]
    for key in ("module", "qtype"):
        cells: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for half, idx in (("dev", 0), ("heldout", 1)):
            for qid in split[half]:
                cells[getattr(info[qid], key)][idx] += 1
        lines.append(f"{key:7s}  dev heldout")
        for name in sorted(cells):
            d, h = cells[name]
            lines.append(f"  {name:15s} {d:3d} {h:3d}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Write the dev / held-out query split.")
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--out", default="data/eval/split_t1.json")
    ap.add_argument("--seed", type=int, default=SEED)
    args = ap.parse_args()
    rows = load_query_rows(args.queries)
    split = make_split(rows, args.seed)
    Path(args.out).write_text(json.dumps(split, indent=1) + "\n", encoding="utf-8")
    print(summarize(split, rows))


if __name__ == "__main__":
    main()
