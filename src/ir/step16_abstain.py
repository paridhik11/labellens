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
    cands += [(a + b) / 2 for a, b in zip(distinct, distinct[1:])]
    cands.append(distinct[-1] + 1.0)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    best: list[float] = []
    best_ba = -1.0
    for t in cands:
        tpr = sum(1 for s, y in zip(scores, labels) if y == 1 and s >= t) / n_pos
        tnr = sum(1 for s, y in zip(scores, labels) if y == 0 and s < t) / n_neg
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
    tp = sum(1 for p, y in zip(preds, labels) if p and y == 0)
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
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
