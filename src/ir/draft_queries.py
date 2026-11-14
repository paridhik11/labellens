"""Fresh candidate queries for a new test set (Step 18). Retrieves and scores nothing.

TWO GROUPS OF 30 (columns of data/eval/fresh_candidates.csv, source_group says which)
  web_faq        real public questions from FDA documents, rewritten as short search queries.
                 Every row keeps the source URL and the original question; each original was
                 checked against the source text (data/eval/fresh_web_faq.tsv).
  chunk_derived  one query per stratified random corpus chunk, written by Claude in-session as a
                 label-team member who has not read the text: a paraphrase with at most 2
                 content words copied from the source chunk. "Content word" means a token
                 (stopwords removed) that is not common domain vocabulary; common means it
                 occurs in 5% or more of all chunks (words like label, device, manufacturer).

HOW THE CHUNK SAMPLE IS STRATIFIED
  module   device 21, medicine 9 (about the 70/30 split of the existing queries)
  part     inside a module, slots follow the part sizes with at least 1 per part
  type     direct 8, field_req 8, vocab_mismatch 7, change_impact 4, symbol 3. symbol and
           change_impact need a chunk that can support them (it mentions a symbol, bar code,
           graphic ... or a change, amendment, update ...); if the random sample has too few
           such chunks, a random chunk of the same part is swapped for an eligible one and
           the worksheet says so.

FINE-TUNING LEAK GUARD
Chunks that appear as sources, and every chunk in their sections, are listed in
data/eval/finetune_exclusions.json and must be left out of any fine-tuning data. Chunks that
the web_faq queries' graded answers rely on are added there once those queries are graded.

Commands:
  python -m src.ir.draft_queries sample    writes data/eval/fresh_chunk_worksheet.tsv
  python -m src.ir.draft_queries build     validates and writes fresh_candidates.csv and the
                                           exclusion list
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.eval import load_chunks, load_query_rows
from src.ir.llm_grade_tool import allocate
from src.ir.tokenizer import tokenize

SEED = 42
MIN_WORDS = 40
GENERIC_DF = 0.05
MAX_COPIED = 2
N_MODULE = {"device": 21, "medicine": 9}
TYPE_QUOTA = {"symbol": 3, "change_impact": 4, "vocab_mismatch": 7, "field_req": 8, "direct": 8}
TYPES = frozenset(TYPE_QUOTA)
WORKSHEET = Path("data/eval/fresh_chunk_worksheet.tsv")
CHUNK_QUERIES = Path("data/eval/fresh_chunk_queries.tsv")
WEB_FAQ = Path("data/eval/fresh_web_faq.tsv")
CANDIDATES = Path("data/eval/fresh_candidates.csv")
EXCLUSIONS = Path("data/eval/finetune_exclusions.json")
SYMBOL_RE = re.compile(
    r"\b(symbols?|bar codes?|barcodes?|pictograms?|graphics?|abbreviations?|icons?|logos?|asterisk)\b", re.I)
CHANGE_RE = re.compile(r"\b(changes?|modif\w+|amend\w+|updat\w+|revis\w+|supplements?|relabel\w*|reprocess\w*)\b", re.I)


def part_of(chunk_id: str) -> str:
    """CFR part of a chunk id such as fda_21cfr801_s801.1_c1 -> '21cfr801'."""
    bits = chunk_id.split("_")
    return bits[1] if len(bits) > 1 else chunk_id


def eligible(chunk: Chunk, qtype: str) -> bool:
    """Whether a chunk can sensibly support a query of this type."""
    if qtype == "symbol":
        return bool(SYMBOL_RE.search(chunk.text))
    if qtype == "change_impact":
        return bool(CHANGE_RE.search(chunk.text))
    return True


def generic_words(chunks: list[Chunk], threshold: float = GENERIC_DF) -> set[str]:
    """Tokens that occur in at least `threshold` of all chunks (common domain vocabulary)."""
    df: Counter[str] = Counter()
    for c in chunks:
        df.update(set(tokenize(c.text)))
    cut = threshold * len(chunks)
    return {t for t, n in df.items() if n >= cut}


def copied_words(query: str, chunk_text: str, generic: set[str]) -> list[str]:
    """Content words of the query that also occur verbatim in the chunk (sorted, unique)."""
    in_chunk = set(tokenize(chunk_text))
    words = {t for t in tokenize(query) if len(t) >= 3 and not t.isdigit()}
    return sorted(t for t in words if t in in_chunk and t not in generic)


def sample_worksheet(chunks: list[Chunk], seed: int = SEED, n_module: dict[str, int] | None = None,
                     quota: dict[str, int] | None = None) -> list[dict[str, str]]:
    """Stratified random chunks with a type each (see the module docstring)."""
    n_module = n_module or N_MODULE
    quota = quota or TYPE_QUOTA
    rng = random.Random(seed)
    pool = sorted((c for c in chunks if len(c.text.split()) >= MIN_WORDS), key=lambda c: c.chunk_id)
    sampled: list[Chunk] = []
    for module in sorted(n_module):
        mpool = [c for c in pool if c.module == module]
        by_part: dict[str, list[Chunk]] = defaultdict(list)
        for c in mpool:
            by_part[part_of(c.chunk_id)].append(c)
        slots = allocate({p: len(v) for p, v in by_part.items()}, n_module[module], min_each=1)
        for part in sorted(by_part):
            cands = by_part[part][:]
            rng.shuffle(cands)
            chosen: list[Chunk] = []
            seen_sections: set[str] = set()
            for c in cands:  # prefer different sections
                if len(chosen) < slots[part] and c.section not in seen_sections:
                    chosen.append(c)
                    seen_sections.add(c.section)
            for c in cands:  # fill up if a part has too few distinct sections
                if len(chosen) < slots[part] and c not in chosen:
                    chosen.append(c)
            sampled += chosen

    notes: dict[str, str] = {}
    assigned: dict[str, str] = {}

    def unassigned() -> list[Chunk]:
        return [c for c in sampled if c.chunk_id not in assigned]

    for qtype in ("symbol", "change_impact"):
        need = quota[qtype]
        cands = [c for c in unassigned() if eligible(c, qtype)]
        rng.shuffle(cands)
        for c in cands[:need]:
            assigned[c.chunk_id] = qtype
        for _ in range(need - len(cands[:need])):
            victim = rng.choice(unassigned())
            same_part = [c for c in pool if part_of(c.chunk_id) == part_of(victim.chunk_id)
                         and c not in sampled and eligible(c, qtype)]
            same_mod = [c for c in pool if c.module == victim.module and c not in sampled
                        and eligible(c, qtype)]
            options = same_part or same_mod
            if not options:
                raise ValueError(f"no eligible {qtype} chunk left in module {victim.module}")
            new = rng.choice(options)
            sampled[sampled.index(victim)] = new
            assigned[new.chunk_id] = qtype
            notes[new.chunk_id] = f"swapped in so the sample has enough {qtype} chunks"
    rest = unassigned()
    rng.shuffle(rest)
    fill = [t for t in ("vocab_mismatch", "field_req", "direct") for _ in range(quota[t])]
    for c, t in zip(rest, fill, strict=True):
        assigned[c.chunk_id] = t

    ordered = sorted(sampled, key=lambda c: (c.module, part_of(c.chunk_id), c.chunk_id))
    return [{"qid": f"fc{i + 1:02d}", "type": assigned[c.chunk_id], "module": c.module,
             "part": part_of(c.chunk_id), "section": c.section, "source_chunk": c.chunk_id,
             "chunk_text": " ".join(c.text.split()), "note": notes.get(c.chunk_id, "")}
            for i, c in enumerate(ordered)]


def read_tsv(path: str | Path) -> list[dict[str, str]]:
    """Reads a tab-separated file with a header row."""
    with Path(path).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def build_candidates(worksheet: list[dict[str, str]], queries: dict[str, str],
                     web_rows: list[dict[str, str]], chunks: list[Chunk],
                     existing: set[str]) -> tuple[list[dict[str, str]], list[str]]:
    """Merges both groups into candidate rows and returns (rows, problems)."""
    problems: list[str] = []
    text_of = {c.chunk_id: c.text for c in chunks}
    generic = generic_words(chunks)
    rows: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for w in web_rows:
        rows.append({"qid": w["qid"], "text": w["text"], "type": w["type"], "source_chunk": "",
                     "source_group": "web_faq", "source_url": w["source_url"], "module": w["module"],
                     "part": "", "original_question": w["original_question"], "copied_words": "",
                     "verification": w["extraction"]})
    for w in worksheet:
        q = queries.get(w["qid"], "").strip()
        if not q:
            problems.append(f"{w['qid']}: no query written")
            continue
        cw = copied_words(q, text_of[w["source_chunk"]], generic)
        if len(cw) > MAX_COPIED:
            problems.append(f"{w['qid']}: copies {len(cw)} content words {cw} (max {MAX_COPIED})")
        rows.append({"qid": w["qid"], "text": q, "type": w["type"], "source_chunk": w["source_chunk"],
                     "source_group": "chunk_derived", "source_url": "", "module": w["module"],
                     "part": w["part"], "original_question": "", "copied_words": " ".join(cw),
                     "verification": ""})
    for r in rows:
        key = re.sub(r"\s+", " ", r["text"].lower()).strip()
        if r["type"] not in TYPES:
            problems.append(f"{r['qid']}: unknown type {r['type']!r}")
        if key in existing:
            problems.append(f"{r['qid']}: same text as an existing query")
        if key in seen:
            problems.append(f"{r['qid']}: duplicates {seen[key]}")
        seen[key] = r["qid"]
        if r["source_group"] == "web_faq" and not r["source_url"].startswith("https://"):
            problems.append(f"{r['qid']}: web_faq row without a source URL")
    return rows, problems


def exclusion_lists(chunks: list[Chunk], source_chunks: list[str]) -> dict:
    """Source chunks, their sections, and every chunk of those sections (fine-tuning exclusions)."""
    by_id = {c.chunk_id: c for c in chunks}
    sections = sorted({by_id[s].section for s in source_chunks if by_id[s].section})
    excluded = sorted(c.chunk_id for c in chunks if c.section in set(sections) or c.chunk_id in source_chunks)
    return {"rule": "leave these chunks out of all fine-tuning data",
            "chunk_derived_source_chunks": sorted(source_chunks),
            "chunk_derived_source_sections": sections,
            "excluded_chunk_ids": excluded,
            "web_faq_answer_chunks": "pending: add chunks graded 1 or 2 for fw queries once they are graded"}


def write_candidates(path: str | Path, rows: list[dict[str, str]]) -> None:
    """Writes fresh_candidates.csv (columns: qid, text, type, source_chunk first)."""
    cols = ["qid", "text", "type", "source_chunk", "source_group", "source_url", "module", "part",
            "original_question", "copied_words", "verification"]
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Draft fresh candidate queries (no retrieval).")
    ap.add_argument("action", choices=["sample", "build"])
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    a = ap.parse_args()
    chunks = load_chunks(a.corpus)
    if a.action == "sample":
        if WORKSHEET.exists():
            raise SystemExit(f"{WORKSHEET} exists; refusing to overwrite the sample")
        rows = sample_worksheet(chunks)
        with WORKSHEET.open("w", encoding="utf-8", newline="\n") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {WORKSHEET}: {len(rows)} chunks")
        print("module:", dict(Counter(r["module"] for r in rows)))
        print("part:", dict(sorted(Counter(r["part"] for r in rows).items())))
        print("type:", dict(Counter(r["type"] for r in rows)))
        print("notes:", [(r["qid"], r["note"]) for r in rows if r["note"]])
        return
    worksheet = read_tsv(WORKSHEET)
    queries = {r["qid"]: r["query"] for r in read_tsv(CHUNK_QUERIES)} if CHUNK_QUERIES.exists() else {}
    existing = {re.sub(r"\s+", " ", r.query.lower()).strip() for r in load_query_rows("data/eval/queries_t1.tsv")}
    rows, problems = build_candidates(worksheet, queries, read_tsv(WEB_FAQ), chunks, existing)
    if problems:
        print("PROBLEMS (nothing written):")
        print("\n".join("  " + p for p in problems))
        raise SystemExit(1)
    write_candidates(CANDIDATES, rows)
    EXCLUSIONS.write_text(json.dumps(exclusion_lists(chunks, [w["source_chunk"] for w in worksheet]),
                                     indent=1) + "\n", encoding="utf-8")
    g = Counter(r["source_group"] for r in rows)
    print(f"wrote {CANDIDATES}: {len(rows)} rows {dict(g)}")
    print("type by group:", {k: dict(Counter(r["type"] for r in rows if r["source_group"] == k)) for k in g})
    print("module by group:", {k: dict(Counter(r["module"] for r in rows if r["source_group"] == k)) for k in g})
    ex = json.loads(EXCLUSIONS.read_text(encoding="utf-8"))
    print(f"wrote {EXCLUSIONS}: {len(ex['chunk_derived_source_chunks'])} source chunks, "
          f"{len(ex['chunk_derived_source_sections'])} sections, {len(ex['excluded_chunk_ids'])} chunks excluded")


if __name__ == "__main__":
    main()
