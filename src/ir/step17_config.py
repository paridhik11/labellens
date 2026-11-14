"""Frozen configuration for the Step 17 held-out run.

WHY A FROZEN CONFIG
Every setting below was chosen on the development half (results/step17_dev.md). The
held-out half is scored exactly once with exactly these settings. To make that
checkable, the config stores:
  - the variants (as the same Spec fields the dev run used), their role and baseline,
  - the fixed parameters (depth, models, bootstrap seed, Holm family),
  - a SHA-256 of the data files the settings depend on (lexicon, split, queries, corpus),
  - settings_sha256, a hash over all of the above.
Two fields are filled in later, after main has the final qrels: main_commit and
qrels (row count and hash). They are NOT part of settings_sha256, so filling them in
cannot change a setting, and `record` refuses to write if the hash would change.

Commands:
  python -m src.ir.step17_config freeze
  python -m src.ir.step17_config record --main-commit <hash> --qrels data/eval/qrels_t1_llm.tsv
  python -m src.ir.step17_config check
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.ir.step17_report import DEPTH, GAIN_MIN, Spec

CONFIG_PATH = Path("data/eval/step17_config.json")
DATA_FILES = {
    "synonyms": "data/eval/synonyms.json",
    "split": "data/eval/split_t1.json",
    "queries": "data/eval/queries_t1.tsv",
    "corpus": "data/processed/regs.jsonl",
}

BEST_COMBO = Spec("hybrid", exp=(0.3, "all", True), pb=(1, 0.1, "bm25"), stem=True, prefix=True)
# (spec, role, compared against, note). Names come from Spec.name, so they match the dev report.
VARIANTS: list[tuple[Spec, str, str | None, str]] = [
    (Spec("bm25"), "baseline", None, ""),
    (Spec("hybrid"), "baseline", None, ""),
    (Spec("dense"), "baseline", None, ""),
    (Spec("bm25", exp=(0.5, "all", False)), "primary", "bm25",
     "P1: expansion with all groups; best bm25 expansion on dev (w=0.5)"),
    (BEST_COMBO, "primary", "hybrid",
     "P2: full best combination on dev (stem, prefix, expansion, part boost; no rerank)"),
    (Spec("hybrid", stem=True, prefix=True), "primary", "hybrid",
     "P3: stemmed BM25 half and BGE query prefix"),
    (Spec("bm25", stem=True), "secondary", "bm25", "descriptive"),
    (Spec("dense", prefix=True), "secondary", "dense", "descriptive"),
    (Spec("hybrid", rr="rrf"), "secondary", "hybrid", "descriptive; MiniLM cross-encoder, rrf fusion"),
    (Spec("bm25", exp=(0.5, "cfr", False)), "secondary", "bm25",
     "descriptive; expansion with CFR-definition groups only"),
    (Spec("hybrid", exp=(0.3, "cfr", False)), "secondary", "hybrid",
     "descriptive; CFR-only expansion on the BM25 half of hybrid (best CFR-only hybrid on dev)"),
    (Spec("hybrid", pb=(1, 0.1, "bm25"), stem=True, prefix=True), "secondary", "hybrid",
     "descriptive; P2 without expansion (was run on dev)"),
    (Spec("hybrid", exp=(0.3, "cfr", True), pb=(1, 0.1, "bm25"), stem=True, prefix=True),
     "secondary", "hybrid",
     "descriptive; P2 with CFR-only expansion (structure fixed by P2, NOT run on dev)"),
]
PARAMS = {
    "seed": 42,
    "depth": DEPTH,
    "metric": "nDCG@10, chunk level, unjudged as 0 and condensed",
    "holm_family": ["P1", "P2", "P3"],
    "bootstrap": {"n": 10000, "seed": 42, "level": 0.95, "p": "two-sided percentile"},
    "bm25": {"k1": 1.5, "b": 0.75},
    "hybrid": {"rrf_k": 60, "bm25_weight": 1.0, "dense_weight": 1.0},
    "dense_model": "BAAI/bge-small-en-v1.5",
    "reranker": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "top_n": 50, "max_length": 512},
    "gain_rule_on_dev": GAIN_MIN,
    "qrels_flavour": "LLM-assessed (claude-sonnet-5-5), not human grades",
    "sensitivity_exclude_heldout": ["q15", "q24", "q55"],
}


def spec_to_dict(spec: Spec) -> dict:
    """Spec as plain JSON data (tuples become lists)."""
    return {"base": spec.base, "exp": list(spec.exp) if spec.exp else None,
            "pb": list(spec.pb) if spec.pb else None, "rr": spec.rr,
            "stem": spec.stem, "prefix": spec.prefix}


def spec_from_dict(d: dict) -> Spec:
    """Inverse of spec_to_dict."""
    return Spec(d["base"], exp=tuple(d["exp"]) if d["exp"] else None,
                pb=tuple(d["pb"]) if d["pb"] else None, rr=d["rr"],
                stem=d["stem"], prefix=d["prefix"])


def file_sha256(path: str | Path) -> str:
    """SHA-256 of a file with CRLF turned into LF, so Windows checkouts hash the same."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def settings_hash(cfg: dict) -> str:
    """Hash over everything except the fill-in fields and the hash itself."""
    core = {k: cfg[k] for k in ("variants", "params", "files", "dev_report")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()


def build_config() -> dict:
    """The frozen config, fill-in fields left empty."""
    primary_ids = iter(("P1", "P2", "P3"))
    variants = []
    for spec, role, vs, note in VARIANTS:
        variants.append({"name": spec.name, "role": role, "vs": vs, "note": note,
                         "id": next(primary_ids) if role == "primary" else None,
                         "spec": spec_to_dict(spec)})
    cfg = {
        "frozen_from": "results/step17_dev.md (29 dev queries, seed 42 split)",
        "dev_report": "results/step17_dev.md",
        "variants": variants,
        "params": PARAMS,
        "files": {k: file_sha256(v) for k, v in DATA_FILES.items()},
        "main_commit": None,
        "qrels": {"path": "data/eval/qrels_t1_llm.tsv", "rows": None, "sha256": None},
    }
    cfg["settings_sha256"] = settings_hash(cfg)
    return cfg


def load_config(path: str | Path = CONFIG_PATH) -> dict:
    """Loads the config file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_config(cfg: dict) -> list[str]:
    """Returns a list of problems (empty if the config is intact and matches the files)."""
    problems = []
    if settings_hash(cfg) != cfg["settings_sha256"]:
        problems.append("settings_sha256 does not match the settings")
    for key, path in DATA_FILES.items():
        if file_sha256(path) != cfg["files"][key]:
            problems.append(f"{path} changed since the freeze")
    for v in cfg["variants"]:
        if spec_from_dict(v["spec"]).name != v["name"]:
            problems.append(f"variant name mismatch: {v['name']}")
    return problems


def record(cfg: dict, main_commit: str, qrels_path: str | Path) -> dict:
    """Fills in main_commit and the qrels row count and hash, leaving every setting alone."""
    before = settings_hash(cfg)
    rows = sum(1 for line in Path(qrels_path).read_text(encoding="utf-8").splitlines() if line.strip())
    out = json.loads(json.dumps(cfg))
    out["main_commit"] = main_commit
    out["qrels"] = {"path": str(qrels_path).replace("\\", "/"), "rows": rows,
                    "sha256": file_sha256(qrels_path)}
    if settings_hash(out) != before:
        raise RuntimeError("recording would change a frozen setting")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Freeze, record or check the Step 17 config.")
    ap.add_argument("action", choices=["freeze", "record", "check"])
    ap.add_argument("--main-commit")
    ap.add_argument("--qrels", default="data/eval/qrels_t1_llm.tsv")
    ap.add_argument("--path", default=str(CONFIG_PATH))
    a = ap.parse_args()
    path = Path(a.path)
    if a.action == "freeze":
        if path.exists():
            raise SystemExit(f"{path} exists; refusing to overwrite a frozen config")
        path.write_text(json.dumps(build_config(), indent=1) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    elif a.action == "record":
        if not a.main_commit:
            raise SystemExit("--main-commit is required")
        cfg = record(load_config(path), a.main_commit, a.qrels)
        path.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf-8")
        print(f"recorded main {a.main_commit}, qrels rows {cfg['qrels']['rows']}")
    else:
        problems = check_config(load_config(path))
        print("\n".join(problems) or "config intact")
        raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
