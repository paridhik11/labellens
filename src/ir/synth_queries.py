"""Synthetic in-domain training queries for fine-tuning the reranker (Step 18d). Scores nothing.

About 150 queries, written in-session by Claude (no API, no small local model) from corpus chunks
only, never from evaluation queries. Rules:
  - the source chunks exclude everything in data/eval/finetune_exclusions.json (the fresh-set
    source chunks and every chunk of their sections), so the fresh set stays an honest test;
  - the query is a paraphrase written as a label-team member who has not read the text: at most 2
    rare content words copied from the source chunk (words in 5% or more of chunks are common),
    at most 4 copied content words counting common ones, Jaccard with the chunk at most 0.15;
  - no query repeats an existing evaluation query, a fresh candidate, or another synthetic one;
  - sampling is stratified by module (device 105, medicine 45), part (at least 1 per part) and
    type (direct 40, field_req 40, vocab_mismatch 35, change_impact 20, symbol 15).
The only known positive of a query is its source chunk; its hard negatives are chosen later from
bm25 and dense results (see src/ir/step18_finetune.py).

Commands:
  python -m src.ir.synth_queries sample   writes data/eval/synth_worksheet.tsv
  python -m src.ir.synth_queries build    validates data/eval/synth_queries.tsv and writes
                                          data/eval/synth_train_queries.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.draft_queries import (
    MAX_COPIED,
    OVERLAP_MAX_COPIED,
    OVERLAP_MAX_JACCARD,
    TYPES,
    copied_words,
    generic_words,
    overlap_stats,
    read_tsv,
    sample_worksheet,
)
from src.ir.eval import load_chunks, load_query_rows

SEED = 42
N_MODULE = {"device": 105, "medicine": 45}
TYPE_QUOTA = {"direct": 40, "field_req": 40, "vocab_mismatch": 35, "change_impact": 20, "symbol": 15}
WORKSHEET = Path("data/eval/synth_worksheet.tsv")
QUERIES = Path("data/eval/synth_queries.tsv")
TRAIN_CSV = Path("data/eval/synth_train_queries.csv")
EXCLUSIONS = Path("data/eval/finetune_exclusions.json")


def eligible_pool(chunks: list[Chunk], excluded: set[str]) -> list[Chunk]:
    """Chunks that may be used as synthetic-query sources (everything not excluded)."""
    return [c for c in chunks if c.chunk_id not in excluded]


def make_worksheet(chunks: list[Chunk], excluded: set[str], seed: int = SEED, n_module: dict[str, int] | None = None,
                   quota: dict[str, int] | None = None) -> list[dict[str, str]]:
    """Stratified sample from the eligible chunks; qids are sq001, sq002, ..."""
    rows = sample_worksheet(eligible_pool(chunks, excluded), seed, n_module or N_MODULE, quota or TYPE_QUOTA)
    for i, r in enumerate(rows):
        r["qid"] = f"sq{i + 1:03d}"
    return rows


def validate(worksheet: list[dict[str, str]], queries: dict[str, str], chunks: list[Chunk], excluded: set[str],
             forbidden: set[str]) -> tuple[list[dict[str, str]], list[str]]:
    """Checks every written query and returns (training rows, problems)."""
    text_of = {c.chunk_id: c.text for c in chunks}
    generic = generic_words(chunks)
    problems: list[str] = []
    rows: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for w in worksheet:
        qid, src = w["qid"], w["source_chunk"]
        q = queries.get(qid, "").strip()
        if not q:
            problems.append(f"{qid}: no query written")
            continue
        if src in excluded:
            problems.append(f"{qid}: source chunk {src} is in the fine-tuning exclusion list")
        cw = copied_words(q, text_of[src], generic)
        ov = overlap_stats(q, text_of[src])
        if len(cw) > MAX_COPIED:
            problems.append(f"{qid}: copies rare content words {cw} (max {MAX_COPIED})")
        if ov["copied_all_count"] > OVERLAP_MAX_COPIED:
            problems.append(f"{qid}: copies {ov['copied_all_count']} content words incl. common "
                            f"(max {OVERLAP_MAX_COPIED})")
        if ov["jaccard"] > OVERLAP_MAX_JACCARD:
            problems.append(f"{qid}: Jaccard {ov['jaccard']:.3f} (max {OVERLAP_MAX_JACCARD})")
        key = re.sub(r"\s+", " ", q.lower()).strip()
        if key in forbidden:
            problems.append(f"{qid}: same text as an evaluation or fresh query")
        if key in seen:
            problems.append(f"{qid}: duplicates {seen[key]}")
        seen[key] = qid
        if w["type"] not in TYPES:
            problems.append(f"{qid}: unknown type {w['type']!r}")
        rows.append({"qid": qid, "query": q, "type": w["type"], "module": w["module"], "source_chunk": src,
                     "source_section": w["section"], "part": w["part"], "copied_rare": " ".join(cw),
                     "copied_all_count": str(ov["copied_all_count"]), "jaccard": f"{ov['jaccard']:.3f}"})
    return rows, problems


def load_excluded(path: str | Path = EXCLUSIONS) -> set[str]:
    """The chunk ids that must stay out of all fine-tuning data."""
    return set(json.loads(Path(path).read_text(encoding="utf-8"))["excluded_chunk_ids"])


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Synthetic training queries (no retrieval, no scoring).")
    ap.add_argument("action", choices=["sample", "build"])
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    a = ap.parse_args()
    chunks = load_chunks(a.corpus)
    excluded = load_excluded()
    if a.action == "sample":
        if WORKSHEET.exists():
            raise SystemExit(f"{WORKSHEET} exists; refusing to overwrite the sample")
        rows = make_worksheet(chunks, excluded)
        with WORKSHEET.open("w", encoding="utf-8", newline="\n") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {WORKSHEET}: {len(rows)} chunks; {len(excluded)} excluded chunks were not eligible")
        print("module:", dict(Counter(r["module"] for r in rows)))
        print("part:", dict(sorted(Counter(r["part"] for r in rows).items())))
        print("type:", dict(Counter(r["type"] for r in rows)))
        return
    worksheet = read_tsv(WORKSHEET)
    queries = {r["qid"]: r["query"] for r in read_tsv(QUERIES)} if QUERIES.exists() else {}
    norm = lambda t: re.sub(r"\s+", " ", t.lower()).strip()  # noqa: E731
    forbidden = {norm(r.query) for r in load_query_rows("data/eval/queries_t1.tsv")}
    forbidden |= {norm(r["text"]) for r in read_tsv_csv("data/eval/fresh_candidates.csv")}
    forbidden |= {norm(r["query"]) for r in read_tsv("data/eval/queries_t1_abstain.tsv")}
    rows, problems = validate(worksheet, queries, chunks, excluded, forbidden)
    if problems:
        print(f"PROBLEMS ({len(problems)}), nothing written:")
        print("\n".join("  " + p for p in problems))
        raise SystemExit(1)
    with TRAIN_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {TRAIN_CSV}: {len(rows)} queries")
    print("copied rare words per query:", dict(sorted(Counter(len(r["copied_rare"].split()) for r in rows).items())))
    print("copied incl. common:", dict(sorted(Counter(int(r["copied_all_count"]) for r in rows).items())))


def read_tsv_csv(path: str) -> list[dict[str, str]]:
    """Reads a comma-separated file with a header row."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    main()
