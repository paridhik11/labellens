"""Step 25b: per-condition counts with 95% Wilson intervals from the evaluation's log lines.

    python scripts/step25b_summarize.py pv_eval.log results/step25b_print_verify.md

Reads lines like `positive clean 5000 rescan_needed` printed by step25b_print_eval.py and appends the summary table.
Definitions (all per kind and condition, denominators are every photo of that kind and condition):
- false match: a photo of a DIFFERENT label (negative) that the verifier called `match`. The requirement is zero.
- correct match: a photo of the approved label (positive) called `match`.
- missed difference: a negative that was not called `mismatch` (it was `match` or `rescan_needed`).
- rescan rate: share of photos called `rescan_needed`, positives and negatives separately.
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes in n trials."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def cell(k: int, n: int) -> str:
    """`k/n (pct) [lo, hi]`."""
    lo, hi = wilson(k, n)
    return f"{k}/{n} ({100 * k / n:.0f}%) [{100 * lo:.0f}, {100 * hi:.0f}]" if n else "n/a"


def main() -> int:
    """Append the interval table to the report."""
    log, report = Path(sys.argv[1]), Path(sys.argv[2])
    rows = [line.split() for line in log.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.startswith(("positive ", "negative "))]
    count: dict[tuple[str, str], Counter] = {}
    for kind, condition, _seed, *rest in rows:
        count.setdefault((kind, condition), Counter())[" ".join(rest)] += 1
    out = ["", "## Per condition with 95% Wilson intervals (percent, in brackets)", "",
           "| condition | photos (pos/neg) | false match (neg called match) | correct match (pos called match) | "
           "missed difference (neg not called mismatch) | rescan rate pos | rescan rate neg |",
           "|---|---|---|---|---|---|---|"]
    total = Counter()
    for condition in ("clean", "moderate", "hard", "all"):
        pos, neg = Counter(), Counter()
        for (kind, cond), c in count.items():
            if condition in (cond, "all"):
                (pos if kind == "positive" else neg).update(c)
        npos, nneg = sum(pos.values()), sum(neg.values())
        out.append(f"| {condition} | {npos}/{nneg} | {cell(neg['match'], nneg)} | {cell(pos['match'], npos)} | "
                   f"{cell(nneg - neg['mismatch'], nneg)} | {cell(pos['rescan_needed'], npos)} | "
                   f"{cell(neg['rescan_needed'], nneg)} |")
        if condition == "all":
            total = pos + neg
    out += ["", f"Other outcomes: positives called mismatch (false alarms): {sum(c['mismatch'] for (k, _), c in count.items() if k == 'positive')}; "
                f"jobs that failed: {total['job_failed']}.", ""]
    report.write_text(report.read_text(encoding="utf-8") + "\n".join(out), encoding="utf-8")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
