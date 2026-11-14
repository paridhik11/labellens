"""Step 16, part 2d: secondary, post-hoc abstention analysis.

Does NOT change the pre-declared primary (hybrid top RRF on ab01 to ab20). It adds:
  set A: ab01 to ab10 answerable vs the 10 no_answer queries (the original 20)
  set B: the existing answerable medicine queries q45 to q61 (q62 is no_answer, so 17) vs
         the same 10 no_answer queries
and more continuous scores. Run after `python -m src.ir.step16_abstain eval`, because that
command rewrites the report and this one appends a "Secondary, post-hoc" section to it.
"""
from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from src.ir.eval import load_chunks, load_query_rows
from src.ir.step16_abstain import (
    CORPUS_PATH,
    DRAFT_PATH,
    AbstainQuery,
    build_medicine_systems,
    evaluate_feature,
    load_abstain_queries,
    retrieve_all,
)
from src.ir.tokenizer import tokenize

QUERIES_T1 = Path("data/eval/queries_t1.tsv")
REPORT = Path("results/step16_abstention.md")
SECTION = "## Secondary, post-hoc"

SCORE_NAMES = (
    "hybrid top RRF",
    "bm25 top",
    "bm25 top / query length",
    "dense top cosine",
    "dense gap rank1-rank5",
    "z-avg(bm25 top, dense top)",
)


def zscores(values: dict[str, float]) -> dict[str, float]:
    """Z-scores of a {qid: value} map using the mean and population std of the map itself.

    Uses no labels. A constant map gives all zeros.
    """
    vals = list(values.values())
    mu = statistics.fmean(vals)
    sd = statistics.pstdev(vals)
    return {k: (0.0 if sd == 0 else (v - mu) / sd) for k, v in values.items()}


def top_score(hits: list) -> float:
    """Rank-1 score, 0.0 when there are no hits."""
    return hits[0].score if hits else 0.0


def rank_gap(hits: list, deep: int = 5) -> float:
    """Rank-1 minus rank-`deep` score (the last hit if fewer than `deep`)."""
    if not hits:
        return 0.0
    return hits[0].score - hits[min(deep, len(hits)) - 1].score


def build_scores(
    runs: dict[str, dict[str, list]], queries: list[AbstainQuery]
) -> dict[str, dict[str, float]]:
    """Score name -> {qid: value} for the six secondary scores over `queries`."""
    ids = [q.qid for q in queries]
    bm = {i: top_score(runs["bm25"][i]) for i in ids}
    de = {i: top_score(runs["dense"][i]) for i in ids}
    n_terms = {q.qid: max(len(tokenize(q.text)), 1) for q in queries}
    zb, zd = zscores(bm), zscores(de)
    return {
        "hybrid top RRF": {i: top_score(runs["hybrid"][i]) for i in ids},
        "bm25 top": bm,
        "bm25 top / query length": {i: bm[i] / n_terms[i] for i in ids},
        "dense top cosine": de,
        "dense gap rank1-rank5": {i: rank_gap(runs["dense"][i]) for i in ids},
        "z-avg(bm25 top, dense top)": {i: (zb[i] + zd[i]) / 2 for i in ids},
    }


def distinct_values(values: dict[str, float], nd: int = 6) -> int:
    """Number of distinct values after rounding to `nd` decimals (the quantisation count)."""
    return len({round(v, nd) for v in values.values()})


def _f(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.3f}"


def section_text(sets: dict[str, tuple[list[AbstainQuery], dict[str, dict[str, float]]]]) -> str:
    """Builds the Markdown for the secondary section."""
    out = [
        SECTION,
        "",
        "Written after the primary results were seen. SECONDARY and exploratory: it does not "
        "change the pre-declared primary (hybrid top RRF, ab01 to ab20). Same method as above "
        "(stratified bootstrap, 10,000 resamples, seed 42; leave-one-out threshold, no_answer "
        "is the positive class). z-scores use the mean and std of the evaluated set itself (no "
        "labels). Set B uses q45 to q61 (17 answerable; q62 is no_answer, so it is not a "
        "positive). Both sets use the same 10 no_answer queries. Intervals are wide.",
        "",
    ]
    for name, (queries, scores) in sets.items():
        n_pos = sum(q.label == "answerable" for q in queries)
        out += [f"### {name}: {n_pos} answerable vs 10 no_answer", ""]
        out += [
            "| Score | AUROC [95% CI] | vs hard only | vs easy only | LOO abstained | Precision | Recall |",
            "|---|---|---|---|---|---|---|",
        ]
        for s in SCORE_NAMES:
            r = evaluate_feature(scores[s], queries)
            cells = []
            for k in ("all", "hard", "easy"):
                d = r[k]
                lo, hi = d["ci"]  # type: ignore[index]
                cells.append(f"{d['auroc']:.3f} [{lo:.3f}, {hi:.3f}]")  # type: ignore[index]
            out.append(
                f"| {s} | " + " | ".join(cells)
                + f" | {r['n_abstain']} | {_f(r['precision'])} | {_f(r['recall'])} |"  # type: ignore[arg-type]
            )
        n_dist = distinct_values(scores["hybrid top RRF"])
        out += ["", f"Distinct hybrid top RRF values across these {len(queries)} queries: {n_dist}.", ""]
    return "\n".join(out) + "\n"


def run(report: Path = REPORT) -> str:
    """Runs both sets and appends (or replaces) the secondary section in the report."""
    abstain = load_abstain_queries(DRAFT_PATH)
    set_a = abstain
    negs = [q for q in abstain if q.label == "no_answer"]
    q_pos = [
        AbstainQuery(r.qid, r.query, "answerable")
        for r in load_query_rows(QUERIES_T1)
        if r.module == "medicine" and r.qtype != "no_answer"
    ]
    set_b = q_pos + negs
    systems = build_medicine_systems(load_chunks(CORPUS_PATH))
    everyone = {q.qid: q for q in set_a + set_b}
    runs = retrieve_all(systems, list(everyone.values()))
    sets = {
        "Set A (ab01 to ab10)": (set_a, build_scores(runs, set_a)),
        "Set B (q45 to q61)": (set_b, build_scores(runs, set_b)),
    }
    text = section_text(sets)
    base = report.read_text(encoding="utf-8")
    if SECTION in base:
        base = base[: base.index(SECTION)].rstrip("\n") + "\n"
    report.write_text(base + "\n" + text, encoding="utf-8")
    return text


def main() -> None:
    """Entry point: python -m src.ir.step16_secondary."""
    argparse.ArgumentParser(description=__doc__.split("\n")[0]).parse_args()
    print(run())


if __name__ == "__main__":
    main()
