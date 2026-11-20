"""Step 17 held-out update: P1 to P3 recomputed on newer qrels, as a labelled update.

The original held-out run (results/step17_heldout.md) and the frozen config
(data/eval/step17_config.json) are NOT touched. This script
  - checks that the frozen settings and data files are intact (not the qrels hash, which is
    expected to differ now),
  - rebuilds the old qrels from the git commit recorded in the config, runs the frozen
    variants on the held-out half with them and with the newer qrels, and
  - writes results/step17_heldout_update.md, saying plainly that it is an update and not a
    second blind scoring: the held-out queries were seen in Step 17, and nothing is tuned here.

Run:  python -m src.ir.step17_heldout_update
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from src.ir.eval import load_chunks, load_qrels, load_query_rows
from src.ir.metrics import recall_at_k
from src.ir.split import load_split
from src.ir.step17_config import check_config, file_sha256, load_config, spec_from_dict
from src.ir.step17_heldout import compare, fmt, primary_table
from src.ir.step17_report import LABEL, ModuleContext, run_spec

OUT = "results/step17_heldout_update.md"


def qrels_at_commit(commit: str, path: str, tmp: Path) -> dict[str, dict[str, int]]:
    """Reads the qrels file as it was at a git commit (without touching the working tree)."""
    text = subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, check=True,
                          encoding="utf-8").stdout
    tmp.write_text(text, encoding="utf-8")
    return load_qrels(tmp)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Held-out update on newer qrels (labelled).")
    ap.add_argument("--config", default="data/eval/step17_config.json")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--tmp", default="data/processed/_qrels_old_tmp.tsv")
    a = ap.parse_args()

    cfg = load_config(a.config)
    problems = [p for p in check_config(cfg)]
    if problems:
        raise SystemExit("frozen settings or data files changed:\n  " + "\n  ".join(problems))
    old = qrels_at_commit(cfg["main_commit"], cfg["qrels"]["path"], Path(a.tmp))
    new = load_qrels(a.qrels)
    n_old = sum(len(v) for v in old.values())
    n_new = sum(len(v) for v in new.values())

    split = load_split("data/eval/split_t1.json")
    rows = {r.qid: r for r in load_query_rows("data/eval/queries_t1.tsv")}
    held = [rows[q] for q in split["heldout"]]
    hq = [r.qid for r in held]
    sens = set(cfg["params"]["sensitivity_exclude_heldout"])
    hq_sens = [q for q in hq if q not in sens]
    chunks = load_chunks("data/processed/regs.jsonl")
    ctxs = {m: ModuleContext([c for c in chunks if c.module == m], None, {}) for m in ("device", "medicine")}
    keep = [v for v in cfg["variants"] if v["role"] in {"baseline", "primary"} and v["spec"]["base"] != "dense"]
    runs_old = {v["name"]: run_spec(spec_from_dict(v["spec"]), held, ctxs, old) for v in keep}
    runs_new = {v["name"]: run_spec(spec_from_dict(v["spec"]), held, ctxs, new) for v in keep}
    cfg_keep = {"variants": keep}

    md = ["# Step 17 held-out update on newer qrels (labelled update)", "",
          f"**{LABEL}.** This is an UPDATE of `results/step17_heldout.md`, not a second blind scoring. The "
          "held-out queries were seen in Step 17 and nothing is tuned or changed here: the frozen settings "
          f"(hash {cfg['settings_sha256'][:12]}) and data files are verified intact. Only the qrels differ.", "",
          f"- Original run: qrels at main commit `{cfg['main_commit'][:10]}`, {n_old} graded pairs.",
          f"- This update: `{a.qrels}`, {n_new} graded pairs (sha256 `{file_sha256(a.qrels)[:12]}`). The extra "
          "pairs include the 10 held-out pairs listed unjudged in Step 17, and the Step 16 abstention pool.",
          "- Held-out half: 28 answerable queries; the same Holm family P1 to P3 as before.", ""]
    subsets = (("all 28 held-out queries", hq),
               (f"without {', '.join(sorted(sens))} ({len(hq_sens)} queries)", hq_sens))
    versions = (("old qrels (reproduces the Step 17 report)", runs_old), ("newer qrels (update)", runs_new))
    for title, qids in subsets:
        for label, runs in versions:
            lines, _ = primary_table(cfg_keep, runs, qids)
            md += [f"## Primaries, {title}, {label}", ""] + lines + [""]
    md += ["## Baselines on the held-out half", "", "| system | nDCG@10 old qrels | nDCG@10 newer qrels | "
           "Recall@20 old | Recall@20 newer |", "|---|---|---|---|---|"]
    for v in keep:
        n = v["name"]
        ro = sum(recall_at_k(runs_old[n].ranked[q], old[q], 20) for q in hq) / len(hq)
        rn = sum(recall_at_k(runs_new[n].ranked[q], new[q], 20) for q in hq) / len(hq)
        md.append(f"| {n} | {fmt(runs_old[n].mean('ndcg', hq))} | {fmt(runs_new[n].mean('ndcg', hq))} "
                  f"| {fmt(ro)} | {fmt(rn)} |")
    shift = {v["id"]: (compare(runs_new[v["name"]], runs_new[v["vs"]], hq)["diff"]
                       - compare(runs_old[v["name"]], runs_old[v["vs"]], hq)["diff"])
             for v in keep if v["role"] == "primary"}
    md += ["", "Change in each primary's held-out gain from the new qrels: "
           + ", ".join(f"{k} {v:+.3f}" for k, v in shift.items()) + "."]
    Path(a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
