"""Batch tool for LLM relevance grading, kept separate from human grades.

The LLM grader follows docs/LLM_GRADER_PROMPT.md. This tool only prepares
batches, checks and stores the grades, and builds TREC qrels from them.
It never reads the human `grade` or the `section` column of the pool, and
it never writes to the pool or the human sample file after creating it.

Subcommands:
  sample      pick a stratified human-grading sample (15 queries, seed 42)
  next-batch  write the next batch of ungraded rows to a file for the grader
  record      check the grader output for that batch and append it
  to-qrels    turn data/eval/pool_t1_llm.csv into TREC qrels
  make-extra  build an extra pool (default data/eval/pool_t1_extra.csv) from any CSV with
              qid and chunk_id columns (default the Step 15 top-10 listing); --skip-graded
              leaves out pairs that already have an LLM grade, --out picks another file
  (next-batch and record take --extra to grade an extra pool, --pool picks a file other than
   pool_t1_extra.csv; the grades are appended to data/eval/pool_t1_llm.csv and batch numbers
   continue after the last recorded batch)

Row ids: a passage can appear under several queries, so every row is
identified by "<qid>:<chunk_id>", for example "q01:fda_21cfr801_s801.109_c1".

Tiny worked example (max_rows=40):
  ungraded queries in order: q03 (20 rows), q07 (15 rows), q09 (18 rows)
  batch 1 takes q03 + q07 (35 rows); adding q09 would pass 40, so it waits.
  The 35 rows are shuffled with seed "42:1", so the grader sees them in an
  order that does not follow any system's ranking.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.ir.eval import NO_ANSWER, QueryRow, load_query_rows

POOL_PATH = Path("data/eval/pool_t1.csv")
LLM_PATH = Path("data/eval/pool_t1_llm.csv")
SAMPLE_PATH = Path("data/eval/pool_t1_human_sample.csv")
QUERIES_PATH = Path("data/eval/queries_t1.tsv")
QRELS_LLM_PATH = Path("data/eval/qrels_t1_llm.tsv")
EXTRA_PATH = Path("data/eval/pool_t1_extra.csv")
CORPUS_PATH = Path("data/processed/regs.jsonl")
UNJUDGED_PATH = Path("results/step15_unjudged.csv")
EXTRA_FIELDS = ["qid", "query", "chunk_id", "text"]

LLM_FIELDS = ["qid", "chunk_id", "llm_grade", "batch", "model", "date"]
VALID_GRADES = {0, 1, 2}


@dataclass(frozen=True)
class PoolRow:
    """One pooled (query, passage) pair as shown to the LLM grader."""

    qid: str
    query: str
    chunk_id: str
    text: str

    @property
    def row_id(self) -> str:
        """Unique id of this row: '<qid>:<chunk_id>'."""
        return f"{self.qid}:{self.chunk_id}"


# ---------- loading ----------

def load_pool_rows(path: str | Path = POOL_PATH) -> list[PoolRow]:
    """Reads only qid, query, chunk_id and text from the pool CSV.

    The human `grade` and the `section` columns are never read.
    """
    with Path(path).open(encoding="utf-8", newline="") as f:
        return [
            PoolRow(r["qid"], r["query"], r["chunk_id"], r["text"])
            for r in csv.DictReader(f)
        ]


def load_llm_rows(path: str | Path = LLM_PATH) -> list[dict[str, str]]:
    """Reads the LLM grades CSV, or returns [] if it does not exist yet."""
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_sample_qids(path: str | Path = SAMPLE_PATH) -> list[str]:
    """Reads the distinct qids of the human sample (the qid column only)."""
    p = Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8", newline="") as f:
        return sorted({r["qid"] for r in csv.DictReader(f)})


# ---------- batching ----------

def query_order(pool: list[PoolRow], priority_qids: list[str]) -> list[str]:
    """Orders qids: priority (human sample) qids first, then the rest, in pool order."""
    seen: list[str] = []
    for r in pool:
        if r.qid not in seen:
            seen.append(r.qid)
    prio = [q for q in seen if q in set(priority_qids)]
    return prio + [q for q in seen if q not in set(priority_qids)]


def next_batch_number(llm_rows: list[dict[str, str]]) -> int:
    """Returns 1 + the highest batch number recorded so far."""
    return max((int(r["batch"]) for r in llm_rows), default=0) + 1


def build_next_batch(
    pool: list[PoolRow],
    graded_ids: set[str],
    priority_qids: list[str],
    batch_no: int,
    max_rows: int = 40,
    seed: int = 42,
) -> list[PoolRow]:
    """Builds the next batch of whole, fully ungraded queries, shuffled.

    Adds queries in query_order until the next one would pass max_rows.
    A batch always holds at least one query, even if it alone passes max_rows.
    Returns [] when every row is graded.
    """
    by_qid: dict[str, list[PoolRow]] = defaultdict(list)
    for r in pool:
        by_qid[r.qid].append(r)

    batch: list[PoolRow] = []
    for qid in query_order(pool, priority_qids):
        rows = by_qid[qid]
        if any(r.row_id in graded_ids for r in rows):
            continue  # whole queries are graded at once, so this one is done
        if batch and len(batch) + len(rows) > max_rows:
            break
        batch.extend(rows)

    random.Random(f"{seed}:{batch_no}").shuffle(batch)
    return batch


def format_batch(rows: list[PoolRow], batch_no: int) -> str:
    """Formats a batch for the grader: row id, query and passage text only."""
    out = [
        f"# Batch {batch_no} ({len(rows)} rows)",
        "Grade with docs/LLM_GRADER_PROMPT.md. Output one line per row: <row_id><TAB><grade>",
        "",
    ]
    for i, r in enumerate(rows, 1):
        out += [f"## Row {i}", f"row_id: {r.row_id}", f"query: {r.query}", f"passage: {r.text}", ""]
    return "\n".join(out)


def progress_line(pool: list[PoolRow], graded_ids: set[str], sample_qids: list[str]) -> str:
    """Summarises how much is graded and whether the sample queries are covered."""
    sample_rows = [r for r in pool if r.qid in set(sample_qids)]
    sample_done = {
        q for q in sample_qids
        if all(r.row_id in graded_ids for r in sample_rows if r.qid == q)
    }
    graded = sum(1 for r in pool if r.row_id in graded_ids)
    return (
        f"graded {graded}/{len(pool)} rows; "
        f"human-sample queries fully LLM-graded: {len(sample_done)}/{len(sample_qids)}"
    )


# ---------- recording ----------

def parse_grades(text: str) -> dict[str, int]:
    """Parses '<row_id><TAB><grade>' lines. Blank lines are ignored.

    Raises ValueError on a malformed line, a grade outside 0/1/2 or a
    repeated row id.
    """
    grades: dict[str, int] = {}
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        parts = line.strip().split("\t")
        if len(parts) != 2:
            raise ValueError(f"line {n}: expected '<row_id><TAB><grade>', got {line!r}")
        row_id, raw = parts[0].strip(), parts[1].strip()
        if raw not in {"0", "1", "2"}:
            raise ValueError(f"line {n}: grade must be 0, 1 or 2, got {raw!r}")
        if row_id in grades:
            raise ValueError(f"line {n}: row id {row_id} appears twice")
        grades[row_id] = int(raw)
    return grades


def check_batch_grades(batch: list[PoolRow], grades: dict[str, int]) -> None:
    """Raises ValueError unless grades cover exactly the rows of the batch."""
    expected = {r.row_id for r in batch}
    missing = sorted(expected - grades.keys())
    extra = sorted(grades.keys() - expected)
    if missing or extra:
        raise ValueError(
            f"grades do not match the batch: missing {missing[:5]} "
            f"({len(missing)} total), not in batch {extra[:5]} ({len(extra)} total)"
        )


def append_llm_rows(
    path: str | Path,
    batch: list[PoolRow],
    grades: dict[str, int],
    batch_no: int,
    model: str,
    graded_on: str,
) -> int:
    """Appends one checked batch to the LLM grades CSV. Returns rows written."""
    if not model.strip():
        raise ValueError("model id is required (as /model shows it); never guess it")
    p = Path(path)
    new_file = not p.exists()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LLM_FIELDS)
        if new_file:
            w.writeheader()
        for r in batch:
            w.writerow({
                "qid": r.qid, "chunk_id": r.chunk_id, "llm_grade": grades[r.row_id],
                "batch": batch_no, "model": model.strip(), "date": graded_on,
            })
    return len(batch)


def llm_csv_to_qrels(csv_path: str | Path, out_path: str | Path) -> int:
    """Writes TREC qrels ('qid 0 chunk_id grade') from the LLM grades CSV."""
    rows = load_llm_rows(csv_path)
    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        "".join(f"{r['qid']} 0 {r['chunk_id']} {int(r['llm_grade'])}\n" for r in rows),
        encoding="utf-8",
    )
    return len(rows)


# ---------- extra pool (Step 15) ----------

def _qid_key(qid: str) -> tuple[int, str]:
    """Sort key so q2 comes before q10: numeric part first, then the full id."""
    digits = "".join(ch for ch in qid if ch.isdigit())
    return (int(digits) if digits else 0, qid)


def build_extra_pool(
    unjudged_path: str | Path,
    queries_path: str | Path,
    corpus_path: str | Path,
    qrels_path: str | Path,
    out_path: str | Path = EXTRA_PATH,
    force: bool = False,
    skip_graded: bool = False,
) -> int:
    """Builds an extra pool CSV (qid, query, chunk_id, text) for unjudged pairs.

    Works for any CSV with qid and chunk_id columns (the Step 15 top-10 listing, the ranks
    11 to 20 listing, ...). Reads unique (qid, chunk_id) pairs (a variant column, if any,
    is dropped, so the grader never sees which system retrieved a chunk), looks up the
    query text and chunk text, and writes the rows sorted by qid then chunk_id. Raises
    ValueError if a qid or chunk is unknown, or if a pair already has an LLM grade in
    qrels_path, unless skip_graded is set: then already graded pairs are left out instead.
    Refuses to write over the main pool, the LLM grades file or the human sample, and
    refuses to replace an existing extra pool unless force is set. Returns rows written.
    """
    dest = Path(out_path)
    protected = {p.resolve() for p in (POOL_PATH, LLM_PATH, SAMPLE_PATH, QRELS_LLM_PATH)}
    if dest.resolve() in protected:
        raise ValueError(f"{dest} is a protected pool or grade file and is never written here")
    if dest.exists() and not force:
        raise FileExistsError(f"{dest} exists; use --force to replace it")

    with Path(unjudged_path).open(encoding="utf-8", newline="") as f:
        pairs = {(r["qid"], r["chunk_id"]) for r in csv.DictReader(f)}
    queries = {r.qid: r.query for r in load_query_rows(queries_path)}
    texts: dict[str, str] = {}
    for line in Path(corpus_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            texts[d["chunk_id"]] = d["text"]
    judged = {
        (parts[0], parts[2])
        for parts in (ln.split() for ln in Path(qrels_path).read_text(encoding="utf-8").splitlines())
        if len(parts) >= 4
    }
    if skip_graded:
        pairs = pairs - judged
    unknown_q = sorted({q for q, _ in pairs if q not in queries})
    unknown_c = sorted({c for _, c in pairs if c not in texts})
    already = sorted(pairs & judged)
    if unknown_q or unknown_c or already:
        raise ValueError(
            f"cannot build extra pool: unknown qids {unknown_q[:5]}, unknown chunks "
            f"{unknown_c[:5]}, already graded {already[:5]} ({len(already)} total)"
        )

    rows = sorted(pairs, key=lambda p: (_qid_key(p[0]), p[1]))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EXTRA_FIELDS, lineterminator="\n")
        w.writeheader()
        for qid, cid in rows:
            w.writerow({"qid": qid, "query": queries[qid], "chunk_id": cid, "text": texts[cid]})
    return len(rows)


def extra_progress_line(pool: list[PoolRow], graded_ids: set[str]) -> str:
    """Progress of the extra pool: rows graded so far and queries still open."""
    graded = sum(1 for r in pool if r.row_id in graded_ids)
    open_q = {r.qid for r in pool if r.row_id not in graded_ids}
    return f"extra pool: graded {graded}/{len(pool)} rows; queries still open: {len(open_q)}"


# ---------- human sample ----------

def allocate(counts: dict[str, int], n: int, min_each: int = 0) -> dict[str, int]:
    """Splits n slots across groups in proportion to counts (largest remainder).

    Each group gets the whole part of its proportional quota, raised to at
    least min_each (capped at its size). Remaining slots go to the largest
    fractional remainders. Ties are broken by group name, so the result is
    deterministic.

    Example: counts {a: 17, b: 16, c: 5}, n=8 -> quotas 3.58, 3.37, 1.05
    -> whole parts 3, 3, 1 (7 slots) -> the 8th goes to a (remainder .58).
    """
    total = sum(counts.values())
    if total == 0 or n <= 0:
        return {g: 0 for g in counts}
    if sum(min(min_each, c) for c in counts.values()) > n:
        raise ValueError(f"cannot give {min_each} to each of {len(counts)} groups with n={n}")
    quotas = {g: n * c / total for g, c in counts.items()}
    alloc = {g: min(counts[g], max(min_each, int(quotas[g]))) for g in counts}
    by_remainder = sorted(counts, key=lambda g: (-(quotas[g] - int(quotas[g])), g))
    while sum(alloc.values()) < n and any(alloc[g] < counts[g] for g in counts):
        for g in by_remainder:
            if sum(alloc.values()) >= n:
                break
            if alloc[g] < counts[g]:
                alloc[g] += 1
    return alloc


def select_sample(rows: list[QueryRow], n: int = 15, seed: int = 42) -> list[str]:
    """Picks n qids stratified by query type, then by module within each type.

    Every query type gets at least one query (so no_answer, symbol and so on
    are always present). Within a type, slots are split across modules in
    proportion, and qids are drawn with a fixed seed.
    """
    by_type: dict[str, list[QueryRow]] = defaultdict(list)
    for r in rows:
        by_type[r.qtype or "untyped"].append(r)
    type_alloc = allocate({t: len(v) for t, v in by_type.items()}, n, min_each=1)

    rng = random.Random(seed)
    chosen: list[str] = []
    for qtype in sorted(by_type):
        by_mod: dict[str, list[str]] = defaultdict(list)
        for r in by_type[qtype]:
            by_mod[r.module or "none"].append(r.qid)
        mod_alloc = allocate({m: len(v) for m, v in by_mod.items()}, type_alloc[qtype])
        for mod in sorted(by_mod):
            chosen += rng.sample(sorted(by_mod[mod]), mod_alloc[mod])
    return sorted(chosen)


def write_sample(
    pool_path: str | Path, qids: list[str], out_path: str | Path, force: bool = False
) -> int:
    """Copies the pool rows of the chosen qids into a new file with an empty grade.

    Keeps the pool's columns so the existing to-qrels and kappa commands work.
    Refuses to overwrite an existing file unless force is set, to protect
    human grades already entered there.
    """
    dest = Path(out_path)
    if dest.exists() and not force:
        raise FileExistsError(f"{dest} exists and may hold human grades; use --force to replace it")
    keep = set(qids)
    with Path(pool_path).open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = [{**r, "grade": ""} for r in reader if r["qid"] in keep]
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def split_between_annotators(
    rows: list[QueryRow],
    row_counts: dict[str, int],
    names: tuple[str, str] = ("pari", "parth"),
    seed: int = 42,
) -> tuple[list[str], dict[str, list[str]]]:
    """Splits sample queries between two annotators with a shared overlap.

    Overlap (graded by both, for inter-annotator kappa): every no_answer
    query, plus one seeded device query and one seeded medicine query
    (when that module exists among the answerable queries).
    The other queries are dealt type by type: within each type the qids are
    shuffled with the seed, and each goes to the annotator with fewer queries
    so far (ties: fewer rows, then the first name). Both annotators get a
    similar mix of types and a similar number of rows.

    Returns (overlap_qids, {name: all qids that annotator grades}).
    """
    rng = random.Random(seed)
    rows = sorted(rows, key=lambda r: r.qid)
    overlap = [r.qid for r in rows if r.qtype == NO_ANSWER]
    answerable = [r for r in rows if r.qtype != NO_ANSWER]
    for module in ("device", "medicine"):
        pool = [r.qid for r in answerable if r.module == module]
        if pool:
            overlap.append(rng.choice(pool))

    own: dict[str, list[str]] = {n: [] for n in names}
    by_type: dict[str, list[str]] = defaultdict(list)
    for r in answerable:
        if r.qid not in overlap:
            by_type[r.qtype].append(r.qid)
    for qtype in sorted(by_type):
        qids = by_type[qtype]
        rng.shuffle(qids)
        for qid in qids:
            name = min(
                names,
                key=lambda n: (len(own[n]), sum(row_counts.get(q, 0) for q in own[n]), names.index(n)),
            )
            own[name].append(qid)

    overlap = sorted(overlap)
    return overlap, {n: sorted(overlap + own[n]) for n in names}


# ---------- CLI ----------

def _current_batch(
    args: argparse.Namespace,
) -> tuple[list[PoolRow], list[PoolRow], set[str], list[str], int]:
    """Loads the pool and grades and builds the next batch.

    With --extra the pool is data/eval/pool_t1_extra.csv (unless --pool is given), no
    human sample is needed, and the batch number continues after the last recorded batch
    in the LLM grades file, so numbering carries on after batch 43.
    """
    extra = getattr(args, "extra", False)
    pool = load_pool_rows(args.pool or (EXTRA_PATH if extra else POOL_PATH))
    llm_rows = load_llm_rows(args.llm)
    graded = {f"{r['qid']}:{r['chunk_id']}" for r in llm_rows}
    sample_qids = [] if extra else load_sample_qids(args.sample)
    if not extra and not sample_qids:
        raise SystemExit(f"No human sample at {args.sample}. Run the 'sample' subcommand first.")
    batch_no = next_batch_number(llm_rows)
    batch = build_next_batch(pool, graded, sample_qids, batch_no, args.max_rows, args.seed)
    return pool, batch, graded, sample_qids, batch_no


def _progress(
    args: argparse.Namespace, pool: list[PoolRow], graded: set[str], sample: list[str]
) -> str:
    """Progress line for the main pool, or for the extra pool with --extra."""
    if getattr(args, "extra", False):
        return extra_progress_line(pool, graded)
    return progress_line(pool, graded, sample)


def main() -> None:
    """Command-line entry point."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser(description="LLM relevance grading tool (separate from human grades).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def batch_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--pool", default=None, help="Pool CSV (default: pool_t1.csv)")
        p.add_argument("--extra", action="store_true",
                       help="Grade data/eval/pool_t1_extra.csv; grades go to the same LLM file")
        p.add_argument("--llm", default=str(LLM_PATH))
        p.add_argument("--sample", default=str(SAMPLE_PATH))
        p.add_argument("--max-rows", type=int, default=40)
        p.add_argument("--seed", type=int, default=42)

    p_s = sub.add_parser("sample", help="Write the stratified human-grading sample.")
    p_s.add_argument("--queries", default=str(QUERIES_PATH))
    p_s.add_argument("--pool", default=str(POOL_PATH))
    p_s.add_argument("--out", default=str(SAMPLE_PATH))
    p_s.add_argument("--n", type=int, default=15)
    p_s.add_argument("--seed", type=int, default=42)
    p_s.add_argument("--force", action="store_true", help="Replace an existing sample file")

    p_sp = sub.add_parser("split", help="Split the human sample between two annotators.")
    p_sp.add_argument("--queries", default=str(QUERIES_PATH))
    p_sp.add_argument("--sample", default=str(SAMPLE_PATH))
    p_sp.add_argument("--names", nargs=2, default=["pari", "parth"])
    p_sp.add_argument("--out-dir", default="data/eval")
    p_sp.add_argument("--seed", type=int, default=42)

    p_n = sub.add_parser("next-batch", help="Write the next ungraded batch for the grader.")
    batch_args(p_n)
    p_n.add_argument("--out", required=True, help="File to write the batch text to")

    p_r = sub.add_parser("record", help="Check grader output for the next batch and append it.")
    batch_args(p_r)
    p_r.add_argument("--grades", required=True, help="File with '<row_id><TAB><grade>' lines")
    p_r.add_argument("--model", required=True, help="Model id exactly as /model shows it")
    p_r.add_argument("--date", default=date.today().isoformat())

    p_x = sub.add_parser("make-extra", help="Build pool_t1_extra.csv from the Step 15 listing.")
    p_x.add_argument("--unjudged", default=str(UNJUDGED_PATH))
    p_x.add_argument("--queries", default=str(QUERIES_PATH))
    p_x.add_argument("--corpus", default=str(CORPUS_PATH))
    p_x.add_argument("--qrels", default=str(QRELS_LLM_PATH))
    p_x.add_argument("--out", default=str(EXTRA_PATH))
    p_x.add_argument("--force", action="store_true", help="Replace an existing extra pool")
    p_x.add_argument("--skip-graded", action="store_true",
                     help="Leave out pairs that already have an LLM grade instead of refusing")

    p_q = sub.add_parser("to-qrels", help="Build TREC qrels from the LLM grades CSV.")
    p_q.add_argument("--llm", default=str(LLM_PATH))
    p_q.add_argument("--out", default=str(QRELS_LLM_PATH))

    a = ap.parse_args()

    if a.cmd == "sample":
        rows = load_query_rows(a.queries)
        qids = select_sample(rows, a.n, a.seed)
        n_rows = write_sample(a.pool, qids, a.out, a.force)
        info = {r.qid: r for r in rows}
        print(f"Wrote {n_rows} rows for {len(qids)} queries to {a.out}")
        print("by type:", dict(sorted(Counter(info[q].qtype for q in qids).items())))
        print("by module:", dict(sorted(Counter(info[q].module for q in qids).items())))
        print("no_answer included:", any(info[q].qtype == NO_ANSWER for q in qids))
        print("qids:", ", ".join(qids))
    elif a.cmd == "split":
        sample_qids = set(load_sample_qids(a.sample))
        rows = [r for r in load_query_rows(a.queries) if r.qid in sample_qids]
        with Path(a.sample).open(encoding="utf-8", newline="") as f:
            row_counts = Counter(r["qid"] for r in csv.DictReader(f))
        names = (a.names[0], a.names[1])
        outs = {n: Path(a.out_dir) / f"sample_{n}.csv" for n in names}
        existing = [str(p) for p in outs.values() if p.exists()]
        if existing:
            raise SystemExit(f"Refusing to overwrite (may hold human grades): {', '.join(existing)}")
        overlap, assigned = split_between_annotators(rows, row_counts, names, a.seed)
        info = {r.qid: r for r in rows}
        print("overlap (graded by both):", ", ".join(overlap))
        for n in names:
            n_rows = write_sample(a.sample, assigned[n], outs[n])
            types = dict(sorted(Counter(info[q].qtype for q in assigned[n]).items()))
            mods = dict(sorted(Counter(info[q].module for q in assigned[n]).items()))
            print(f"{n}: {len(assigned[n])} queries, {n_rows} rows -> {outs[n]}")
            print(f"  qids: {', '.join(assigned[n])}")
            print(f"  by type: {types}")
            print(f"  by module: {mods}")
    elif a.cmd == "next-batch":
        pool, batch, graded, sample_qids, batch_no = _current_batch(a)
        print(_progress(a, pool, graded, sample_qids))
        if not batch:
            print("Nothing left to grade.")
            return
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(format_batch(batch, batch_no), encoding="utf-8")
        qids = sorted({r.qid for r in batch})
        print(f"Batch {batch_no}: {len(batch)} rows, queries {', '.join(qids)} -> {a.out}")
    elif a.cmd == "record":
        pool, batch, graded, sample_qids, batch_no = _current_batch(a)
        if not batch:
            raise SystemExit("Nothing left to grade.")
        grades = parse_grades(Path(a.grades).read_text(encoding="utf-8"))
        check_batch_grades(batch, grades)
        n = append_llm_rows(a.llm, batch, grades, batch_no, a.model, a.date)
        graded |= {r.row_id for r in batch}
        print(f"Recorded batch {batch_no}: {n} rows -> {a.llm}")
        print("grade counts:", dict(sorted(Counter(grades.values()).items())))
        print(_progress(a, pool, graded, sample_qids))
    elif a.cmd == "make-extra":
        with Path(a.unjudged).open(encoding="utf-8", newline="") as f:
            n_listed = len({(r["qid"], r["chunk_id"]) for r in csv.DictReader(f)})
        n = build_extra_pool(a.unjudged, a.queries, a.corpus, a.qrels, a.out, a.force, a.skip_graded)
        with Path(a.out).open(encoding="utf-8", newline="") as f:
            qids = sorted({r["qid"] for r in csv.DictReader(f)}, key=_qid_key)
        print(f"Unique pairs in {a.unjudged}: {n_listed}; left out as already graded: {n_listed - n}")
        print(f"Wrote {n} rows for {len(qids)} queries to {a.out}")
        print("qids:", ", ".join(qids))
    elif a.cmd == "to-qrels":
        n = llm_csv_to_qrels(a.llm, a.out)
        print(f"Wrote {n} LLM qrels rows to {a.out}")


if __name__ == "__main__":
    main()
