"""Step 18 cross-validation harness: folds, the keep rule, the experiment log.

HOW AN EXPERIMENT IS JUDGED
Every idea is compared with a base system on the same 57 answerable queries. The
queries are split into 5 stratified folds (seed 42, saved in data/eval/cv_folds.json).
For each idea we compute, per fold and pooled over all queries:
  nDCG@10 with unjudged chunks as grade 0   ("unjudged=0")
  nDCG@10 with unjudged chunks removed first ("condensed")
  Recall@20 (reported, not part of the rule)
  unjudged@10: the share of the top 10 that has no grade.

KEEP RULE (fixed before any experiment)
  - the pooled mean gain is above 0.01 on BOTH nDCG lists, and
  - the idea wins in at least 3 of the 5 folds (a fold is won when the gain is above 0
    on both lists), and
  - the gain survives leaving out the two queries that gain most (list by list): the
    remaining gain must still be above 0.01, otherwise the idea is dropped as
    "driven by 1 to 2 queries".
PENDING_GRADING: if the variant's unjudged@10 is above 0.05 the result cannot be trusted
(the qrels were pooled from old systems), so the idea is neither kept nor dropped. Its
unjudged pairs go to results/step18_unjudged.csv for grading and it is re-judged after.

Nothing here learns from the folds. Experiments that fit parameters (fusion weights,
fine-tuning) must fit on four folds and rank the fifth; they hand this module the
resulting rankings, so the rule is applied the same way to every idea.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from src.ir.eval import NO_ANSWER, QueryRow, load_chunks, load_qrels, load_query_rows
from src.ir.metrics import recall_at_k
from src.ir.step14_report import paired_bootstrap_ci
from src.ir.step17_report import DEPTH, query_metrics

SEED = 42
K_FOLDS = 5
GAIN_MIN = 0.01
MIN_FOLD_WINS = 3
PENDING_UNJ = 0.05
FOLDS_PATH = Path("data/eval/cv_folds.json")
EXPERIMENTS_MD = Path("results/step18_experiments.md")
UNJUDGED_CSV = Path("results/step18_unjudged.csv")
LLM_QRELS_NOTE = "LLM-assessed qrels (claude-sonnet-5-5), not human grades"


# ---------------------------------------------------------------- folds

def make_folds(rows: list[QueryRow], k: int = K_FOLDS, seed: int = SEED) -> dict:
    """Stratified k-fold split of the answerable queries.

    Queries are grouped by (type, module), shuffled inside each group with the seed, and
    dealt to the folds like cards; the deal continues where the last group stopped, so
    fold sizes differ by at most one and every group is spread across the folds.
    no_answer queries have no relevant chunk, so they are listed and kept out of the folds.
    """
    rng = random.Random(seed)
    groups: dict[tuple[str, str], list[str]] = defaultdict(list)
    no_answer: list[str] = []
    for r in rows:
        if r.qtype == NO_ANSWER:
            no_answer.append(r.qid)
        else:
            groups[(r.qtype, r.module)].append(r.qid)
    folds: list[list[str]] = [[] for _ in range(k)]
    pos = 0
    for key in sorted(groups):
        ids = sorted(groups[key])
        rng.shuffle(ids)
        for qid in ids:
            folds[pos % k].append(qid)
            pos += 1
    return {"seed": seed, "k": k, "folds": [sorted(f) for f in folds], "no_answer": sorted(no_answer)}


def load_folds(path: str | Path = FOLDS_PATH) -> dict:
    """Loads a folds file written by make_folds."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- scoring

def score_ranked(ranked: list[str], rels: dict[str, int]) -> dict[str, float]:
    """Per-query scores: ndcg (unjudged=0), cond (condensed), unj (unjudged@10), recall20."""
    m = query_metrics(ranked, rels)
    m["recall20"] = recall_at_k(ranked, rels, 20)
    return m


@dataclass
class ExperimentResult:
    """Everything the log and the decision need for one idea."""

    exp_id: str
    title: str
    qids: list[str]
    fold_of: dict[str, int]
    base: dict[str, dict[str, float]]
    var: dict[str, dict[str, float]]
    k: int = K_FOLDS
    extra: dict = field(default_factory=dict)

    def diffs(self, key: str, qids: list[str] | None = None) -> list[float]:
        ids = self.qids if qids is None else qids
        return [self.var[q][key] - self.base[q][key] for q in ids]

    def gain(self, key: str, qids: list[str] | None = None) -> float:
        d = self.diffs(key, qids)
        return sum(d) / max(len(d), 1)

    def fold_qids(self, f: int) -> list[str]:
        return [q for q in self.qids if self.fold_of[q] == f]

    def fold_gain(self, key: str, f: int) -> float:
        return self.gain(key, self.fold_qids(f))

    def folds_won(self) -> int:
        return sum(self.fold_gain("ndcg", f) > 0 and self.fold_gain("cond", f) > 0
                   for f in range(self.k))

    def without_top2(self, key: str) -> float:
        """Pooled gain after removing the two queries with the largest positive gain."""
        order = sorted(self.qids, key=lambda q: self.var[q][key] - self.base[q][key], reverse=True)
        drop = {q for q in order[:2] if self.var[q][key] - self.base[q][key] > 0}
        rest = [q for q in self.qids if q not in drop]
        return self.gain(key, rest)

    def top_gainers(self, key: str = "ndcg", n: int = 2) -> list[tuple[str, float]]:
        order = sorted(self.qids, key=lambda q: self.var[q][key] - self.base[q][key], reverse=True)
        return [(q, self.var[q][key] - self.base[q][key]) for q in order[:n]]

    def unjudged10(self, which: str = "var") -> float:
        src = self.var if which == "var" else self.base
        return sum(src[q]["unj"] for q in self.qids) / max(len(self.qids), 1)


def decide(res: ExperimentResult) -> tuple[str, str]:
    """Applies the keep rule; returns (decision, reason)."""
    gn, gc = res.gain("ndcg"), res.gain("cond")
    won = res.folds_won()
    if res.unjudged10() > PENDING_UNJ:
        return "PENDING_GRADING", (f"unjudged@10 is {res.unjudged10():.3f}, above {PENDING_UNJ}; "
                                   "grade the pairs in results/step18_unjudged.csv, then re-judge")
    if gn <= GAIN_MIN or gc <= GAIN_MIN:
        return "DROPPED", f"gain {gn:+.3f} (unjudged=0) / {gc:+.3f} (condensed) is not above {GAIN_MIN}"
    if won < MIN_FOLD_WINS:
        return "DROPPED", f"wins only {won} of {res.k} folds (needs {MIN_FOLD_WINS})"
    t_n, t_c = res.without_top2("ndcg"), res.without_top2("cond")
    if t_n <= GAIN_MIN or t_c <= GAIN_MIN:
        tops = ", ".join(f"{q} {d:+.3f}" for q, d in res.top_gainers())
        return "DROPPED", (f"driven by 1 to 2 queries ({tops}); without them the gain is "
                           f"{t_n:+.3f} / {t_c:+.3f}")
    return "KEPT", f"gain {gn:+.3f} / {gc:+.3f}, wins {won} of {res.k} folds, survives leave-top-2-out"


def evaluate_experiment(
    exp_id: str,
    title: str,
    base_ranked: dict[str, list[str]],
    var_ranked: dict[str, list[str]],
    qrels: dict[str, dict[str, int]],
    folds: dict,
    extra: dict | None = None,
) -> ExperimentResult:
    """Scores base and variant rankings per query and packages them for the rule and the log."""
    fold_of = {q: i for i, f in enumerate(folds["folds"]) for q in f}
    qids = [q for q in sorted(fold_of) if q in base_ranked and q in var_ranked]
    return ExperimentResult(
        exp_id, title, qids, fold_of,
        {q: score_ranked(base_ranked[q], qrels[q]) for q in qids},
        {q: score_ranked(var_ranked[q], qrels[q]) for q in qids},
        k=folds["k"], extra=extra or {},
    )


# ---------------------------------------------------------------- log

def experiment_markdown(res: ExperimentResult, what: str, params: dict | None = None,
                        notes: str = "") -> str:
    """One experiment section for results/step18_experiments.md."""
    decision, reason = decide(res)
    lo_hi = paired_bootstrap_ci([res.var[q]["ndcg"] for q in res.qids],
                                [res.base[q]["ndcg"] for q in res.qids])
    lines = [f"## {res.exp_id}: {res.title}", "",
             f"**Decision: {decision}.** {reason}.", "",
             f"- What changed: {what}"]
    if params:
        lines.append("- Parameters: " + ", ".join(f"{k}={v}" for k, v in params.items()))
    lines += [
        f"- Pooled over {len(res.qids)} queries: nDCG@10 unjudged=0 {res.gain('ndcg'):+.3f}, "
        f"condensed {res.gain('cond'):+.3f}, Recall@20 {res.gain('recall20'):+.3f}.",
        f"- Bootstrap 95% interval of the unjudged=0 gain (information only): "
        f"[{lo_hi[1]:+.3f}, {lo_hi[2]:+.3f}].",
        f"- Leave-top-2-out gain: {res.without_top2('ndcg'):+.3f} / {res.without_top2('cond'):+.3f}; "
        "top gainers: " + ", ".join(f"{q} {d:+.3f}" for q, d in res.top_gainers()) + ".",
        f"- unjudged@10: variant {res.unjudged10():.3f}, base {res.unjudged10('base'):.3f}.",
        "", "| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for f in range(res.k):
        ids = res.fold_qids(f)
        bn = sum(res.base[q]["ndcg"] for q in ids) / len(ids)
        vn = sum(res.var[q]["ndcg"] for q in ids) / len(ids)
        bc = sum(res.base[q]["cond"] for q in ids) / len(ids)
        vc = sum(res.var[q]["cond"] for q in ids) / len(ids)
        won = "yes" if (vn - bn > 0 and vc - bc > 0) else ""
        lines.append(f"| {f + 1} | {len(ids)} | {bn:.3f} | {vn:.3f} | {vn - bn:+.3f} "
                     f"| {bc:.3f} | {vc:.3f} | {vc - bc:+.3f} | {won} |")
    pooled_bn = sum(res.base[q]["ndcg"] for q in res.qids) / len(res.qids)
    pooled_vn = sum(res.var[q]["ndcg"] for q in res.qids) / len(res.qids)
    lines += ["", f"Pooled base nDCG@10 {pooled_bn:.3f}, variant {pooled_vn:.3f}; folds won "
              f"{res.folds_won()} of {res.k}."]
    if notes:
        lines += ["", notes]
    return "\n".join(lines) + "\n"


HEADER = ("# Step 18 experiments\n\n"
          f"**{LLM_QRELS_NOTE}.** 5-fold stratified cross-validation over the 57 answerable queries "
          "(`data/eval/cv_folds.json`, seed 42). Gains are over the stated base, pooled over all queries. "
          "Keep rule: gain above 0.01 on both nDCG@10 lists (unjudged=0 and condensed), at least 3 of 5 "
          "folds won, survives leaving out the two biggest-gaining queries. unjudged@10 above 0.05 "
          "means PENDING_GRADING. This file is written by the harness; each section is replaced when its "
          "experiment is re-run.\n")


def upsert_section(path: str | Path, exp_id: str, section: str) -> None:
    """Writes section into the log, replacing an existing section with the same exp_id."""
    p = Path(path)
    text = p.read_text(encoding="utf-8") if p.exists() else HEADER
    parts = text.split("\n## ")
    head, rest = parts[0], parts[1:]
    kept = [s for s in rest if not s.startswith(f"{exp_id}:")]
    new = section.removeprefix("## ")
    allp = kept + [new]
    allp.sort(key=lambda s: s.split(":")[0])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(head.rstrip("\n") + "\n\n" + "\n".join("## " + s.rstrip("\n") + "\n" for s in allp),
                 encoding="utf-8")


# ---------------------------------------------------------------- unjudged pairs

def update_unjudged_csv(path: str | Path, variant: str, exp_id: str, rows: list[QueryRow],
                        ranked: dict[str, list[str]], qrels: dict[str, dict[str, int]],
                        texts: dict[str, str]) -> int:
    """Adds the variant's unjudged top-10 pairs to the cumulative CSV; returns the pair count.

    One row per (qid, chunk_id). Pairs that have since been graded in qrels are dropped, so the
    file only ever lists what still needs grading. Nothing is scored as relevant.
    """
    cols = ["qid", "query", "module", "chunk_id", "text", "first_seen_in", "variants"]
    p = Path(path)
    book: dict[tuple[str, str], dict[str, str]] = {}
    if p.exists():
        with p.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                book[(r["qid"], r["chunk_id"])] = r
    for row in rows:
        for cid in ranked.get(row.qid, [])[:10]:
            if cid in qrels.get(row.qid, {}):
                continue
            key = (row.qid, cid)
            if key in book:
                names = set(book[key]["variants"].split(" | "))
                names.add(variant)
                book[key]["variants"] = " | ".join(sorted(names))
            else:
                book[key] = {"qid": row.qid, "query": row.query, "module": row.module, "chunk_id": cid,
                             "text": " ".join(texts[cid].split()), "first_seen_in": exp_id,
                             "variants": variant}
    book = {k: v for k, v in book.items() if k[1] not in qrels.get(k[0], {})}
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(sorted(book.values(), key=lambda r: (r["qid"], r["chunk_id"])))
    return len(book)


# ---------------------------------------------------------------- running systems

def rank_with_spec(spec: object, rows: list[QueryRow], ctxs: dict) -> dict[str, list[str]]:
    """Top-DEPTH chunk ids per query for a step17 Spec, each query in its own module."""
    return {r.qid: [h.doc_id for h in ctxs[r.module].build(spec).search(r.query, k=DEPTH)] for r in rows}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 18 CV harness.")
    ap.add_argument("action", choices=["folds", "e0"])
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--folds", default=str(FOLDS_PATH))
    a = ap.parse_args()
    rows = load_query_rows(a.queries)
    if a.action == "folds":
        folds = make_folds(rows)
        Path(a.folds).write_text(json.dumps(folds, indent=1) + "\n", encoding="utf-8")
        info = {r.qid: r for r in rows}
        for i, f in enumerate(folds["folds"]):
            mods = defaultdict(int)
            types = defaultdict(int)
            for q in f:
                mods[info[q].module] += 1
                types[info[q].qtype] += 1
            print(f"fold {i + 1}: n={len(f)} modules={dict(mods)} types={dict(types)}")
        print(f"no_answer left out: {folds['no_answer']}")
        return
    # e0: hybrid+stem+prefix vs hybrid, a carried-over idea that checks the harness end to end
    from src.ir.step17_report import ModuleContext, Spec

    folds = load_folds(a.folds)
    qrels = load_qrels(a.qrels)
    chunks = load_chunks("data/processed/regs.jsonl")
    texts = {c.chunk_id: c.text for c in chunks}
    ctxs = {m: ModuleContext([c for c in chunks if c.module == m], None, {}) for m in ("device", "medicine")}
    answer = [r for r in rows if r.qid in {q for f in folds["folds"] for q in f}]
    base = rank_with_spec(Spec("hybrid"), answer, ctxs)
    var_spec = Spec("hybrid", stem=True, prefix=True)
    var = rank_with_spec(var_spec, answer, ctxs)
    res = evaluate_experiment("E0", "hybrid+stem+prefix vs hybrid (carried over from Step 17)", base, var,
                              qrels, folds)
    what = ("BM25 half uses the light-stemmed index and the dense half adds the BGE query instruction. "
            "Base is plain hybrid. Run first to check the harness; Step 17 already saw these queries.")
    upsert_section(EXPERIMENTS_MD, "E0", experiment_markdown(res, what, {"base": "hybrid",
                                                                         "variant": var_spec.name}))
    n = update_unjudged_csv(UNJUDGED_CSV, var_spec.name, "E0", answer, var, qrels, texts)
    print(decide(res), f"| unjudged pairs in {UNJUDGED_CSV}: {n}")


if __name__ == "__main__":
    main()
