"""Step 16: abstention evaluation for the medicine mode.

Parts (CLI sub-commands):
  pool   build the grading pool: bm25, dense and hybrid top 20 on the medicine index only
  check  list no_answer queries that have a chunk graded >= 2 (they must be relabelled)
  eval   score every system's top score and rank-1 margin as an answerable vs no_answer
         predictor (AUROC with bootstrap CI, leave-one-out threshold) and write the report

WHAT IS ABSTENTION?
A system "abstains" when it declines to answer because the evidence is too weak. Here the
signal is a retrieval score: if the best chunk scores low, or rank 1 barely beats rank 2,
the query probably has no answer in the corpus.

WHAT IS AUROC?
Take one answerable query and one no_answer query at random. AUROC is the probability that
the answerable one gets the higher score (ties count one half). 0.5 is a coin flip, 1.0 is
a perfect separation.
"""
from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.eval import build_systems, load_chunks, load_qrels
from src.ir.llm_grade_tool import build_extra_pool

CORPUS_PATH = Path("data/processed/regs.jsonl")
DRAFT_PATH = Path("data/eval/queries_t1_abstain_draft.csv")
TSV_PATH = Path("data/eval/queries_t1_abstain.tsv")
POOL_PATH = Path("data/eval/pool_t1_abstain.csv")
LISTING_PATH = Path("results/step16_pool_listing.csv")
LLM_QRELS_PATH = Path("data/eval/qrels_t1_llm.tsv")
DEPTH = 20
SYSTEMS = ("bm25", "dense", "hybrid")


@dataclass(frozen=True)
class AbstainQuery:
    """One abstention query: label is answerable or no_answer, difficulty easy/hard/empty."""

    qid: str
    text: str
    label: str
    difficulty: str = ""


def load_abstain_queries(path: str | Path = DRAFT_PATH) -> list[AbstainQuery]:
    """Loads the abstention query CSV (qid, text, label, difficulty, rationale)."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    out = [AbstainQuery(r["qid"], r["text"], r["label"], r.get("difficulty", "")) for r in rows]
    bad = [q.qid for q in out if q.label not in ("answerable", "no_answer")]
    if bad:
        raise ValueError(f"unknown label for {bad}")
    if any(q.label == "no_answer" and q.difficulty not in ("easy", "hard") for q in out):
        raise ValueError("every no_answer query needs difficulty easy or hard")
    return out


def write_query_tsv(queries: list[AbstainQuery], out_path: str | Path = TSV_PATH) -> None:
    """Writes the queries as qid, query, module, type TSV so the existing tools can read them."""
    with Path(out_path).open("w", encoding="utf-8", newline="") as f:
        f.write("qid\tquery\tmodule\ttype\n")
        for q in queries:
            f.write(f"{q.qid}\t{q.text}\tmedicine\t{q.label}\n")


def build_medicine_systems(chunks: list[Chunk]) -> dict[str, object]:
    """Builds bm25, dense and hybrid on the medicine chunks only (modules never mix)."""
    med = [c for c in chunks if c.module == "medicine"]
    docs = [(c.chunk_id, c.text) for c in med]
    systems = build_systems(docs, with_dense=True, chunks=med)
    return {s.name: s for s in systems if s.name in SYSTEMS}


def retrieve_all(
    systems: dict[str, object], queries: list[AbstainQuery], depth: int = DEPTH
) -> dict[str, dict[str, list]]:
    """Runs every query on every system: system -> qid -> hits (rank 1 first)."""
    return {
        name: {q.qid: s.search(q.text, k=depth) for q in queries}  # type: ignore[attr-defined]
        for name, s in systems.items()
    }


def listing_rows(
    runs: dict[str, dict[str, list]], depth: int = DEPTH
) -> list[dict[str, str]]:
    """Flattens runs into (system, qid, rank, chunk_id, score) rows for the top `depth`."""
    rows = []
    for system, by_q in runs.items():
        for qid, hits in by_q.items():
            for h in hits[:depth]:
                rows.append(
                    {"system": system, "qid": qid, "rank": str(h.rank),
                     "chunk_id": h.doc_id, "score": f"{h.score:.6f}"}
                )
    return rows


def no_answer_with_grade2(
    queries: list[AbstainQuery], qrels: dict[str, dict[str, int]]
) -> dict[str, list[str]]:
    """Maps each no_answer qid with a chunk graded >= 2 to those chunk ids (sorted)."""
    out: dict[str, list[str]] = {}
    for q in queries:
        if q.label != "no_answer":
            continue
        hits = sorted(c for c, g in qrels.get(q.qid, {}).items() if g >= 2)
        if hits:
            out[q.qid] = hits
    return out


# ---------- evaluation ----------

def auroc(pos: list[float], neg: list[float]) -> float:
    """P(random positive scores above random negative), ties count one half.

    Worked example: pos [0.9, 0.5], neg [0.5, 0.1]: pairs 0.9>0.5, 0.9>0.1, 0.5=0.5, 0.5>0.1
    give (1 + 1 + 0.5 + 1) / 4 = 0.875.
    """
    if not pos or not neg:
        raise ValueError("auroc needs at least one positive and one negative")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def bootstrap_auroc(
    pos: list[float], neg: list[float], n: int = 10000, seed: int = 42
) -> tuple[float, float]:
    """Stratified bootstrap 95% percentile interval of AUROC.

    Answerable and no_answer queries are resampled separately, so both classes are always
    present. Fixed seed, so the same inputs always give the same interval.
    """
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        p = [rng.choice(pos) for _ in pos]
        q = [rng.choice(neg) for _ in neg]
        vals.append(auroc(p, q))
    vals.sort()
    return vals[int(0.025 * n)], vals[min(int(0.975 * n), n - 1)]


def best_threshold(scores: list[float], labels: list[int]) -> float:
    """Threshold with maximum balanced accuracy; label 1 = answerable (score >= t).

    Candidates are the midpoints between consecutive distinct scores plus one below the
    minimum and one above the maximum. Ties are broken by the median tied threshold.
    """
    distinct = sorted(set(scores))
    cands = [distinct[0] - 1.0]
    cands += [(a + b) / 2 for a, b in zip(distinct, distinct[1:], strict=False)]
    cands.append(distinct[-1] + 1.0)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    best: list[float] = []
    best_ba = -1.0
    for t in cands:
        tpr = sum(1 for s, y in zip(scores, labels, strict=True) if y == 1 and s >= t) / n_pos
        tnr = sum(1 for s, y in zip(scores, labels, strict=True) if y == 0 and s < t) / n_neg
        ba = (tpr + tnr) / 2
        if ba > best_ba + 1e-12:
            best, best_ba = [t], ba
        elif abs(ba - best_ba) <= 1e-12:
            best.append(t)
    best.sort()
    return best[len(best) // 2]


def loo_abstain(scores: list[float], labels: list[int]) -> list[bool]:
    """Leave-one-out abstain predictions: threshold from the other queries, applied to one."""
    preds = []
    for i, s in enumerate(scores):
        t = best_threshold(scores[:i] + scores[i + 1:], labels[:i] + labels[i + 1:])
        preds.append(s < t)
    return preds


def precision_recall_abstain(
    preds: list[bool], labels: list[int]
) -> tuple[float | None, float]:
    """Precision and recall of abstaining; no_answer (label 0) is the positive class.

    Precision is None when the system never abstains.
    """
    tp = sum(1 for p, y in zip(preds, labels, strict=True) if p and y == 0)
    n_abstain = sum(preds)
    n_no = sum(1 for y in labels if y == 0)
    return (tp / n_abstain if n_abstain else None), tp / n_no


def features(
    runs: dict[str, dict[str, list]], qid: str, system: str
) -> dict[str, float]:
    """Top score and rank-1 minus rank-2 margin of one system for one query."""
    hits = runs[system][qid]
    top = hits[0].score if hits else 0.0
    second = hits[1].score if len(hits) > 1 else 0.0
    return {"top": top, "margin": top - second}


FEATURES = ("top", "margin")
PRIMARY = ("hybrid", "top")
SEED = 42
N_BOOT = 10000


def pos_neg(
    scores: dict[str, float], queries: list[AbstainQuery], difficulty: str | None = None
) -> tuple[list[float], list[float]]:
    """Scores of answerable queries (positives) and no_answer queries (negatives).

    difficulty "easy" or "hard" keeps only the no_answer queries of that difficulty;
    None keeps all of them.
    """
    pos = [scores[q.qid] for q in queries if q.label == "answerable"]
    neg = [
        scores[q.qid]
        for q in queries
        if q.label == "no_answer" and (difficulty is None or q.difficulty == difficulty)
    ]
    return pos, neg


def evaluate_feature(
    scores: dict[str, float], queries: list[AbstainQuery], n_boot: int = N_BOOT
) -> dict[str, object]:
    """AUROC with bootstrap CI (all, hard-only, easy-only) and leave-one-out abstention.

    Returns a dict with keys all/hard/easy (auroc, ci, n_pos, n_neg) plus precision, recall,
    recall_hard, recall_easy, n_abstain and preds from the leave-one-out threshold on all
    queries.
    """
    out: dict[str, object] = {}
    for name, diff in (("all", None), ("hard", "hard"), ("easy", "easy")):
        pos, neg = pos_neg(scores, queries, diff)
        lo, hi = bootstrap_auroc(pos, neg, n=n_boot, seed=SEED)
        out[name] = {"auroc": auroc(pos, neg), "ci": (lo, hi), "n_pos": len(pos), "n_neg": len(neg)}
    sc = [scores[q.qid] for q in queries]
    lab = [1 if q.label == "answerable" else 0 for q in queries]
    preds = loo_abstain(sc, lab)
    prec, rec = precision_recall_abstain(preds, lab)
    by_diff: dict[str, float | None] = {}
    for diff in ("hard", "easy"):
        idx = [i for i, q in enumerate(queries) if q.label == "no_answer" and q.difficulty == diff]
        by_diff[diff] = sum(preds[i] for i in idx) / len(idx) if idx else None
    out.update(
        precision=prec, recall=rec, recall_hard=by_diff["hard"], recall_easy=by_diff["easy"],
        n_abstain=sum(preds), preds=preds,
    )
    return out


def collect_scores(
    runs: dict[str, dict[str, list]], queries: list[AbstainQuery]
) -> dict[tuple[str, str], dict[str, float]]:
    """(system, feature) -> {qid: value} for every system and feature."""
    return {
        (s, f): {q.qid: features(runs, q.qid, s)[f] for q in queries}
        for s in runs
        for f in FEATURES
    }


def _f(x: float | None, nd: int = 3) -> str:
    """Formats a number, or n/a for None."""
    return "n/a" if x is None else f"{x:.{nd}f}"


def report_markdown(
    queries: list[AbstainQuery],
    scores: dict[tuple[str, str], dict[str, float]],
    results: dict[tuple[str, str], dict[str, object]],
    predecl: str,
    flips: dict[str, list[str]],
    max_grade: dict[str, int],
) -> str:
    """Builds the Markdown report for results/step16_abstention.md."""
    n_ans = sum(q.label == "answerable" for q in queries)
    n_hard = sum(q.difficulty == "hard" for q in queries)
    n_easy = sum(q.difficulty == "easy" for q in queries)
    out = ["# Step 16: abstention evaluation (medicine mode)", ""]
    out += ["## Pre-declaration (committed before any score was computed)", "", predecl.strip(), ""]
    out += ["## Data", ""]
    out += [
        f"- Queries: {len(queries)} ({n_ans} answerable, {len(queries) - n_ans} no_answer: "
        f"{n_hard} hard, {n_easy} easy). Medicine index only (468 chunks).",
        f"- Relabelling check (grade >= 2 chunk for a no_answer query in the judged pool): "
        f"{len(flips)} queries flipped" + (": " + ", ".join(flips) if flips else "") + ".",
        "- Pool: bm25, dense and hybrid top 20, 788 unique (query, chunk) pairs, all graded by the "
        "LLM grader (claude-sonnet-5-5, frozen prompt). Grades are not human grades.",
        "- Highest grade seen per no_answer query: "
        + ", ".join(f"{q.qid}={max_grade.get(q.qid, 0)}" for q in queries if q.label == "no_answer")
        + ".",
        "- No cross-encoder exists in this repo, so the cross-encoder rank-1 score was not computed.",
        "",
        "## Size warning",
        "",
        "With 10 answerable and 10 no_answer queries (10 vs 7 hard, 10 vs 3 easy) every interval "
        "below is very wide and the bootstrap itself is unstable at this size. The easy-only "
        "comparison has only 3 negatives, so its AUROC can take only a few values and its "
        "interval is close to uninformative. Treat all numbers as indicative, not as estimates.",
        "",
        "## AUROC (answerable = positive, higher score = more likely answerable)",
        "",
        f"Stratified bootstrap, {N_BOOT} resamples, seed {SEED}, 95% percentile interval.",
        "",
        "| System | Score | AUROC all 20 [95% CI] | vs hard only (10 v 7) | vs easy only (10 v 3) |",
        "|---|---|---|---|---|",
    ]
    for (s, f), r in results.items():
        cells = []
        for k in ("all", "hard", "easy"):
            d = r[k]
            lo, hi = d["ci"]  # type: ignore[index]
            cells.append(f"{d['auroc']:.3f} [{lo:.3f}, {hi:.3f}]")  # type: ignore[index]
        tag = " (PRIMARY)" if (s, f) == PRIMARY else ""
        out.append(f"| {s} | {f}{tag} | " + " | ".join(cells) + " |")
    out += [
        "",
        "## Abstaining at a leave-one-out threshold (all 20 queries)",
        "",
        "no_answer is the positive class. Threshold picked on the other 19 queries (max balanced "
        "accuracy), applied to the held-out one.",
        "",
        "| System | Score | Abstained | Precision | Recall | Recall hard | Recall easy |",
        "|---|---|---|---|---|---|---|",
    ]
    for (s, f), r in results.items():
        out.append(
            f"| {s} | {f} | {r['n_abstain']} | {_f(r['precision'])} | {_f(r['recall'])} | "  # type: ignore[arg-type]
            f"{_f(r['recall_hard'])} | {_f(r['recall_easy'])} |"  # type: ignore[arg-type]
        )
    out += ["", "## Per query, primary score (hybrid top RRF score)", ""]
    out += ["| qid | label | difficulty | hybrid top | LOO abstain | query |", "|---|---|---|---|---|---|"]
    prim = scores[PRIMARY]
    for i, q in enumerate(queries):
        pred = results[PRIMARY]["preds"][i]  # type: ignore[index]
        out.append(
            f"| {q.qid} | {q.label} | {q.difficulty or '-'} | {prim[q.qid]:.5f} | "
            f"{'abstain' if pred else 'answer'} | {q.text} |"
        )
    return "\n".join(out) + "\n"


def cmd_eval(args: argparse.Namespace) -> None:
    """Runs the abstention evaluation and writes the Markdown report."""
    queries = load_abstain_queries(args.queries)
    chunks = load_chunks(CORPUS_PATH)
    runs = retrieve_all(build_medicine_systems(chunks), queries)
    scores = collect_scores(runs, queries)
    results = {k: evaluate_feature(v, queries) for k, v in scores.items()}
    qrels = load_qrels(args.qrels)
    flips = no_answer_with_grade2(queries, qrels)
    max_grade = {q.qid: max(qrels.get(q.qid, {}).values(), default=0) for q in queries}
    predecl = Path(args.predecl).read_text(encoding="utf-8")
    text = report_markdown(queries, scores, results, predecl, flips, max_grade)
    Path(args.out).write_text(text, encoding="utf-8")
    print(text)


# ---------- CLI ----------

def cmd_pool(args: argparse.Namespace) -> None:
    """Builds the retrieval listing and the grading pool (qid, query, chunk_id, text)."""
    queries = load_abstain_queries(args.queries)
    write_query_tsv(queries, args.tsv)
    chunks = load_chunks(CORPUS_PATH)
    runs = retrieve_all(build_medicine_systems(chunks), queries)
    rows = listing_rows(runs)
    Path(args.listing).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.listing).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["system", "qid", "rank", "chunk_id", "score"],
                           lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    n = build_extra_pool(
        args.listing, args.tsv, CORPUS_PATH, LLM_QRELS_PATH,
        out_path=args.out, force=args.force, skip_graded=True,
    )
    print(f"listing rows: {len(rows)}; pool pairs written: {n} -> {args.out}")


def cmd_check(args: argparse.Namespace) -> None:
    """Prints no_answer queries that have a chunk graded >= 2 in the judged pool."""
    queries = load_abstain_queries(args.queries)
    flips = no_answer_with_grade2(queries, load_qrels(args.qrels))
    print(f"no_answer queries with a grade >= 2 chunk: {len(flips)}")
    for qid, chunk_ids in flips.items():
        print(qid, ", ".join(chunk_ids))


def main() -> None:
    """Entry point: python -m src.ir.step16_abstain {pool,check,eval}."""
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("pool")
    sp.add_argument("--queries", default=str(DRAFT_PATH))
    sp.add_argument("--tsv", default=str(TSV_PATH))
    sp.add_argument("--listing", default=str(LISTING_PATH))
    sp.add_argument("--out", default=str(POOL_PATH))
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_pool)
    sc = sub.add_parser("check")
    sc.add_argument("--queries", default=str(DRAFT_PATH))
    sc.add_argument("--qrels", default=str(LLM_QRELS_PATH))
    sc.set_defaults(func=cmd_check)
    se = sub.add_parser("eval")
    se.add_argument("--queries", default=str(DRAFT_PATH))
    se.add_argument("--qrels", default=str(LLM_QRELS_PATH))
    se.add_argument("--predecl", default="results/step16_predeclaration.md")
    se.add_argument("--out", default="results/step16_abstention.md")
    se.set_defaults(func=cmd_eval)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
