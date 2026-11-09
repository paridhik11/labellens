"""IR metrics. qrels for a query: dict doc_id -> graded relevance (0, 1, 2)."""
from __future__ import annotations

import math
import random


def dcg(gains: list[float]) -> float:
    return sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(ranked: list[str], rels: dict[str, int], k: int = 10) -> float:
    gains = [rels.get(d, 0) for d in ranked[:k]]
    ideal = sorted(rels.values(), reverse=True)[:k]
    idcg = dcg(ideal)
    return dcg(gains) / idcg if idcg > 0 else 0.0


def recall_at_k(ranked: list[str], rels: dict[str, int], k: int = 20) -> float:
    relevant = {d for d, g in rels.items() if g > 0}
    if not relevant:
        return 0.0
    return len(relevant & set(ranked[:k])) / len(relevant)


def mrr(ranked: list[str], rels: dict[str, int]) -> float:
    for i, d in enumerate(ranked):
        if rels.get(d, 0) > 0:
            return 1.0 / (i + 1)
    return 0.0


def average_precision(ranked: list[str], rels: dict[str, int]) -> float:
    relevant = {d for d, g in rels.items() if g > 0}
    if not relevant:
        return 0.0
    hits, total = 0, 0.0
    for i, d in enumerate(ranked):
        if d in relevant:
            hits += 1
            total += hits / (i + 1)
    return total / len(relevant)


def paired_bootstrap(a: list[float], b: list[float], n: int = 10000, seed: int = 42) -> float:
    """Approximate p-value that system A is not better than B (one-sided), per-query scores."""
    rng = random.Random(seed)
    diffs = [x - y for x, y in zip(a, b, strict=False)]
    m = len(diffs)
    if m == 0:
        return 1.0
    not_better = 0
    for _ in range(n):
        sample = [diffs[rng.randrange(m)] for _ in range(m)]
        if sum(sample) <= 0:
            not_better += 1
    return not_better / n
