"""Step 15b: ablation tables on the LLM-assessed qrels (data/eval/qrels_t1_llm.tsv).

Usage (repo root):
  python -m src.ir.step15_report      # -> results/step15_ablations.md

One section per ablation, and inside it one table per module (device, medicine) and per
level (chunk, section). Each variant is compared with the default it changes:

  rrf_k          rrf_k10, rrf_k30, rrf_k100            vs default_hybrid
  weights        w_bm25_2_dense_1 ... w_bm25_1_dense_3 vs default_hybrid
  stemming       bm25_stem vs default_bm25, hybrid_stem vs default_hybrid
  query_prefix   dense_prefix vs default_dense, hybrid_prefix vs default_hybrid

That is 11 comparisons per module, 22 over both modules, at each level. nDCG@10 is the
primary metric: its difference gets a paired bootstrap interval (queries resampled, 10000
times, seed 42), a raw p, a Holm-adjusted p within the ablation (both modules together) and
a Holm-adjusted p over all 22 (same level). Chunk and section level are separate families.
The grid is a sensitivity analysis fixed in advance, not tuning.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.eval import (
    METRIC_NAMES,
    evaluate,
    find_corpus_gaps,
    load_chunks,
    load_qrels,
    load_query_rows,
    split_no_answer,
)
from src.ir.step14_report import (
    LABEL,
    METRIC_TITLES,
    bootstrap_mean_interval,
    holm_adjust,
    mean,
    paired_bootstrap_ci,
)
from src.ir.step15_ablation import TOP_K, build_variants, collect_unjudged, weight_name

LEVELS = ("chunk", "section")
# ablation key -> (title, [(variant, reference variant), ...]), grid fixed in advance
ABLATIONS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "rrf_k": (
        "RRF smoothing constant k (default 60)",
        [(f"rrf_k{k}", "default_hybrid") for k in (10, 30, 100)],
    ),
    "weights": (
        "RRF weights bm25:dense (default 1:1)",
        [(weight_name(b, d), "default_hybrid") for b, d in ((2, 1), (3, 1), (1, 2), (1, 3))],
    ),
    "stemming": (
        "Light stemming in BM25",
        [("bm25_stem", "default_bm25"), ("hybrid_stem", "default_hybrid")],
    ),
    "query_prefix": (
        "BGE retrieval instruction prefix on queries",
        [("dense_prefix", "default_dense"), ("hybrid_prefix", "default_hybrid")],
    ),
}
PROVISIONAL = (
    "**Recall@20, MAP and MRR are provisional until the depth-20 pool is graded.** They reach "
    "past rank 10, and the qrels only cover the top 10 of each variant plus the original pool. "
    "The chunk-level tables show how many ranks 11 to 20 are still unjudged (counted as 0). "
    "nDCG@10 is the primary metric and uses only the top 10."
)


def per_variant_metrics(
    variants: dict[str, Retriever],
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
    c2s: dict[str, str],
) -> dict[str, dict[str, dict[str, list[float]]]]:
    """Per-query metrics for every variant: level -> variant -> metric -> values.

    Each variant is evaluated alone because evaluate() keys results by the retriever's
    own name, and several variants share a name (all hybrids are called 'hybrid').
    Values are aligned to the order of queries.
    """
    out: dict[str, dict[str, dict[str, list[float]]]] = {lv: {} for lv in LEVELS}
    for name, system in variants.items():
        _, chunk_pq = evaluate([system], queries, qrels)
        _, sec_pq = evaluate([system], queries, qrels, chunk_to_section=c2s)
        out["chunk"][name] = dict(chunk_pq[system.name])
        out["section"][name] = dict(sec_pq[system.name])
    return out


def module_ablation_data(
    chunks: list[Chunk],
    variants: dict[str, Retriever],
    rows: list,
    qrels: dict[str, dict[str, int]],
) -> dict:
    """Metrics and unjudged counts for one module's scored queries (gaps excluded).

    Scored queries are the answerable graded queries minus corpus gaps, the same set as
    the Step 14 main tables. Unjudged counts use the same queries: 'chunk' and 'section'
    are unjudged items in the top 10, 'r11_20' unjudged chunks at ranks 11 to 20.
    """
    answerable, _ = split_no_answer(rows)
    graded = [r.qid for r in answerable if r.qid in qrels]
    gaps = set(find_corpus_gaps(graded, qrels))
    queries = {r.qid: r.query for r in answerable if r.qid in qrels and r.qid not in gaps}
    c2s = {c.chunk_id: (c.section or c.chunk_id) for c in chunks}
    mod = chunks[0].module or ""
    _, top10 = collect_unjudged({mod: variants}, {mod: chunks}, {mod: queries}, qrels)
    _, r11 = collect_unjudged(
        {mod: variants}, {mod: chunks}, {mod: queries}, qrels, k=2 * TOP_K, start=TOP_K
    )
    unj = {
        v: {
            "chunk": top10[v]["chunk_rows"],
            "section": top10[v]["section_rows"],
            "r11_20": r11[v]["chunk_rows"],
        }
        for v in variants
    }
    return {
        "module": mod,
        "qids": list(queries),
        "gaps": sorted(gaps),
        "pq": per_variant_metrics(variants, queries, qrels, c2s),
        "unjudged": unj,
    }


def comparison_rows(data: dict[str, dict]) -> list[dict]:
    """All nDCG@10 comparisons vs the default each variant changes, with both Holm columns.

    One row per (module, level, variant). p_holm_abl adjusts within the (level, ablation)
    family, both modules together; p_holm_all adjusts within the (level) family of all 22.
    """
    rows: list[dict] = []
    for mod in sorted(data):
        for level in LEVELS:
            pq = data[mod]["pq"][level]
            for abl, (_, pairs) in ABLATIONS.items():
                for variant, ref in pairs:
                    d, lo, hi, p = paired_bootstrap_ci(pq[variant]["ndcg"], pq[ref]["ndcg"])
                    rows.append({
                        "module": mod, "level": level, "ablation": abl, "variant": variant,
                        "ref": ref, "n": len(pq[variant]["ndcg"]),
                        "diff": d, "lo": lo, "hi": hi, "p": p,
                    })
    for level in LEVELS:
        lv_rows = [r for r in rows if r["level"] == level]
        for r, adj in zip(lv_rows, holm_adjust([r["p"] for r in lv_rows]), strict=True):
            r["p_holm_all"] = adj
        for abl in ABLATIONS:
            fam = [r for r in lv_rows if r["ablation"] == abl]
            for r, adj in zip(fam, holm_adjust([r["p"] for r in fam]), strict=True):
                r["p_holm_abl"] = adj
    return rows


def _cell_p(p: float) -> str:
    """'0.123' style cell from a p-value (drops the 'p=' prefix)."""
    if p != p:
        return "n/a"
    if p < 0.0002:
        return "<0.0002"
    return f"{p:.4f}" if p < 0.001 else f"{p:.3f}"


def ablation_table(
    mod_data: dict, level: str, abl: str, comps: dict[tuple[str, str, str, str], dict]
) -> list[str]:
    """Markdown table for one ablation, one module, one level."""
    _, pairs = ABLATIONS[abl]
    pq = mod_data["pq"][level]
    mod = mod_data["module"]
    refs = list(dict.fromkeys(ref for _, ref in pairs))
    show_r11 = level == "chunk"
    head = (
        "| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) "
        "| Holm (all 22) | unjudged@10 |"
    )
    if show_r11:
        head += " unjudged ranks 11-20 |"
    head += " " + " | ".join(f"{METRIC_TITLES[m]}*" for m in METRIC_NAMES[1:]) + " |"
    cols = head.count("|") - 1
    lines = [head, "|" + "---|" * cols]
    order = [(r, None) for r in refs] + [(v, ref) for v, ref in pairs]
    for name, ref in order:
        vals = pq[name]
        m, lo, hi = bootstrap_mean_interval(vals["ndcg"])
        unj = mod_data["unjudged"][name]
        if ref is None:
            diff_cells = ["reference", "", "", ""]
            label = f"{name} (default)"
        else:
            c = comps[(mod, level, abl, name)]
            diff_cells = [
                f"{c['diff']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}]",
                _cell_p(c["p"]), _cell_p(c["p_holm_abl"]), _cell_p(c["p_holm_all"]),
            ]
            label = f"{name} (vs {ref})"
        cells = [label, f"{m:.3f} [{lo:.3f}, {hi:.3f}]", *diff_cells, str(unj[level])]
        if show_r11:
            cells.append(str(unj["r11_20"]))
        cells += [f"{mean(vals[k]):.3f}" for k in METRIC_NAMES[1:]]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def ablations_report(data: dict[str, dict]) -> str:
    """Builds the 15b markdown for every ablation, module and level."""
    comps = comparison_rows(data)
    index = {(r["module"], r["level"], r["ablation"], r["variant"]): r for r in comps}
    n_all = len([r for r in comps if r["level"] == "chunk"])
    out = [
        "# Step 15b: ablation tables",
        "",
        f"**All tables use {LABEL}.** Sensitivity analysis: every variant changes one thing from",
        "the default (bm25 k1=1.5 b=0.75 unstemmed, dense bge-small-en-v1.5 without query prefix,",
        "hybrid RRF k=60 weights 1:1). The grid was fixed before any result was seen and nothing",
        "here is tuned. Device and medicine are separate tables.",
        "",
        "## How to read this",
        "- Each variant is compared with the default it changes (named in its row). The table also",
        "  shows that default as a reference row.",
        "- nDCG@10 is the primary metric. The interval on each nDCG@10 is a percentile bootstrap over",
        "  queries (10000 resamples, seed 42). The difference vs default is a paired bootstrap over",
        "  queries with a two-sided percentile bootstrap p-value (resolution about 0.0002).",
        "  When a variant ranks most queries exactly like its default, many resamples have a mean",
        "  difference of exactly 0, so p is conservative.",
        "- **Holm (this ablation)** adjusts the raw p within one ablation at one level, both modules",
        "  together (rrf_k 6 comparisons, weights 8, stemming 4, query_prefix 4).",
        f"  **Holm (all {n_all})** adjusts over all {n_all} nDCG@10 comparisons at that level",
        "  (11 variants x 2 modules). Chunk and section level are separate families. A Holm p is",
        "  never smaller than the raw p.",
        "- **unjudged@10** is the number of top-10 chunks (chunk level) or top-10 sections (section",
        "  level) of the variant that have no LLM grade, summed over the scored queries. A section",
        "  counts as judged when any of its chunks is graded. Unjudged items score 0. At chunk level",
        "  every value is 0, so no chunk-level nDCG@10 is understated by missing grades. At section",
        "  level the value is NOT 0: the extra pool graded top-10 chunks, not the sections that the",
        "  chunk ranking aggregates into (built from the top 100 chunks), so some top-10 sections hold",
        "  no graded chunk. Read section-level differences with that in mind.",
        "- Scored queries are the answerable graded queries (no_answer queries and corpus gaps",
        "  excluded), as in the Step 14 main tables.",
        "",
        f"> {PROVISIONAL}",
        "> The columns marked * (Recall@20, MRR, MAP) are those provisional metrics and carry no",
        "> p-values.",
        "",
    ]
    for abl, (title, _) in ABLATIONS.items():
        out += [f"## Ablation: {title} (`{abl}`)", ""]
        for mod in sorted(data):
            md = data[mod]
            for level in LEVELS:
                n = len(md["qids"])
                out += [
                    f"### {mod.capitalize()}, {level} level, {n} queries. {LABEL}",
                    "",
                    *ablation_table(md, level, abl, index),
                    "",
                ]
    out += [
        "## Caveats",
        "- Grades are the LLM's. In Step 13 the LLM was stricter than the humans at the 0/1",
        "  boundary. Step 13 used the original 308-row human sample pool and is frozen.",
        "- 10000 bootstrap resamples over 17 to 40 queries per module give wide intervals. A",
        "  non-significant Holm p is absence of evidence, not evidence of no effect.",
        "- Weights and k values were not tuned on these queries, but they were looked at together,",
        "  so read the best variant as a candidate, not a win.",
        "",
    ]
    return "\n".join(out)


def build_data(corpus: str, queries: str, qrels_path: str) -> dict[str, dict]:
    """Builds all variants per module and collects metrics and unjudged counts."""
    all_chunks = load_chunks(corpus)
    qrels = load_qrels(qrels_path)
    rows_q = load_query_rows(queries)
    data: dict[str, dict] = {}
    for mod in sorted({c.module for c in all_chunks if c.module}):
        chunks = [c for c in all_chunks if c.module == mod]
        variants = build_variants(chunks)
        rows = [r for r in rows_q if r.module == mod]
        data[mod] = module_ablation_data(chunks, variants, rows, qrels)
    return data


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Step 15b ablation tables.")
    ap.add_argument("--corpus", default="data/processed/regs.jsonl")
    ap.add_argument("--queries", default="data/eval/queries_t1.tsv")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--out-dir", default="results")
    a = ap.parse_args()
    text = ablations_report(build_data(a.corpus, a.queries, a.qrels))
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "step15_ablations.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
