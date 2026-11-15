"""Step 18-abs: can retrieval scores tell answerable medicine queries from unanswerable ones?

SETUP (medicine index only, like Step 16, whose files are not touched)
  positives  the 17 answerable medicine queries q45 to q61 (class "answerable")
  negatives  the 10 Step 16 no_answer queries ab11 to ab20 (class "no_answer"); rows from
             data/eval/fresh_no_answer_candidates.csv join once they are pooled and graded
  split      half of each class is held out as the abstention TEST split (seed 42), scored once
             at 18f. This module scores the DEV half only unless run with --test.

SCORES (first stage: hybrid+stem+prefix on the medicine index, top 30)
  ce_top      best bge-reranker-base score among the top 30 candidates (cache from 18b where it exists)
  ce_margin   best minus second-best cross-encoder score
  zavg        mean of the z-scored bm25 top score and dense top cosine (mean and std from the dev half)
  logreg      leave-one-out logistic regression on [bm25 top, dense top, ce top, query-term coverage
              of the first-stage rank-1 chunk]

METRICS (answerable is the positive class for AUROC; higher score = more likely answerable)
  AUROC with a bootstrap 95% interval (10,000 resamples, seed 42, the two classes resampled
  separately); leave-one-out abstention (no_answer is the positive class): precision and recall.
  Targets: AUROC 0.90 or more and leave-one-out precision 0.80 or more.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import numpy as np

from src.ir.tokenizer import tokenize

SEED = 42
N_BOOT = 10000
SPLIT_PATH = Path("data/eval/abstain_split.json")
TARGET_AUROC, TARGET_PRECISION = 0.90, 0.80


def halves(ids: list[str], seed: int = SEED) -> tuple[list[str], list[str]]:
    """Seeded split into (dev, test); dev gets the extra id when the count is odd."""
    ids = sorted(ids)
    random.Random(seed).shuffle(ids)
    k = math.ceil(len(ids) / 2)
    return sorted(ids[:k]), sorted(ids[k:])


def make_split(pos: list[str], neg: list[str], seed: int = SEED) -> dict:
    """Stratified abstention split: half of the positives and half of the negatives each way."""
    pd, pt = halves(pos, seed)
    nd, nt = halves(neg, seed)
    return {"seed": seed, "dev": {"answerable": pd, "no_answer": nd}, "test": {"answerable": pt, "no_answer": nt}}


def auroc(pos: list[float], neg: list[float]) -> float:
    """P(a random positive scores above a random negative); ties count one half."""
    p, n = np.asarray(pos, float), np.asarray(neg, float)
    gt = (p[:, None] > n[None, :]).sum() + 0.5 * (p[:, None] == n[None, :]).sum()
    return float(gt / (len(p) * len(n)))


def bootstrap_auroc(pos: list[float], neg: list[float], n_boot: int = N_BOOT, seed: int = SEED,
                    level: float = 0.95) -> tuple[float, float]:
    """Percentile interval with the two classes resampled separately (both are always present)."""
    rng = np.random.default_rng(seed)
    p, n = np.asarray(pos, float), np.asarray(neg, float)
    ip = rng.integers(0, len(p), size=(n_boot, len(p)))
    inn = rng.integers(0, len(n), size=(n_boot, len(n)))
    ps, ns = p[ip], n[inn]
    gt = (ps[:, :, None] > ns[:, None, :]).sum(axis=(1, 2)) + 0.5 * (ps[:, :, None] == ns[:, None, :]).sum(axis=(1, 2))
    vals = gt / (len(p) * len(n))
    return float(np.quantile(vals, (1 - level) / 2)), float(np.quantile(vals, (1 + level) / 2))


def best_threshold(scores: list[float], labels: list[int]) -> float:
    """Threshold maximising balanced accuracy for 'answerable if score >= t' (midpoints, plus both ends)."""
    s = sorted(set(scores))
    cands = [s[0] - 1.0] + [(a + b) / 2 for a, b in zip(s, s[1:], strict=False)] + [s[-1] + 1.0]
    best, best_t = -1.0, cands[0]
    for t in cands:
        tp = sum(1 for x, y in zip(scores, labels, strict=True) if y == 1 and x >= t)
        tn = sum(1 for x, y in zip(scores, labels, strict=True) if y == 0 and x < t)
        n1, n0 = sum(labels), len(labels) - sum(labels)
        bal = 0.5 * (tp / n1 + tn / n0)
        if bal > best + 1e-12:
            best, best_t = bal, t
    return best_t


def loo_threshold_abstain(scores: list[float], labels: list[int]) -> list[int]:
    """Leave-one-out decisions (1 = abstain): the threshold is picked on the other queries."""
    out = []
    for i in range(len(scores)):
        rest_s = scores[:i] + scores[i + 1:]
        rest_y = labels[:i] + labels[i + 1:]
        out.append(int(scores[i] < best_threshold(rest_s, rest_y)))
    return out


def loo_logreg_abstain(features: np.ndarray, labels: list[int], c: float = 1.0) -> list[int]:
    """Leave-one-out logistic regression (standardised inside each fold); 1 = abstain (p(answerable) < 0.5)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    y = np.asarray(labels)
    out = []
    for i in range(len(y)):
        keep = np.arange(len(y)) != i
        sc = StandardScaler().fit(features[keep])
        clf = LogisticRegression(C=c, max_iter=1000).fit(sc.transform(features[keep]), y[keep])
        out.append(int(clf.predict_proba(sc.transform(features[i:i + 1]))[0, 1] < 0.5))
    return out


def abstain_precision_recall(decisions: list[int], labels: list[int]) -> tuple[float | None, float]:
    """Precision and recall of abstaining; no_answer (label 0) is the positive class."""
    tp = sum(1 for d, y in zip(decisions, labels, strict=True) if d == 1 and y == 0)
    fp = sum(1 for d, y in zip(decisions, labels, strict=True) if d == 1 and y == 1)
    fn = sum(1 for d, y in zip(decisions, labels, strict=True) if d == 0 and y == 0)
    prec = tp / (tp + fp) if tp + fp else None
    return prec, tp / (tp + fn) if tp + fn else 0.0


def coverage(query: str, chunk_text: str) -> float:
    """Share of the query's content tokens (stopwords removed, light stemming) found in the chunk."""
    q = set(tokenize(query, stem=True))
    return len(q & set(tokenize(chunk_text, stem=True))) / len(q) if q else 0.0


def zscorer(values: list[float]):
    """Returns f(x) = (x - mean) / std using the given (dev) values."""
    m = float(np.mean(values))
    s = float(np.std(values)) or 1.0
    return lambda x: (x - m) / s


def fmt_ci(a: float, ci: tuple[float, float]) -> str:
    return f"{a:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]"


def evaluate(feat: dict[str, dict[str, float]], labels: dict[str, int], z_from: list[str],
             z_feat: dict[str, dict[str, float]] | None = None) -> list[dict]:
    """Metrics for each score on the queries in feat (labels: 1 answerable, 0 no_answer).

    feat maps qid to {bm25, dense, ce_top, ce_margin, coverage}; z_from lists the qids whose values set
    the z-score mean and std (looked up in z_feat, default feat, so a test run can still fit on dev).
    """
    qids = sorted(feat)
    zf = z_feat if z_feat is not None else feat
    zb = zscorer([zf[q]["bm25"] for q in z_from])
    zd = zscorer([zf[q]["dense"] for q in z_from])
    scores = {
        "ce_top": [feat[q]["ce_top"] for q in qids],
        "ce_margin": [feat[q]["ce_margin"] for q in qids],
        "zavg(bm25 top, dense top)": [(zb(feat[q]["bm25"]) + zd(feat[q]["dense"])) / 2 for q in qids],
    }
    y = [labels[q] for q in qids]
    rows = []
    for name, s in scores.items():
        pos = [v for v, t in zip(s, y, strict=True) if t == 1]
        neg = [v for v, t in zip(s, y, strict=True) if t == 0]
        dec = loo_threshold_abstain(s, y)
        prec, rec = abstain_precision_recall(dec, y)
        rows.append({"score": name, "auroc": auroc(pos, neg), "ci": bootstrap_auroc(pos, neg),
                     "abstained": sum(dec), "precision": prec, "recall": rec})
    x = np.array([[feat[q]["bm25"], feat[q]["dense"], feat[q]["ce_top"], feat[q]["coverage"]] for q in qids])
    dec = loo_logreg_abstain(x, y)
    prec, rec = abstain_precision_recall(dec, y)
    rows.append({"score": "logreg (LOO) on [bm25 top, dense top, ce top, coverage]", "auroc": None, "ci": None,
                 "abstained": sum(dec), "precision": prec, "recall": rec})
    return rows


def report_markdown(rows: list[dict], n_pos: int, n_neg: int, split: str, per_query: list[str]) -> str:
    """Markdown table plus the target check."""
    lines = ["| score | AUROC [95% CI] | abstained | LOO precision | LOO recall | meets targets |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        au = fmt_ci(r["auroc"], r["ci"]) if r["auroc"] is not None else "n/a (no single score)"
        pr = "n/a" if r["precision"] is None else f"{r['precision']:.3f}"
        ok_a = r["auroc"] is not None and r["auroc"] >= TARGET_AUROC
        ok_p = r["precision"] is not None and r["precision"] >= TARGET_PRECISION
        lines.append(f"| {r['score']} | {au} | {r['abstained']} of {n_pos + n_neg} | {pr} | {r['recall']:.3f} "
                     f"| AUROC {'yes' if ok_a else 'no'}, precision {'yes' if ok_p else 'no'} |")
    return "\n".join([f"**{split} split: {n_pos} answerable, {n_neg} no_answer.** Targets: AUROC "
                      f">= {TARGET_AUROC}, leave-one-out precision >= {TARGET_PRECISION}.", ""] + lines
                     + ["", "Per query (qid: label, ce_top, ce_margin, bm25 top, dense top, coverage):", ""]
                     + per_query)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 18-abs abstention track (dev half unless --test).")
    ap.add_argument("--test", action="store_true", help="score the held-out half (once, at 18f)")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--out", default="results/step18_abstain.md")
    a = ap.parse_args()
    from src.ir.eval import load_chunks, load_query_rows
    from src.ir.step17_report import ModuleContext, Spec
    from src.ir.step18_rerank import load_score_cache, save_score_cache

    pos = [r.qid for r in load_query_rows("data/eval/queries_t1.tsv")
           if r.module == "medicine" and r.qtype != "no_answer"]
    ab = load_query_rows("data/eval/queries_t1_abstain.tsv")
    neg = [r.qid for r in ab if r.qtype == "no_answer"]
    if SPLIT_PATH.exists():
        split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    else:
        split = make_split(pos, neg)
        SPLIT_PATH.write_text(json.dumps(split, indent=1) + "\n", encoding="utf-8")
    half = "test" if a.test else "dev"
    if a.test:
        a.out = "results/step18_abstain_test.md"
        if Path(a.out).exists():
            raise SystemExit(f"{a.out} exists: the abstention test split is scored once")
    queries = {r.qid: r.query for r in load_query_rows("data/eval/queries_t1.tsv")}
    queries.update({r.qid: r.query for r in ab})
    labels = {q: 1 for q in pos} | {q: 0 for q in neg}
    use = split[half]["answerable"] + split[half]["no_answer"]
    z_from = split["dev"]["answerable"] + split["dev"]["no_answer"]
    use_all = list(dict.fromkeys(use + z_from))  # z-scores are always fitted on the dev half
    chunks = [c for c in load_chunks("data/processed/regs.jsonl") if c.module == "medicine"]
    ctx = ModuleContext(chunks, None, {})
    first = ctx.build(Spec("hybrid", stem=True, prefix=True))
    text_of = {c.chunk_id: c.text for c in chunks}
    cache_path = "data/processed/ce_cache_bge-reranker-base.json"
    cache = load_score_cache(cache_path)
    todo = {q: [h for h in first.search(queries[q], k=30)] for q in use_all}
    missing = sum((queries[q], h.doc_id) not in cache for q, hs in todo.items() for h in hs)
    print(f"[scores] {len(use)} {half} queries, {missing} cross-encoder pairs not in the 18b cache", flush=True)
    if missing:
        import os

        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        import torch
        from sentence_transformers import CrossEncoder

        torch.set_num_threads(a.threads)
        from src.ir.rerank import CrossEncoderReranker

        rr = CrossEncoderReranker(first, model=CrossEncoder("BAAI/bge-reranker-base", max_length=512),
                                  top_n=30, batch_size=8, score_cache=cache)
        for q, hs in todo.items():
            rr.scores(queries[q], hs)
        save_score_cache(cache_path, "BAAI/bge-reranker-base", cache)
    feat: dict[str, dict[str, float]] = {}
    for q in use_all:
        hs = todo[q]
        ce = sorted((cache[(queries[q], h.doc_id)] for h in hs), reverse=True)
        feat[q] = {"bm25": ctx.bm25.search(queries[q], k=1)[0].score,
                   "dense": ctx.dense_prefix.search(queries[q], k=1)[0].score,
                   "ce_top": ce[0], "ce_margin": ce[0] - ce[1], "coverage": coverage(queries[q], text_of[hs[0].doc_id])}
    rows = evaluate({q: feat[q] for q in use}, labels, z_from, z_feat=feat)
    per = [f"- {q}: {'answerable' if labels[q] else 'no_answer'}, {feat[q]['ce_top']:.3f}, {feat[q]['ce_margin']:.3f}, "
           f"{feat[q]['bm25']:.2f}, {feat[q]['dense']:.3f}, {feat[q]['coverage']:.2f}" for q in sorted(use)]
    body = report_markdown(rows, len(split[half]["answerable"]), len(split[half]["no_answer"]),
                           "TEST" if a.test else "DEV", per)
    print(body)
    if a.test:
        Path(a.out).write_text("# Step 18-abs: abstention TEST split (scored once)\n\n" + body + "\n",
                               encoding="utf-8")
    else:
        Path(a.out).write_text(
            "# Step 18-abs: abstention track (dev half only)\n\n"
            "**LLM-assessed qrels are not used here; the labels are the query classes. The TEST split is not "
            "scored in this file: it is scored once at 18f, so these numbers come from 14 queries and are "
            "development numbers.** Step 16's files are untouched.\n\n"
            "Setup: medicine index only; positives q45 to q61 (17), negatives ab11 to ab20 (10). Scores come "
            "from hybrid+stem+prefix top 30; ce = bge-reranker-base. The z-scores use the dev half. "
            f"Split saved in `{SPLIT_PATH}` (seed 42): dev {len(split['dev']['answerable'])} + "
            f"{len(split['dev']['no_answer'])}, test {len(split['test']['answerable'])} + "
            f"{len(split['test']['no_answer'])}.\n\n## Dev half\n\n" + body + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
