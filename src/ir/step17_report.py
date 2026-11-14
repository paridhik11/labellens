"""Step 17e: tune the three retrieval tweaks on the DEVELOPMENT half only.

Reads qrels but never writes them. The held-out half is not touched here.

WHAT IS COMPARED
Every variant is a small spec: a base (bm25 or hybrid), optionally query expansion,
optionally the part boost, optionally the cross-encoder rerank. Each variant is run
on the dev queries, each query against its own module's chunks (device and medicine
stay separate), to depth 50.

TWO nDCG@10 NUMBERS (the qrels are pooled from the OLD systems, so a variant that
surfaces chunks nobody graded is judged on incomplete data)
  unjudged=0  chunks not in the qrels count as grade 0 (the standard way).
  condensed   chunks not in the qrels are removed from the list first, so the next
              judged chunk moves up. Optimistic for a variant that retrieves
              many unjudged chunks, pessimistic when it hides relevant ones;
              read the two together with the unjudged@10 share.

GAIN RULE (fixed before running)
A family "gains" on a base when its best configuration beats that base by more than
0.01 nDCG@10 on BOTH numbers, pooled over dev. Only then is it combined with others,
and the alternative part scoring (summed RRF of a part's top 3 chunks) is tried
only for a base where the BM25 part scoring showed no gain.

Run:
  python -m src.ir.step17_report --qrels data/eval/qrels_t1_llm.tsv \
      --out results/step17_dev.md --unjudged results/step17_unjudged.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex
from src.ir.eval import load_chunks, load_qrels, load_query_rows
from src.ir.expand import AppendExpansionRetriever, ExpandedBM25Retriever, SynonymExpander
from src.ir.metrics import ndcg_at_k
from src.ir.partboost import PartBoostRetriever, build_part_index
from src.ir.rerank import DEFAULT_MODEL, CrossEncoderReranker
from src.ir.split import load_split
from src.ir.step14_report import paired_bootstrap_ci

DEPTH = 50
GAIN_MIN = 0.01
WEIGHTS = (0.3, 0.5, 1.0)
BETAS = (0.1, 0.25, 0.5, 1.0)
TOPS = (1, 2)
LABEL = "LLM-assessed qrels (claude-sonnet-5-5), not human grades"


# ---------------------------------------------------------------- variants

@dataclass(frozen=True)
class Spec:
    """One retrieval variant. Fields left None switch that stage off."""

    base: str  # 'bm25' or 'hybrid'
    exp: tuple[float, str, bool] | None = None  # (weight, 'all' | 'cfr', also dense query)
    pb: tuple[int, float, str] | None = None  # (top_parts, beta, 'bm25' | 'rrf_top3')
    rr: str | None = None  # 'replace' | 'rrf' (hybrid base only)

    @property
    def name(self) -> str:
        parts = [self.base]
        if self.exp:
            w, src, both = self.exp
            side = "" if self.base == "bm25" else (",dense" if both else ",bm25side")
            parts.append(f"exp(w={w},{src}{side})")
        if self.pb:
            t, b, sc = self.pb
            parts.append(f"pb(top={t},beta={b},{'bm25' if sc == 'bm25' else 'votes'})")
        if self.rr:
            parts.append(f"rr({self.rr})")
        return "+".join(parts)

    @property
    def family(self) -> str:
        stages = [s for s, on in (("exp", self.exp), ("pb", self.pb), ("rr", self.rr)) if on]
        if not stages:
            return "baseline"
        return stages[0] if len(stages) == 1 else "combo"


class ModuleContext:
    """Everything one module needs to build any variant (indexes, dense, caches)."""

    def __init__(self, chunks: list[Chunk], ce_model: object | None, ce_cache: dict) -> None:
        from src.ir.dense import DenseRetriever
        from src.ir.hybrid import HybridRetriever

        self.docs = [(c.chunk_id, c.text) for c in chunks]
        self.ix = InvertedIndex().build(self.docs)
        self.bm25 = BM25Retriever(self.ix)
        self.dense = DenseRetriever.from_chunks(chunks)
        self.hybrid = HybridRetriever(bm25=self.bm25, dense=self.dense)
        self.part_index = build_part_index(self.docs)
        self.ce_model = ce_model
        self.ce_cache = ce_cache
        self._built: dict[Spec, Retriever] = {}

    def build(self, spec: Spec) -> Retriever:
        """Builds (once) the retriever for a spec."""
        if spec in self._built:
            return self._built[spec]
        from src.ir.hybrid import HybridRetriever

        if spec.exp:
            w, src, both = spec.exp
            expander = SynonymExpander.from_file(sources=None if src == "all" else {"cfr_definition"})
            lex = ExpandedBM25Retriever(self.ix, expander, weight=w)
            if spec.base == "bm25":
                r: Retriever = lex
            else:
                dense = AppendExpansionRetriever(self.dense, expander, "dense_exp") if both else self.dense
                r = HybridRetriever(bm25=lex, dense=dense)
        else:
            r = self.bm25 if spec.base == "bm25" else self.hybrid
        if spec.pb:
            t, b, sc = spec.pb
            r = PartBoostRetriever(r, self.part_index, top_parts=t, beta=b, fetch_k=DEPTH,
                                   part_scoring=sc)
        if spec.rr:
            assert spec.base == "hybrid", "the reranker is only run on a hybrid base"
            r = CrossEncoderReranker(r, model=self.ce_model, mode=spec.rr, top_n=DEPTH,
                                     score_cache=self.ce_cache)
        self._built[spec] = r
        return r


def load_ce_model() -> object:
    """Loads the cross-encoder from the local cache only (never downloads)."""
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import CrossEncoder

    return CrossEncoder(DEFAULT_MODEL, max_length=512)


# ---------------------------------------------------------------- metrics

def query_metrics(ranked: list[str], rels: dict[str, int]) -> dict[str, float]:
    """nDCG@10 with unjudged as 0, nDCG@10 condensed, and the unjudged share of the top 10."""
    judged = [d for d in ranked if d in rels]
    top = ranked[:10]
    return {
        "ndcg": ndcg_at_k(ranked, rels, 10),
        "cond": ndcg_at_k(judged, rels, 10),
        "unj": sum(d not in rels for d in top) / max(len(top), 1),
    }


def is_gain(diff_ndcg: float, diff_cond: float, minimum: float = GAIN_MIN) -> bool:
    """True when both nDCG@10 numbers beat the base by more than `minimum`."""
    return diff_ndcg > minimum and diff_cond > minimum


@dataclass
class Run:
    """Per-query results of one variant, aligned with the qids list used to build it."""

    spec: Spec
    qids: list[str]
    metrics: dict[str, list[float]]
    ranked: dict[str, list[str]]

    def mean(self, key: str, qids: list[str] | None = None) -> float:
        idx = [i for i, q in enumerate(self.qids) if qids is None or q in qids]
        return sum(self.metrics[key][i] for i in idx) / max(len(idx), 1)

    def values(self, key: str, qids: list[str]) -> list[float]:
        pos = {q: i for i, q in enumerate(self.qids)}
        return [self.metrics[key][pos[q]] for q in qids]


def run_spec(spec: Spec, rows: list, ctxs: dict[str, ModuleContext],
             qrels: dict[str, dict[str, int]]) -> Run:
    """Runs one variant over the given query rows (each in its own module)."""
    out: dict[str, list[float]] = {"ndcg": [], "cond": [], "unj": []}
    ranked: dict[str, list[str]] = {}
    for row in rows:
        hits = ctxs[row.module].build(spec).search(row.query, k=DEPTH)
        ids = [h.doc_id for h in hits]
        ranked[row.qid] = ids
        m = query_metrics(ids, qrels[row.qid])
        for k in out:
            out[k].append(m[k])
    return Run(spec, [r.qid for r in rows], out, ranked)


# ---------------------------------------------------------------- selection

def best_of(runs: list[Run], key: str, qids: list[str] | None = None) -> Run:
    """Highest mean of `key`; ties keep the earlier (simpler) run."""
    best = runs[0]
    for r in runs[1:]:
        if r.mean(key, qids) > best.mean(key, qids) + 1e-12:
            best = r
    return best


def family_gain(runs: list[Run], base: Run) -> tuple[Run | None, bool]:
    """Best run of a family by nDCG@10, and whether it passes the gain rule vs base."""
    if not runs:
        return None, False
    best = best_of(runs, "ndcg")
    return best, is_gain(best.mean("ndcg") - base.mean("ndcg"), best.mean("cond") - base.mean("cond"))


def unjudged_rows(run: Run, rows: list, qrels: dict[str, dict[str, int]],
                  texts: dict[str, str], split_name: str) -> list[dict]:
    """The top-10 chunks of a run that have no grade for that query."""
    out = []
    for row in rows:
        for rank, d in enumerate(run.ranked[row.qid][:10], start=1):
            if d not in qrels[row.qid]:
                out.append({"variant": run.spec.name, "qid": row.qid, "query": row.query,
                            "module": row.module, "split": split_name, "rank": rank,
                            "chunk_id": d, "text": " ".join(texts[d].split())})
    return out


def write_unjudged(path: str | Path, rows: list[dict]) -> None:
    """Writes the unjudged-rows CSV (UTF-8, one row per variant, query and rank)."""
    cols = ["variant", "qid", "query", "module", "split", "rank", "chunk_id", "text"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- the dev run

def stage1_specs() -> list[Spec]:
    """Baselines plus the full grid of single-stage variants."""
    specs = [Spec("bm25"), Spec("hybrid")]
    for src in ("all", "cfr"):
        for w in WEIGHTS:
            specs.append(Spec("bm25", exp=(w, src, False)))
            specs.append(Spec("hybrid", exp=(w, src, False)))
            specs.append(Spec("hybrid", exp=(w, src, True)))
    for base in ("bm25", "hybrid"):
        for t in TOPS:
            for b in BETAS:
                specs.append(Spec(base, pb=(t, b, "bm25")))
    specs += [Spec("hybrid", rr="replace"), Spec("hybrid", rr="rrf")]
    return specs


def votes_specs(base: str) -> list[Spec]:
    """The alternative part scoring grid for one base."""
    return [Spec(base, pb=(t, b, "rrf_top3")) for t in TOPS for b in BETAS]


def fmt(x: float) -> str:
    return f"{x:.3f}"


def motivating_qids(path: str | Path = "data/eval/synonyms.json") -> set[str]:
    """Queries named in motivated_by of failure-derived groups (the lexicon was written after
    seeing their failures, so any gain on them is not independent evidence)."""
    import json

    groups = json.loads(Path(path).read_text(encoding="utf-8"))["groups"]
    return {q for g in groups for q in g.get("motivated_by", [])}


def table(runs: list[Run], bases: dict[str, Run], qids: list[str], mod_qids: dict[str, list[str]],
          excl: set[str] | None = None) -> list[str]:
    """Markdown table: pooled and per-module nDCG@10 (both numbers), unjudged@10, diff vs base.

    The last column repeats the nDCG@10 difference without the `excl` queries (the leak check).
    """
    rest = [q for q in qids if q not in (excl or set())]
    lines = ["| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine "
             f"| diff vs base [95% CI] | gain | diff without {len(qids) - len(rest)} motivating queries |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        base = bases[r.spec.base]
        d, lo, hi, _ = paired_bootstrap_ci(r.values("ndcg", qids), base.values("ndcg", qids))
        dc = r.mean("cond") - base.mean("cond")
        gain = "yes" if (r is not base and is_gain(d, dc)) else ""
        lines.append(
            f"| {r.spec.name} | {len(qids)} | {fmt(r.mean('ndcg'))} | {fmt(r.mean('cond'))} "
            f"| {fmt(r.mean('unj'))} | {fmt(r.mean('ndcg', mod_qids['device']))} "
            f"| {fmt(r.mean('ndcg', mod_qids['medicine']))} | {d:+.3f} [{lo:+.3f}, {hi:+.3f}] "
            f"| {gain} | {r.mean('ndcg', rest) - base.mean('ndcg', rest):+.3f} |")
    return lines


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 17e: tune on the dev half only.")
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--split", default="data/eval/split_t1.json")
    ap.add_argument("--out", default="results/step17_dev.md")
    ap.add_argument("--unjudged", default="results/step17_unjudged.csv")
    a = ap.parse_args()

    t0 = time.time()
    split = load_split(a.split)
    dev = set(split["dev"])
    rows = [r for r in load_query_rows(a.queries) if r.qid in dev]
    qrels = load_qrels(a.qrels)
    qids = [r.qid for r in rows]
    mod_qids = {m: [r.qid for r in rows if r.module == m] for m in ("device", "medicine")}

    all_chunks = load_chunks(a.corpus)
    texts = {c.chunk_id: c.text for c in all_chunks}
    ce_model, ce_cache = load_ce_model(), {}
    ctxs = {m: ModuleContext([c for c in all_chunks if c.module == m], ce_model, ce_cache)
            for m in ("device", "medicine")}

    runs: dict[Spec, Run] = {}

    def go(specs: list[Spec]) -> None:
        for s in specs:
            if s not in runs:
                runs[s] = run_spec(s, rows, ctxs, qrels)

    go(stage1_specs())
    bases = {"bm25": runs[Spec("bm25")], "hybrid": runs[Spec("hybrid")]}

    def fam(family: str, base: str) -> list[Run]:
        return [r for r in runs.values() if r.spec.family == family and r.spec.base == base]

    notes: list[str] = []
    gains: dict[tuple[str, str], tuple[Run | None, bool]] = {}
    for base in ("bm25", "hybrid"):
        gains[("exp", base)] = family_gain(fam("exp", base), bases[base])
        gains[("pb", base)] = family_gain(fam("pb", base), bases[base])
        if not gains[("pb", base)][1]:
            go(votes_specs(base))
            gains[("pb", base)] = family_gain(fam("pb", base), bases[base])
            notes.append(f"Part boost on {base}: BM25 part scoring showed no gain, so the summed-RRF "
                         f"top-3 vote scoring was also run (both are in the table).")
    gains[("rr", "hybrid")] = family_gain(fam("rr", "hybrid"), bases["hybrid"])

    # Stage 2: combine only components that passed the gain rule.
    def passed(family: str, base: str) -> Spec | None:
        run, ok = gains[(family, base)]
        return run.spec if run is not None and ok else None

    for base in ("bm25", "hybrid"):
        e, p = passed("exp", base), passed("pb", base)
        if e and p:
            go([Spec(base, exp=e.exp, pb=p.pb)])
        elif e or p:
            notes.append(f"No A+B combo on {base}: one of the two components showed no gain on dev.")
    e, p, c = passed("exp", "hybrid"), passed("pb", "hybrid"), passed("rr", "hybrid")
    if c:
        if e:
            go([Spec("hybrid", exp=e.exp, rr=c.rr)])
        if p:
            go([Spec("hybrid", pb=p.pb, rr="rrf")])
        if e and p:
            go([Spec("hybrid", exp=e.exp, pb=p.pb, rr="rrf")])
    else:
        notes.append("Reranker showed no gain over hybrid on dev: no combination with it was run.")

    # Finalists: baselines, and per family the best by each number (plus best per source set).
    finalists: list[Run] = [bases["bm25"], bases["hybrid"]]

    def add(run: Run | None) -> None:
        if run is not None and run not in finalists:
            finalists.append(run)

    for fam_name in ("exp", "pb", "rr", "combo"):
        for base in ("bm25", "hybrid"):
            rs = fam(fam_name, base)
            if rs:
                add(best_of(rs, "ndcg"))
                add(best_of(rs, "cond"))
    for base in ("bm25", "hybrid"):
        for src in ("all", "cfr"):
            rs = [r for r in fam("exp", base) if r.spec.exp and r.spec.exp[1] == src]
            if rs:
                add(best_of(rs, "ndcg"))

    unj = []
    for r in finalists:
        unj += unjudged_rows(r, rows, qrels, texts, "dev")
    write_unjudged(a.unjudged, unj)
    unique = len({(u["qid"], u["chunk_id"]) for u in unj})

    md = [f"# Step 17e: tuning on the development half ({len(qids)} queries)", "",
          f"**{LABEL}.** Dev half only (seed 42 split, {len(mod_qids['device'])} device and "
          f"{len(mod_qids['medicine'])} medicine queries). The held-out half is untouched. Settings were "
          "chosen on these same queries, so differences here are optimistic and the intervals are "
          "descriptive, not tests. Depth 50, nDCG@10, chunk level; queries are searched in their own module.",
          "", "Unjudged chunks are not in the pooled qrels (the pool came from the old systems). "
          "'condensed' removes them from the list first. Gain rule: best config beats its base by "
          f"more than {GAIN_MIN} on both numbers.", ""]
    md += [f"- {n}" for n in notes]
    mot = sorted(motivating_qids())
    md += ["", "**Leak check.** The failure-derived synonym groups were written after reading the failure "
           f"list. Queries that motivated them: {', '.join(mot)} ("
           f"{', '.join(q for q in mot if q in dev) or 'none'} in dev; "
           f"{', '.join(q for q in mot if q not in dev) or 'none'} in held-out). The last column of each "
           "table repeats the difference to the base without the motivating queries that are in dev."]
    titles = {"baseline": "Baselines", "exp": "A. Query expansion", "pb": "B. Part boost",
              "rr": "C. Cross-encoder rerank (hybrid top 50)", "combo": "Combinations"}
    for fam_name, title in titles.items():
        rs = [r for r in runs.values() if r.spec.family == fam_name]
        if rs:
            md += ["", f"## {title}", ""] + table(rs, bases, qids, mod_qids, motivating_qids())
    md += ["", "## Finalists and their unjudged top-10 rows", "",
           "| variant | nDCG@10 | condensed | unjudged rows (dev) |", "|---|---|---|---|"]
    for r in finalists:
        md.append(f"| {r.spec.name} | {fmt(r.mean('ndcg'))} | {fmt(r.mean('cond'))} "
                  f"| {sum(1 for u in unj if u['variant'] == r.spec.name)} |")
    md += ["", f"`{a.unjudged}`: {len(unj)} rows, {unique} unique (query, chunk) pairs to grade "
           "(the same pair can appear under several variants). Nothing was graded here."]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\n[{len(runs)} variants, {time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
