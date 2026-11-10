"""Pooling, TREC qrels export, and inter-annotator agreement tooling.

POOLING EXPLANATION
Judging every chunk in a corpus for every query does not scale (for 10 queries
over 903 chunks, exhaustive judging would require 9,030 manual decisions).
Instead, pooling collects only the top k results from a diverse set of systems
(TF-IDF, BM25, Dense, Hybrid), merges them into one deduplicated candidate set
per query, and shuffles the order to hide system identity during grading.

Tiny worked example (k=2 per system):
  BM25 top-2:   [c_10, c_22]
  Dense top-2:  [c_22, c_05]
  Pooled unique set: {c_05, c_10, c_22}  -> shuffled order: [c_22, c_05, c_10]
  The annotator judges 3 chunks instead of the full corpus, and never sees
  whether BM25, Dense, or both retrieved each candidate.

Usage:
  python -m src.ir.qrels_tool pool --queries data/eval/queries_t1.tsv --out data/eval/pool_t1.csv
  python -m src.ir.qrels_tool to-qrels --csv data/eval/pool_t1.csv --out data/eval/qrels_t1.tsv
  python -m src.ir.qrels_tool kappa annotator1.csv annotator2.csv
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.eval import QueryRow, build_systems, load_chunks, load_query_rows

VALID_GRADES = {0, 1, 2}
POOL_COLUMNS = ["qid", "query", "chunk_id", "section", "text", "grade"]


@dataclass(frozen=True)
class KappaResult:
    """Summary statistics from Cohen's kappa agreement computation."""

    n_overlap: int
    n_agree: int
    po: float
    pe: float
    kappa: float


def _build_module_pools(
    chunks: list[Chunk],
    needed_modules: set[str],
    with_dense: bool = True,
    cache_dir: Path | None = None,
    model: object | None = None,
) -> dict[str, tuple[list[Retriever], dict[str, Chunk]]]:
    """Builds retrieval systems separately per module before any ranking occurs."""
    module_systems: dict[str, tuple[list[Retriever], dict[str, Chunk]]] = {}
    shared_model = model

    for mod in sorted(needed_modules):
        if mod in ("device", "medicine"):
            mod_chunks = [c for c in chunks if c.module == mod]
        else:
            mod_chunks = list(chunks)

        if not mod_chunks:
            raise ValueError(f"No corpus chunks found for module '{mod}'.")

        docs = [(c.chunk_id, c.text) for c in mod_chunks]
        chunk_map = {c.chunk_id: c for c in mod_chunks}
        systems = build_systems(
            docs,
            with_dense=with_dense,
            chunks=mod_chunks,
            cache_dir=cache_dir,
            model=shared_model,
        )
        # Reuse the loaded SentenceTransformer instance across modules if present.
        if with_dense and shared_model is None:
            for sys_obj in systems:
                if getattr(sys_obj, "name", "") == "dense":
                    # Trigger lazy load on first module only if a query uses it later,
                    # or share whatever model was constructed during encoding.
                    shared_model = getattr(sys_obj, "_model", None)
        module_systems[mod] = (systems, chunk_map)

    return module_systems


def build_pool_rows(
    corpus_chunks: list[Chunk],
    query_rows: list[QueryRow],
    top_k: int = 10,
    seed: int = 42,
    with_dense: bool = True,
    cache_dir: Path | None = None,
    model: object | None = None,
) -> tuple[list[dict[str, str]], dict[str, int]]:
    """Pools top-k hits across all systems per query, deduplicates, and shuffles."""
    needed_modules = {
        (q.module if q.module in ("device", "medicine") else "all")
        for q in query_rows
    }
    module_pools = _build_module_pools(
        corpus_chunks,
        needed_modules=needed_modules,
        with_dense=with_dense,
        cache_dir=cache_dir,
        model=model,
    )

    # Share the dense model after its first lazy query encode to avoid double loading.
    loaded_model = model
    pooled_rows: list[dict[str, str]] = []
    per_query_counts: dict[str, int] = {}

    for qrow in query_rows:
        mod_key = qrow.module if qrow.module in ("device", "medicine") else "all"
        systems, chunk_map = module_pools[mod_key]

        if with_dense and loaded_model is not None:
            for sys_obj in systems:
                if getattr(sys_obj, "name", "") == "dense" and getattr(sys_obj, "_model", None) is None:
                    sys_obj._model = loaded_model  # type: ignore[attr-defined]

        candidate_ids: set[str] = set()
        for sys_obj in systems:
            hits = sys_obj.search(qrow.query, k=top_k)
            for hit in hits:
                if hit.doc_id in chunk_map:
                    candidate_ids.add(hit.doc_id)

        if with_dense and loaded_model is None:
            for sys_obj in systems:
                if getattr(sys_obj, "name", "") == "dense":
                    loaded_model = getattr(sys_obj, "_model", None)

        ordered_ids = sorted(candidate_ids)
        rng = random.Random(f"{seed}:{qrow.qid}")
        rng.shuffle(ordered_ids)

        per_query_counts[qrow.qid] = len(ordered_ids)
        for cid in ordered_ids:
            chunk = chunk_map[cid]
            clean_text = " ".join(chunk.text.split())
            pooled_rows.append(
                {
                    "qid": qrow.qid,
                    "query": qrow.query,
                    "chunk_id": cid,
                    "section": chunk.section,
                    "text": clean_text,
                    "grade": "",
                }
            )

    return pooled_rows, per_query_counts


def write_pool_csv(rows: list[dict[str, str]], out_path: str | Path) -> Path:
    """Writes pooled annotation rows to a UTF-8 CSV with an empty grade column."""
    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=POOL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return dest


def _parse_grade(raw: str, row_desc: str) -> int:
    """Parses and validates a relevance grade in {0, 1, 2}."""
    try:
        val = int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid non-integer grade '{raw}' at {row_desc}.") from exc
    if val not in VALID_GRADES:
        raise ValueError(
            f"Grade {val} out of valid range {sorted(VALID_GRADES)} at {row_desc}."
        )
    return val


def csv_to_qrels(
    csv_path: str | Path,
    out_path: str | Path,
    strict: bool = False,
) -> tuple[int, int]:
    """Converts a graded annotation CSV to TREC qrels format (qid 0 chunk_id grade).

    Blank grades are skipped unless strict=True. Returns (written_count, skipped_blank).
    """
    src = Path(csv_path)
    qrel_lines: list[str] = []
    skipped_blank = 0

    with src.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not {"qid", "chunk_id", "grade"}.issubset(
            reader.fieldnames
        ):
            raise ValueError(
                f"CSV {src} must contain columns qid, chunk_id, grade; found {reader.fieldnames}."
            )
        for line_num, row in enumerate(reader, start=2):
            qid = (row.get("qid") or "").strip()
            cid = (row.get("chunk_id") or "").strip()
            grade_str = (row.get("grade") or "").strip()
            if not grade_str:
                if strict:
                    raise ValueError(f"Missing grade at row {line_num} ({qid}, {cid}).")
                skipped_blank += 1
                continue
            grade = _parse_grade(grade_str, f"row {line_num} ({qid}, {cid})")
            qrel_lines.append(f"{qid} 0 {cid} {grade}")

    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(qrel_lines) + ("\n" if qrel_lines else "")
    dest.write_text(content, encoding="utf-8")
    return len(qrel_lines), skipped_blank


def _load_graded_map(csv_path: str | Path) -> dict[tuple[str, str], int]:
    """Loads non-empty validated grades keyed by (qid, chunk_id) from a CSV."""
    src = Path(csv_path)
    grades: dict[tuple[str, str], int] = {}
    with src.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not {"qid", "chunk_id", "grade"}.issubset(
            reader.fieldnames
        ):
            raise ValueError(
                f"CSV {src} must contain columns qid, chunk_id, grade; found {reader.fieldnames}."
            )
        for line_num, row in enumerate(reader, start=2):
            grade_str = (row.get("grade") or "").strip()
            if not grade_str:
                continue
            qid = (row.get("qid") or "").strip()
            cid = (row.get("chunk_id") or "").strip()
            grades[(qid, cid)] = _parse_grade(grade_str, f"{src} row {line_num}")
    return grades


def compute_cohens_kappa(csv_a: str | Path, csv_b: str | Path) -> KappaResult:
    """Computes Cohen's kappa between two annotated CSVs on overlapping graded rows."""
    grades_a = _load_graded_map(csv_a)
    grades_b = _load_graded_map(csv_b)
    overlap = sorted(set(grades_a) & set(grades_b))
    if not overlap:
        raise ValueError("No overlapping graded (qid, chunk_id) rows found between CSVs.")

    n = len(overlap)
    labels_a = [grades_a[k] for k in overlap]
    labels_b = [grades_b[k] for k in overlap]
    n_agree = sum(1 for a, b in zip(labels_a, labels_b, strict=True) if a == b)
    po = n_agree / n

    counts_a = Counter(labels_a)
    counts_b = Counter(labels_b)
    categories = sorted(set(counts_a) | set(counts_b))
    pe = sum((counts_a[c] / n) * (counts_b[c] / n) for c in categories)

    if abs(1.0 - pe) < 1e-12:
        kappa = 1.0 if abs(po - 1.0) < 1e-12 else 0.0
    else:
        kappa = (po - pe) / (1.0 - pe)

    return KappaResult(n_overlap=n, n_agree=n_agree, po=po, pe=pe, kappa=kappa)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Pooling, TREC qrels export, and Cohen's kappa agreement tools."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pool = sub.add_parser("pool", help="Pool top-k chunks across all systems into a CSV.")
    p_pool.add_argument("--corpus", default="data/processed/regs.jsonl")
    p_pool.add_argument("--queries", default="data/eval/queries_t1.tsv")
    p_pool.add_argument("--out", default="data/eval/pool_t1.csv")
    p_pool.add_argument("--k", type=int, default=10, help="Top-k per system (default: 10)")
    p_pool.add_argument("--seed", type=int, default=42, help="Shuffle seed (default: 42)")
    p_pool.add_argument("--no-dense", action="store_true", help="Pool only tfidf and bm25")

    p_qrels = sub.add_parser("to-qrels", help="Convert an annotated CSV into TREC qrels.")
    p_qrels.add_argument("--csv", required=True, help="Annotated pool CSV path")
    p_qrels.add_argument("--out", default="data/eval/qrels_t1.tsv", help="Output TREC qrels TSV")
    p_qrels.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any row has an empty grade column",
    )

    p_kappa = sub.add_parser("kappa", help="Compute Cohen's kappa between two annotated CSVs.")
    p_kappa.add_argument("csv_a", help="First annotator CSV")
    p_kappa.add_argument("csv_b", help="Second annotator CSV")

    args = parser.parse_args()

    if args.command == "pool":
        chunks = load_chunks(args.corpus)
        query_rows = load_query_rows(args.queries)
        rows, counts = build_pool_rows(
            chunks,
            query_rows,
            top_k=args.k,
            seed=args.seed,
            with_dense=not args.no_dense,
        )
        dest = write_pool_csv(rows, args.out)
        print(f"Pooled {len(rows)} rows across {len(query_rows)} queries -> {dest}")
        for qid, cnt in counts.items():
            print(f"  {qid}: {cnt} unique candidates")
    elif args.command == "to-qrels":
        written, skipped = csv_to_qrels(args.csv, args.out, strict=args.strict)
        print(f"Wrote {written} qrels rows to {args.out} (skipped {skipped} blank rows).")
    elif args.command == "kappa":
        res = compute_cohens_kappa(args.csv_a, args.csv_b)
        print(
            f"Overlapping graded rows: {res.n_overlap} | "
            f"Agreed: {res.n_agree} | po={res.po:.4f} | pe={res.pe:.4f} | "
            f"Cohen's kappa={res.kappa:.4f}"
        )


if __name__ == "__main__":
    main()

