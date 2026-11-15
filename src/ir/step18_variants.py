"""Step 18c runner: heading enrichment, bge-base and bge-large, ensembles, MedCPT bi-encoder.

Each experiment is evaluated by the Step 18 harness against plain hybrid AND hybrid+stem+prefix
(results/step18_experiments.md), with the "without q55" column. Embedding time and wall time
are logged, batches are kept small and torch uses few threads because the machine is shared.

Groups (so slow models can run in separate passes):
  enrich   E2a to E2f   heading and part number prepended for indexing
  base     E3a, E3b, E3e   bge-base alone and in an ensemble
  medcpt   E4a to E4c   MedCPT bi-encoder
  large    E3c, E3d, E3f   bge-large alone and in an ensemble

Run:  python -m src.ir.step18_variants --groups enrich,base --threads 6
"""
from __future__ import annotations

import argparse
import sys
import time

from src.ir.eval import load_chunks, load_qrels, load_query_rows
from src.ir.step17_report import ModuleContext, Spec
from src.ir.step18_cv import decide, load_folds, log_experiment, rank_with_spec
from src.ir.step18_systems import (
    PLAIN_HYBRID,
    STEM_PREFIX_HYBRID,
    Context18,
    check_baselines,
    experiments,
)

GROUPS = {
    "enrich": ["E2a", "E2b", "E2c", "E2d", "E2e", "E2f"],
    "base": ["E3a", "E3b", "E3e"],
    "medcpt": ["E4a", "E4b", "E4c"],
    "large": ["E3c", "E3d", "E3f"],
}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 18c experiments.")
    ap.add_argument("--groups", default="enrich,base,medcpt,large")
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    a = ap.parse_args()

    import os

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    import torch

    torch.set_num_threads(a.threads)
    folds = load_folds()
    in_folds = {q for f in folds["folds"] for q in f}
    rows = [r for r in load_query_rows(a.queries) if r.qid in in_folds]
    qrels = load_qrels(a.qrels)
    chunks = load_chunks("data/processed/regs.jsonl")
    texts = {c.chunk_id: c.text for c in chunks}
    ctxs = {m: Context18([c for c in chunks if c.module == m]) for m in ("device", "medicine")}

    # the baselines of this runner must be the Step 17 baselines, not look-alikes
    old = {m: ModuleContext([c for c in chunks if c.module == m], None, {}) for m in ("device", "medicine")}
    reference = {"hybrid": rank_with_spec(Spec("hybrid"), rows, old),
                 "hybrid+stem+prefix": rank_with_spec(Spec("hybrid", stem=True, prefix=True), rows, old)}
    bad = check_baselines(rows, ctxs, reference)
    if bad:
        raise SystemExit(f"Context18 baselines differ from Step 17 on {len(bad)} rankings, e.g. {bad[:3]}")
    print("[check] plain hybrid and hybrid+stem+prefix are identical to the Step 17 rankings on all "
          f"{len(rows)} queries", flush=True)

    def rank(system) -> dict[str, list[str]]:
        return {r.qid: [h.doc_id for h in ctxs[r.module].build(system).search(r.query, k=50)] for r in rows}

    bases = {"hybrid": rank(PLAIN_HYBRID), "hybrid+stem+prefix": rank(STEM_PREFIX_HYBRID)}
    wanted = [e for g in a.groups.split(",") for e in GROUPS[g]]
    by_id = {e[0]: e for e in experiments()}
    t_all = time.time()
    for exp_id in wanted:
        _, title, what, system = by_id[exp_id]
        t = time.time()
        try:
            ranked = rank(system)
        except Exception as exc:  # keep going: one failed model must not lose the others
            print(f"[error] {exp_id} {system.name}: {type(exc).__name__}: {exc}", flush=True)
            continue
        dt = time.time() - t
        params = {"system": system.name, "wall_s_to_build_and_rank": f"{dt:.0f}"}
        notes = f"Build and ranking wall time: {dt / 60:.1f} min (embeddings cached on disk afterwards)."
        res = log_experiment(exp_id, title, what, params, system.name, ranked, bases, rows, qrels, folds,
                             texts, notes)
        print(f"{exp_id} {system.name} {dt / 60:.1f} min", {b: decide(r)[0] for b, r in res.items()}, flush=True)
    print(f"[done] {(time.time() - t_all) / 60:.1f} min total", flush=True)


if __name__ == "__main__":
    main()
