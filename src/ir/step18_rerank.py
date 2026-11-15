"""Step 18b: a stronger cross-encoder (bge-reranker-base) on top of two first stages.

Experiments E1a to E1h: first stage (plain hybrid, or hybrid+stem+prefix) x depth (30 or 50)
x mode (replace or blend). Each is reported against plain hybrid AND hybrid+stem+prefix by
the Step 18 harness (results/step18_experiments.md).

Cost control: the top 50 of each first stage is scored once and cached on disk
(data/processed/ce_cache_*.json, not tracked), so depth 30 reuses depth 50's scores, replace
and blend share one pass, and an interrupted run resumes. Batch size and torch threads are
kept modest because other jobs share this machine; wall time is logged.

Run:  python -m src.ir.step18_rerank --model BAAI/bge-reranker-base --threads 6 --batch 8
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from src.ir.eval import load_chunks, load_qrels, load_query_rows
from src.ir.rerank import CrossEncoderReranker
from src.ir.step17_report import DEPTH, ModuleContext, Spec
from src.ir.step18_cv import (
    EXPERIMENTS_MD,
    decide,
    load_folds,
    log_experiment,
    rank_with_spec,
)

SEP = "\x1f"
DEPTHS = (30, 50)
MODES = ("replace", "blend")
ALPHA = 0.5
STAGES = {"hybrid": Spec("hybrid"), "hybrid+stem+prefix": Spec("hybrid", stem=True, prefix=True)}


def load_score_cache(path: str | Path) -> dict[tuple[str, str], float]:
    """Reads a cross-encoder score cache written by save_score_cache (empty if missing)."""
    p = Path(path)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8"))["scores"]
    out = {}
    for k, v in raw.items():
        query, chunk = k.split(SEP)
        out[(query, chunk)] = v
    return out


def save_score_cache(path: str | Path, model: str, cache: dict[tuple[str, str], float]) -> None:
    """Writes the cache as JSON; keys are 'query<unit separator>chunk_id'."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps({"model": model, "scores": {f"{q}{SEP}{c}": v for (q, c), v in cache.items()}}),
                   encoding="utf-8")
    tmp.replace(p)


def variant_name(stage: str, depth: int, mode: str, tag: str = "bge-reranker-base") -> str:
    """Display name such as 'hybrid+stem+prefix+bge-reranker-base(top50,blend)'."""
    return f"{stage}+{tag}(top{depth},{mode})"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 18b: bge-reranker-base experiments.")
    ap.add_argument("--model", default="BAAI/bge-reranker-base")
    ap.add_argument("--tag", default="bge-reranker-base")
    ap.add_argument("--exp-prefix", default="E1")
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--max-length", type=int, default=512)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    a = ap.parse_args()

    os.environ.setdefault("HF_HUB_OFFLINE", "1")  # never download here
    import torch
    from sentence_transformers import CrossEncoder

    torch.set_num_threads(a.threads)
    cache_path = a.cache or f"data/processed/ce_cache_{a.tag}.json"
    cache = load_score_cache(cache_path)
    print(f"[cache] {len(cache)} scores loaded from {cache_path}", flush=True)

    folds = load_folds()
    in_folds = {q for f in folds["folds"] for q in f}
    rows = [r for r in load_query_rows(a.queries) if r.qid in in_folds]
    qrels = load_qrels(a.qrels)
    chunks = load_chunks("data/processed/regs.jsonl")
    texts = {c.chunk_id: c.text for c in chunks}
    ctxs = {m: ModuleContext([c for c in chunks if c.module == m], None, {}) for m in ("device", "medicine")}

    t0 = time.time()
    model = CrossEncoder(a.model, max_length=a.max_length)
    print(f"[model] {a.model} loaded in {time.time() - t0:.0f}s, threads={a.threads}, batch={a.batch}",
          flush=True)

    # 1. prescore the top 50 of each first stage (one pass, cached)
    pairs_scored, t_score = 0, 0.0
    t_all = time.time()
    for stage, spec in STAGES.items():
        for i, row in enumerate(rows, start=1):
            first = ctxs[row.module].build(spec)
            rr = CrossEncoderReranker(first, model=model, top_n=DEPTH, batch_size=a.batch, score_cache=cache)
            hits = first.search(row.query, k=DEPTH)
            todo = sum((row.query, h.doc_id) not in cache for h in hits)
            t = time.time()
            rr.scores(row.query, hits)
            dt = time.time() - t
            pairs_scored += todo
            t_score += dt
            if todo:
                print(f"[score] {stage} query {i}/{len(rows)} {row.qid}: {todo} new pairs in {dt:.1f}s "
                      f"({todo / dt:.2f} pairs/s; running {pairs_scored / max(t_score, 1e-9):.2f}/s, "
                      f"wall {(time.time() - t_all) / 60:.1f} min)", flush=True)
            if i % 3 == 0 and todo:
                save_score_cache(cache_path, a.model, cache)
        save_score_cache(cache_path, a.model, cache)
    wall = (time.time() - t_all) / 60
    rate = pairs_scored / max(t_score, 1e-9)
    print(f"[score] done: {pairs_scored} new pairs, {wall:.1f} min wall, {rate:.2f} pairs/s", flush=True)

    # 2. evaluate every variant against both bases
    base_ranked = {name: rank_with_spec(spec, rows, ctxs) for name, spec in STAGES.items()}
    letters = "abcdefgh"
    n = 0
    for stage, spec in STAGES.items():
        for depth in DEPTHS:
            for mode in MODES:
                exp_id = f"{a.exp_prefix}{letters[n]}"
                n += 1
                ranked = {}
                for row in rows:
                    first = ctxs[row.module].build(spec)
                    rr = CrossEncoderReranker(first, model=model, top_n=depth, mode=mode, alpha=ALPHA,
                                              batch_size=a.batch, score_cache=cache)
                    ranked[row.qid] = [h.doc_id for h in rr.search(row.query, k=DEPTH)]
                vname = variant_name(stage, depth, mode, a.tag)
                what = (f"{a.model} reorders the top {depth} of {stage}; mode {mode}"
                        + (f" (alpha {ALPHA}: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage "
                           "score)" if mode == "blend" else " (sorted by cross-encoder score alone)")
                        + f". Hits beyond depth {depth} keep their first-stage order.")
                notes = (f"Wall time of the scoring pass (shared by E1a to E1h): {wall:.1f} min for {pairs_scored} "
                         f"new pairs, {rate:.2f} pairs/s, batch {a.batch}, {a.threads} torch threads, on a machine "
                         "shared with other jobs.")
                res = log_experiment(exp_id, f"{a.tag} on {stage}, top {depth}, {mode}", what,
                                     {"model": a.model, "first_stage": stage, "depth": depth, "mode": mode,
                                      "alpha": ALPHA if mode == "blend" else "-", "max_length": a.max_length},
                                     vname, ranked, base_ranked, rows, qrels, folds, texts, notes)
                print(exp_id, vname, {b: decide(r)[0] for b, r in res.items()}, flush=True)
    print(f"[done] log: {EXPERIMENTS_MD}", flush=True)


if __name__ == "__main__":
    main()
