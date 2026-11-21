"""Once-only evaluation of 100 committed names (med100) at the unchanged medicine threshold and review band."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

from src.gen.eval_medicine_aliases import summarize


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% interval for k successes in n trials."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def by_kind(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Counts per kind: correct (matched, right product), wrong (matched, wrong product), review, rejected."""
    out: dict[str, dict[str, Any]] = {}
    for kind in ('brand', 'generic', 'misspelled', 'decoy'):
        part = [r for r in rows if r['kind'] == kind]
        outcomes = [r['result']['outcome'] for r in part]
        ok = lambda r: r['predicted'] == r['expected']  # noqa: E731
        out[kind] = {
            'n': len(part),
            'correct': sum(r['result']['outcome'] == 'matched' and ok(r) for r in part),
            'wrong': sum(r['result']['outcome'] == 'matched' and not ok(r) for r in part),
            'review': outcomes.count('needs_review'),
            'review_top_correct': sum(r['result']['outcome'] == 'needs_review' and ok(r) for r in part),
            'rejected': outcomes.count('no_reference_match'),
        }
    return out


def main() -> None:
    """Run the real E5b matcher once; persist every query and its latency without altering anything."""
    from src.api.medicine import MATCH_THRESHOLD, REVIEW_BAND, MedicineCatalog, ProductMatcher

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Scoring output is immutable')
    assert MATCH_THRESHOLD == 0.65 and REVIEW_BAND == 0.05
    with Path('src/gen/medicine_match_med100.tsv').open(encoding='utf-8') as handle:
        queries = list(csv.DictReader(handle, delimiter='\t'))
    assert len(queries) == 100 and sum(q['kind'] == 'decoy' for q in queries) == 25
    catalog = MedicineCatalog()
    assert len(catalog.products) == 100
    matcher = ProductMatcher(catalog)
    matcher._load()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rows, times = [], []
    with args.output.open('x', encoding='utf-8') as handle:
        for query in queries:
            start = time.perf_counter()
            result = matcher.match(query['query'])
            times.append(time.perf_counter() - start)
            predicted = catalog.products[result['candidates'][0][0]].name if result['candidates'] else ''
            row = {**query, 'predicted': predicted, 'result': result, 'seconds': times[-1]}
            rows.append(row)
            handle.write(json.dumps(row) + '\n')
            handle.flush()
    positives = [r for r in rows if r['kind'] != 'decoy']
    kinds = by_kind(rows)
    correct = sum(v['correct'] for k, v in kinds.items() if k != 'decoy')
    times.sort()
    summary = {'summary': summarize(rows), 'by_kind': kinds,
               'positives_correct_wilson95': wilson(correct, len(positives)),
               'decoy_clean_wilson95_upper_zero': wilson(0, 25),
               'latency_median_s': statistics.median(times),
               'latency_p90_s': times[int(0.9 * len(times)) - 1]}
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
