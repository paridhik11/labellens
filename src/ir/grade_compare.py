"""Step 13: compare LLM relevance grades with human grades.

Inputs
  data/eval/sample_pari.csv, data/eval/sample_parth.csv   human grades (column `grade`)
  data/eval/pool_t1_llm.csv                               LLM grades (column `llm_grade`)

What it reports (all on the rows a human graded)
  1. Agreement: exact agreement, weighted kappa (linear and quadratic),
     binary agreement and binary kappa (grade >= 1 counts as relevant).
  2. The same numbers for human vs human on the rows both people graded.
  3. System ranking: nDCG@10 of every retrieval system under human qrels and
     under LLM qrels, and Kendall's tau between the two rankings.
  4. Per-system grade distribution of the top 10 results, human vs LLM.

Tiny worked example of weighted kappa (grades 0, 1, 2):
  A person says 2 and the LLM says 1: a small miss, so a small penalty.
  A person says 2 and the LLM says 0: a big miss, so a big penalty.
  Plain kappa treats both misses the same, weighted kappa does not.
  Linear weight = |i - j| / 2, quadratic weight = ((i - j) / 2) ** 2.

Where two humans graded the same row (the shared queries), the human qrels use
the first file's grade (Pari). Human-vs-human agreement is reported separately,
so nothing is hidden by that choice.

This module only reads the human files. It never writes to them or to the pool.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.eval import (
    NO_ANSWER,
    build_systems,
    evaluate,
    find_corpus_gaps,
    load_chunks,
    load_qrels,
    load_query_rows,
    split_no_answer,
)
from src.ir.llm_grade_tool import LLM_PATH, llm_csv_to_qrels

LABELS = (0, 1, 2)
HUMAN_PATHS = ("data/eval/sample_pari.csv", "data/eval/sample_parth.csv")
Key = tuple[str, str]


# ---------- loading ----------

def load_human_grades(path: str | Path) -> dict[Key, int]:
    """Reads (qid, chunk_id) -> human grade from an annotator CSV.

    Rows with an empty grade are skipped. A grade outside 0, 1, 2 raises.
    """
    grades: dict[Key, int] = {}
    with Path(path).open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            raw = (r.get("grade") or "").strip()
            if not raw:
                continue
            g = int(raw)
            if g not in LABELS:
                raise ValueError(f"{path}: bad grade {raw!r} for {r['qid']}:{r['chunk_id']}")
            grades[(r["qid"], r["chunk_id"])] = g
    return grades


def load_llm_grades(path: str | Path = LLM_PATH) -> dict[Key, int]:
    """Reads (qid, chunk_id) -> LLM grade from pool_t1_llm.csv."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return {(r["qid"], r["chunk_id"]): int(r["llm_grade"]) for r in csv.DictReader(f)}


def merge_human(files: list[dict[Key, int]]) -> dict[Key, int]:
    """Merges annotator grades; the earlier file wins on rows graded twice."""
    merged: dict[Key, int] = {}
    for g in reversed(files):
        merged.update(g)
    return merged


def to_qrels(grades: dict[Key, int]) -> dict[str, dict[str, int]]:
    """Turns (qid, chunk_id) -> grade into qid -> {chunk_id: grade}."""
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    for (qid, cid), g in grades.items():
        qrels[qid][cid] = g
    return dict(qrels)


# ---------- agreement ----------

def weighted_kappa(a: list[int], b: list[int], weights: str = "quadratic") -> float:
    """Weighted Cohen's kappa for ordinal grades 0, 1, 2.

    kappa = 1 - (observed weighted disagreement / expected weighted disagreement).
    weights is 'linear' or 'quadratic'. Returns 1.0 when expected disagreement
    is 0 and the raters agree everywhere, else 0.0 in that degenerate case.
    """
    if len(a) != len(b) or not a:
        raise ValueError("need two non-empty lists of equal length")
    if weights not in ("linear", "quadratic"):
        raise ValueError("weights must be 'linear' or 'quadratic'")
    n, top = len(a), len(LABELS) - 1

    def w(i: int, j: int) -> float:
        d = abs(i - j) / top
        return d if weights == "linear" else d * d

    ca, cb = Counter(a), Counter(b)
    observed = sum(w(x, y) for x, y in zip(a, b, strict=True)) / n
    expected = sum(w(i, j) * (ca[i] / n) * (cb[j] / n) for i in LABELS for j in LABELS)
    if expected == 0:
        return 1.0 if observed == 0 else 0.0
    return 1.0 - observed / expected


def agreement_report(a: dict[Key, int], b: dict[Key, int]) -> dict[str, float]:
    """Agreement numbers between two graders on the rows both graded."""
    keys = sorted(set(a) & set(b))
    if not keys:
        raise ValueError("no overlapping rows")
    xa = [a[k] for k in keys]
    xb = [b[k] for k in keys]
    ba = [int(x >= 1) for x in xa]
    bb = [int(x >= 1) for x in xb]
    n = len(keys)
    po_bin = sum(p == q for p, q in zip(ba, bb, strict=True)) / n
    pa, pb = sum(ba) / n, sum(bb) / n
    pe_bin = pa * pb + (1 - pa) * (1 - pb)
    kappa_bin = 1.0 if pe_bin == 1 else (po_bin - pe_bin) / (1 - pe_bin)
    return {
        "n": n,
        "exact": sum(p == q for p, q in zip(xa, xb, strict=True)) / n,
        "kappa_linear": weighted_kappa(xa, xb, "linear"),
        "kappa_quadratic": weighted_kappa(xa, xb, "quadratic"),
        "binary_agreement": po_bin,
        "binary_kappa": kappa_bin,
    }


def confusion(a: dict[Key, int], b: dict[Key, int]) -> dict[tuple[int, int], int]:
    """Counts (grade in a, grade in b) on the overlapping rows."""
    c: Counter[tuple[int, int]] = Counter()
    for k in set(a) & set(b):
        c[(a[k], b[k])] += 1
    return dict(c)


# ---------- ranking agreement ----------

def kendall_tau(x: list[float], y: list[float]) -> float:
    """Kendall's tau-b between two score lists (ties handled).

    Counts pairs ranked the same way (concordant) minus pairs ranked the
    opposite way (discordant), divided by the pairs that are not tied.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("need two lists of equal length >= 2")
    conc = disc = tx = ty = 0
    for i, j in combinations(range(len(x)), 2):
        dx, dy = x[i] - x[j], y[i] - y[j]
        if dx == 0 and dy == 0:
            continue
        if dx == 0:
            tx += 1
        elif dy == 0:
            ty += 1
        elif (dx > 0) == (dy > 0):
            conc += 1
        else:
            disc += 1
    denom = ((conc + disc + tx) * (conc + disc + ty)) ** 0.5
    return (conc - disc) / denom if denom else 0.0


def bootstrap_mean_ci(
    values: list[float], n: int = 10000, seed: int = 42, level: float = 0.95
) -> tuple[float, float, float]:
    """Mean of per-query values with a percentile bootstrap interval.

    Resamples the queries with replacement n times, takes the mean of each
    resample, and reads the (1-level)/2 and (1+level)/2 percentiles.
    Fixed seed, so the same input always gives the same interval.
    Returns (mean, low, high).
    """
    if not values:
        raise ValueError("need at least one value")
    rng = random.Random(seed)
    m = len(values)
    means = sorted(sum(values[rng.randrange(m)] for _ in range(m)) / m for _ in range(n))
    lo = means[int((1 - level) / 2 * n)]
    hi = means[min(int((1 + level) / 2 * n), n - 1)]
    return sum(values) / m, lo, hi


def usable_queries(
    qrels_list: list[dict[str, dict[str, int]]],
    answerable: list[str],
) -> list[str]:
    """Answerable qids graded in every qrels and not a corpus gap in any of them."""
    keep = []
    for qid in answerable:
        if all(qid in q for q in qrels_list) and not any(
            qid in find_corpus_gaps([qid], q) for q in qrels_list
        ):
            keep.append(qid)
    return keep


def rank_systems(results: dict[str, dict[str, float]], metric: str = "ndcg") -> list[str]:
    """System names sorted best first by one metric."""
    return sorted(results, key=lambda s: -results[s][metric])


def top_k_grade_distribution(
    systems: list[Retriever],
    queries: dict[str, str],
    grades: dict[Key, int],
    k: int = 10,
) -> dict[str, dict[str, float]]:
    """Per system: share of top-k results graded 0, 1, 2, plus how many were ungraded.

    Ungraded results count as 0 and are reported in the 'ungraded' count.
    """
    out: dict[str, dict[str, float]] = {}
    for s in systems:
        c: Counter[int] = Counter()
        ungraded = total = 0
        for qid, q in queries.items():
            for h in s.search(q, k=k):
                total += 1
                g = grades.get((qid, h.doc_id))
                if g is None:
                    ungraded += 1
                    g = 0
                c[g] += 1
        out[s.name] = {
            **{f"g{g}": c[g] / max(total, 1) for g in LABELS},
            "total": total,
            "ungraded": ungraded,
        }
    return out


# ---------- report ----------

def _fmt_agreement(r: dict[str, float]) -> str:
    return (
        f"| {int(r['n'])} | {r['exact']:.3f} | {r['kappa_linear']:.3f} | "
        f"{r['kappa_quadratic']:.3f} | {r['binary_agreement']:.3f} | {r['binary_kappa']:.3f} |"
    )


AGREEMENT_HEADER = (
    "| rows | exact agreement | weighted kappa (linear) | weighted kappa (quadratic) "
    "| binary agreement | binary kappa |\n|---|---|---|---|---|---|"
)


def _confusion_md(c: dict[tuple[int, int], int], row_name: str, col_name: str) -> str:
    lines = [f"| {row_name} \\ {col_name} | 0 | 1 | 2 |", "|---|---|---|---|"]
    for i in LABELS:
        lines.append(f"| {i} | " + " | ".join(str(c.get((i, j), 0)) for j in LABELS) + " |")
    return "\n".join(lines)


def build_report(
    human_files: dict[str, dict[Key, int]],
    llm: dict[Key, int],
    systems_by_module: dict[str, list[Retriever]],
    query_rows: list,
    llm_models: str = "",
) -> str:
    """Builds the whole Step 13 markdown report."""
    names = list(human_files)
    human = merge_human(list(human_files.values()))
    out: list[str] = ["# Step 13: LLM grades vs human grades", ""]

    out += [
        "## Data",
        f"- Human-graded rows (merged, first file wins on shared rows): {len(human)}",
        f"- Human queries: {len({q for q, _ in human})}",
        f"- LLM model id(s) in pool_t1_llm.csv: {llm_models or 'not given'}",
        "",
    ]
    for n, g in human_files.items():
        out.append(f"- {n}: {len(g)} rows, grades {dict(sorted(Counter(g.values()).items()))}")
    out.append(f"- Merged human grades: {dict(sorted(Counter(human.values()).items()))}")
    llm_on_human = {k: llm[k] for k in human if k in llm}
    out.append(
        f"- LLM grades on the same rows: {dict(sorted(Counter(llm_on_human.values()).items()))}"
        f" ({len(llm_on_human)} of {len(human)} rows have an LLM grade)"
    )
    out.append("")

    no_answer_qids = {r.qid for r in query_rows if r.qtype == NO_ANSWER}
    excluded = sorted({q for q, _ in human} & no_answer_qids)

    def without(grades: dict[Key, int]) -> dict[Key, int]:
        return {k: v for k, v in grades.items() if k[0] not in no_answer_qids}

    def agreement_table(drop_no_answer: bool) -> list[str]:
        f = without if drop_no_answer else (lambda g: g)
        rows = [
            AGREEMENT_HEADER,
            f"| **{names[0]} only (headline)** "
            + _fmt_agreement(agreement_report(f(human_files[names[0]]), f(llm)))[1:],
            "| all human rows (merged) " + _fmt_agreement(agreement_report(f(human), f(llm)))[1:],
        ]
        for n in names[1:]:
            rows.append(f"| {n} only " + _fmt_agreement(agreement_report(f(human_files[n]), f(llm)))[1:])
        return rows

    out += ["## 1. LLM vs human agreement", "", "### All rows", ""]
    out += agreement_table(False)
    out += [
        "",
        f"### Excluding no_answer queries ({', '.join(excluded) or 'none'})",
        "",
        "A no_answer query has no right passage, so nearly every row is 0 and agreement on",
        "it is easy. Dropping it shows agreement on queries that do have an answer.",
        "",
    ]
    out += agreement_table(True)
    out += ["", f"Confusion matrix, {names[0]} only (rows = human, columns = LLM):", ""]
    out.append(_confusion_md(confusion(human_files[names[0]], llm), names[0], "LLM"))
    out += ["", "Confusion matrix, all human rows (rows = human, columns = LLM):", ""]
    out.append(_confusion_md(confusion(human, llm), "human", "LLM"))
    out.append("")

    if len(human_files) >= 2:
        a, b = list(human_files.values())[:2]
        shared = set(a) & set(b)
        out += [
            f"## 2. Human vs human ({names[0]} vs {names[1]}, rows both graded)",
            "",
        ]
        if shared:
            out += [AGREEMENT_HEADER, "| shared rows " + _fmt_agreement(agreement_report(a, b))[1:]]
            out += ["", _confusion_md(confusion(a, b), names[0], names[1]), ""]
            sa = {k: a[k] for k in shared}
            sb = {k: b[k] for k in shared}
            out += [
                "On the same shared rows, each human against the LLM:",
                "",
                AGREEMENT_HEADER,
                f"| {names[0]} vs LLM " + _fmt_agreement(agreement_report(sa, llm))[1:],
                f"| {names[1]} vs LLM " + _fmt_agreement(agreement_report(sb, llm))[1:],
                "",
            ]
        else:
            out += ["No rows were graded by both annotators.", ""]

    human_qrels = to_qrels(human)
    llm_all = to_qrels(llm)
    answerable, _ = split_no_answer(query_rows)
    human_qids = {q for q, _ in human}
    ans_qids = [r.qid for r in answerable if r.qid in human_qids]
    use = usable_queries([human_qrels, llm_all], ans_qids)
    dropped = sorted(human_qids - set(use))
    out += [
        "## 3. System ranking by nDCG@10",
        "",
        "Systems are built per module (device queries search device chunks, medicine queries",
        "search medicine chunks), the same way the pool was made, so no result is unjudged",
        "because of a module mix-up.",
        f"Queries used (answerable, graded by both, not a corpus gap under either): {len(use)}",
        f"Human-sample queries left out (no_answer or gap): {', '.join(dropped) or 'none'}",
        "",
    ]
    by_module: dict[str, list[str]] = defaultdict(list)
    for r in query_rows:
        if r.qid in set(use):
            by_module[r.module].append(r.qid)
    qtext = {r.qid: r.query for r in query_rows}

    per_module: dict[str, dict[str, dict[str, list[float]]]] = {}
    dist: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
    for mod, qids in sorted(by_module.items()):
        systems = systems_by_module[mod]
        queries = {q: qtext[q] for q in qids}
        _, h_pq = evaluate(systems, queries, {q: human_qrels[q] for q in qids})
        _, l_pq = evaluate(systems, queries, {q: llm_all[q] for q in qids})
        per_module[mod] = {
            "human": {s: h_pq[s]["ndcg"] for s in h_pq},
            "llm": {s: l_pq[s]["ndcg"] for s in l_pq},
        }
        dist[mod] = {
            "human": top_k_grade_distribution(systems, queries, human),
            "llm": top_k_grade_distribution(systems, queries, llm),
        }

    def ndcg_table(
        title: str,
        h_vals: dict[str, list[float]],
        l_vals: dict[str, list[float]],
        n: int,
    ) -> None:
        h_m = {s: sum(v) / len(v) for s, v in h_vals.items()}
        l_m = {s: sum(v) / len(v) for s, v in l_vals.items()}
        rh = sorted(h_m, key=lambda s: -h_m[s])
        rl = sorted(l_m, key=lambda s: -l_m[s])
        names_ = list(h_m)
        tau = kendall_tau([h_m[s] for s in names_], [l_m[s] for s in names_])
        out.extend([
            f"### {title} ({n} queries)",
            "",
            "| system | nDCG@10 human | nDCG@10 LLM | rank human | rank LLM |",
            "|---|---|---|---|---|",
        ])
        for s in names_:
            out.append(
                f"| {s} | {h_m[s]:.3f} | {l_m[s]:.3f} | {rh.index(s) + 1} | {rl.index(s) + 1} |"
            )
        pairs = len(names_) * (len(names_) - 1) // 2
        out.extend(["", f"Kendall's tau between the two rankings: {tau:.3f} (only {pairs} pairs).", ""])

    ci_lines: list[str] = []

    falling_by_scope: dict[str, list[str]] = {}

    def ci_table(
        title: str, h_vals: dict[str, list[float]], l_vals: dict[str, list[float]], scope: str
    ) -> None:
        ci_lines.extend([
            f"### {title}",
            "",
            "| system | mean LLM - human | 95% CI | interval excludes 0 |",
            "|---|---|---|---|",
        ])
        falling = []
        for s in h_vals:
            diffs = [lv - hv for lv, hv in zip(l_vals[s], h_vals[s], strict=True)]
            mean, lo, hi = bootstrap_mean_ci(diffs)
            if mean < 0:
                falling.append(s)
            ci_lines.append(
                f"| {s} | {mean:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {'yes' if lo > 0 or hi < 0 else 'no'} |"
            )
        falling_by_scope[scope] = falling
        ci_lines.extend([
            "",
            f"Systems whose mean difference is negative (LLM scores lower): {', '.join(falling) or 'none'}.",
            "",
        ])

    for mod, d in per_module.items():
        ndcg_table(f"{mod} module", d["human"], d["llm"], len(by_module[mod]))
    comb_h: dict[str, list[float]] = defaultdict(list)
    comb_l: dict[str, list[float]] = defaultdict(list)
    for d in per_module.values():
        for s, v in d["human"].items():
            comb_h[s] += v
        for s, v in d["llm"].items():
            comb_l[s] += v
    if len(per_module) > 1:
        ndcg_table("Both modules, mean over all queries (reference only)", comb_h, comb_l, len(use))

    out += [
        "### nDCG@10 difference, LLM minus human, with bootstrap 95% interval",
        "",
        "Per-query nDCG@10 under LLM qrels minus under human qrels, resampling queries with",
        "replacement (10000 resamples, seed 42). The sample is small, so intervals are wide.",
        "",
    ]
    ci_table(f"Both modules ({len(use)} queries)", comb_h, comb_l, "both modules")
    for mod, d in per_module.items():
        ci_table(f"{mod} module ({len(by_module[mod])} queries)", d["human"], d["llm"], f"{mod} module")
    only_dense = [sc for sc, f in falling_by_scope.items() if f == ["dense"]]
    others = [f"{sc} ({', '.join(f) or 'none'})" for sc, f in falling_by_scope.items() if f != ["dense"]]
    ci_lines += [
        "### Reading the intervals",
        "",
        f"- Dense is the only system that falls in: {', '.join(only_dense) or 'no scope'}.",
        f"- Other scopes (systems that fall): {'; '.join(others) or 'none'}.",
        "- An interval that includes 0 means the shift could be chance at this sample size.",
        "",
    ]
    out += ci_lines

    out += [
        "## 4. Grade distribution of each system's top 10",
        "",
        "| module | system | grader | share 0 | share 1 | share 2 | results | ungraded |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for mod in dist:
        for s in dist[mod]["human"]:
            for who, label in (("human", "human"), ("llm", "LLM")):
                d = dist[mod][who][s]
                out.append(
                    f"| {mod} | {s} | {label} | {d['g0']:.3f} | {d['g1']:.3f} | {d['g2']:.3f} | "
                    f"{int(d['total'])} | {int(d['ungraded'])} |"
                )
    out.append("")
    return "\n".join(out)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Compare LLM grades with human grades.")
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--llm", default=str(LLM_PATH))
    ap.add_argument("--human", nargs="+", default=list(HUMAN_PATHS))
    ap.add_argument("--out", default="results/step13_llm_vs_human.md")
    ap.add_argument("--qrels-llm-out", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--qrels-human-out", default="data/eval/qrels_t1_human_sample.tsv")
    ap.add_argument("--no-dense", action="store_true")
    a = ap.parse_args()

    human_files = {Path(p).stem.replace("sample_", ""): load_human_grades(p) for p in a.human}
    llm = load_llm_grades(a.llm)

    n = llm_csv_to_qrels(a.llm, a.qrels_llm_out)
    print(f"wrote {a.qrels_llm_out} ({n} rows)")
    human_qrels = to_qrels(merge_human(list(human_files.values())))
    with Path(a.qrels_human_out).open("w", encoding="utf-8", newline="\n") as f:
        for qid in sorted(human_qrels):
            for cid in sorted(human_qrels[qid]):
                f.write(f"{qid} 0 {cid} {human_qrels[qid][cid]}\n")
    print(f"wrote {a.qrels_human_out}")
    load_qrels(a.qrels_human_out)  # parse check

    with Path(a.llm).open(encoding="utf-8", newline="") as f:
        models = ", ".join(sorted({r["model"] for r in csv.DictReader(f)}))

    all_chunks: list[Chunk] = load_chunks(a.corpus)
    systems_by_module: dict[str, list[Retriever]] = {}
    for mod in sorted({c.module for c in all_chunks if c.module}):
        chunks = [c for c in all_chunks if c.module == mod]
        systems_by_module[mod] = build_systems(
            [(c.chunk_id, c.text) for c in chunks], with_dense=not a.no_dense, chunks=chunks
        )
    report = build_report(
        human_files, llm, systems_by_module, load_query_rows(a.queries), models
    )
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
