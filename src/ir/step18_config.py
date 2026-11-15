"""Frozen Step 18 retrieval config: E5b (stemmed BM25 + bge-large with query prefix and heading enrichment).

E5b = reciprocal rank fusion (k=60, equal weights) of
  - BM25 over a light-stemmed index of the chunk text, and
  - bge-large-en-v1.5 over chunk text with "21 CFR Part <part>, section <section>: <heading>. " prepended,
    queried with the BGE retrieval instruction.
Each query is searched in its own module's chunks (device or medicine), to depth 50.

E5b was SELECTED on 5-fold cross-validation over the 57 answerable queries (results/step18_experiments.md),
so cross-validation numbers are optimistic. The fresh set (data/eval/fresh_candidates.csv) is the
honest test and is scored once, after this file exists.

Load it:
    from src.ir.step18_config import load_system
    retrievers = load_system()          # {"device": Retriever, "medicine": Retriever}
    hits = retrievers["medicine"].search("tamper-evident packaging", k=10)

Rebuild the bge-large index cache (about 37 min of CPU, only needed when data/processed/dense_cache_*large*
is missing; the vectors are cached by chunk id and content hash):
    python -m src.ir.step18_config rebuild-cache

Other commands:  python -m src.ir.step18_config freeze | check | cache-status
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from src.ir.base import Retriever
from src.ir.dense import BGE_QUERY_PREFIX, _cache_paths, _corpus_fingerprint
from src.ir.eval import load_chunks
from src.ir.step17_config import file_sha256
from src.ir.step18_systems import MODELS, PLAIN_HYBRID, STEM_PREFIX_HYBRID, Context18, Sys18, enrich_chunk, experiments

CONFIG_PATH = Path("data/eval/step18_config.json")
CORPUS = "data/processed/regs.jsonl"
DATA_FILES = {
    "corpus": CORPUS,
    "cv_folds": "data/eval/cv_folds.json",
    "fresh_candidates": "data/eval/fresh_candidates.csv",
    "finetune_exclusions": "data/eval/finetune_exclusions.json",
    "abstain_split": "data/eval/abstain_split.json",
}
SELECTED_ID = "E5b"
ENRICHMENT_TEMPLATE = "21 CFR Part {part}, section {section}: {title}. {text}"


def system_to_dict(s: Sys18) -> dict:
    """A Sys18 as plain JSON data."""
    return {
        "name": s.name,
        "bm25": None if s.bm25 is None else {"stem": s.bm25[0], "heading_prepended": s.bm25[1]},
        "dense": [{"model": MODELS[m], "query_prefix": BGE_QUERY_PREFIX if p else "", "heading_prepended": e}
                  for m, p, e in s.dense],
        "medcpt": s.medcpt,
    }


def e5b() -> Sys18:
    """The frozen system, taken from the experiment list so the config cannot drift from the CV runs."""
    return next(e[3] for e in experiments() if e[0] == SELECTED_ID)


def cache_files(chunks_by_module: dict[str, list]) -> dict[str, dict[str, str]]:
    """Expected dense cache files (embeddings and ids) for every dense part of E5b, per module."""
    out: dict[str, dict[str, str]] = {}
    for module, chunks in chunks_by_module.items():
        for model, _prefix, enrich in e5b().dense:
            src = [enrich_chunk(c) for c in chunks] if enrich else chunks
            fp = _corpus_fingerprint([f"{c.chunk_id}:{c.hash}" for c in src])
            emb, meta = _cache_paths(fp, MODELS[model].replace("/", "_"))
            out.setdefault(module, {})[MODELS[model]] = str(emb).replace("\\", "/")
            out[module][MODELS[model] + " (ids)"] = str(meta).replace("\\", "/")
    return out


def _chunks_by_module() -> dict[str, list]:
    chunks = load_chunks(CORPUS)
    return {m: [c for c in chunks if c.module == m] for m in ("device", "medicine")}


def settings_hash(cfg: dict) -> str:
    """SHA-256 over the system, comparators, parameters, data hashes and cache names."""
    core = {k: cfg[k] for k in ("system", "comparators", "parameters", "data_files", "cache_files")}
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()


def build_config() -> dict:
    """The frozen config (reads the CV evidence for E5b from results/step18_summary.json)."""
    summary = json.loads(Path("results/step18_summary.json").read_text(encoding="utf-8"))
    keep = ("exp_id", "base", "decision", "gain_ndcg", "gain_cond", "gain_recall20", "ci_lo", "ci_hi",
            "folds_won", "k", "top2_ndcg", "wo_ndcg", "unj10")
    evidence = [{k: r[k] for k in keep} for r in summary if r["exp_id"] == SELECTED_ID]
    cfg = {
        "name": SELECTED_ID,
        "frozen_after": "18d, before the fresh set and the abstention test split were scored",
        "system": system_to_dict(e5b()),
        "comparators": {"plain hybrid": system_to_dict(PLAIN_HYBRID),
                        "hybrid+stem+prefix": system_to_dict(STEM_PREFIX_HYBRID)},
        "parameters": {"fusion": {"type": "rrf", "k": 60, "weights": "equal", "fetch_k": "max(3k, 50)"},
                       "enrichment_template": ENRICHMENT_TEMPLATE, "depth": 50,
                       "modules": "each query is searched in its own module's chunks",
                       "bm25": {"k1": 1.5, "b": 0.75, "index": "light stemming, stopwords removed"}},
        "selected_on": {
            "method": "5-fold stratified cross-validation, 57 answerable queries, seed 42",
            "rule": "gain above 0.01 on both nDCG@10 lists, at least 3 of 5 folds won, survives leave-top-2-out",
            "caveat": "chosen among about 20 ideas on these queries; CV numbers are optimistic and the fresh set "
                      "is the honest test",
            "cv_rows": evidence},
        "data_files": {k: file_sha256(v) for k, v in DATA_FILES.items()},
        "cache_files": cache_files(_chunks_by_module()),
        "how_to_load": "from src.ir.step18_config import load_system; load_system()",
        "how_to_rebuild_cache": "python -m src.ir.step18_config rebuild-cache  (about 37 min of CPU)",
    }
    cfg["settings_sha256"] = settings_hash(cfg)
    return cfg


def load_config(path: str | Path = CONFIG_PATH) -> dict:
    """Reads the config file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_config(cfg: dict) -> list[str]:
    """Problems (empty when the hash, the data files and the system all match)."""
    problems = []
    if settings_hash(cfg) != cfg["settings_sha256"]:
        problems.append("settings_sha256 does not match the settings")
    for key, path in DATA_FILES.items():
        if file_sha256(path) != cfg["data_files"][key]:
            problems.append(f"{path} changed since the freeze")
    if cfg["system"] != system_to_dict(e5b()):
        problems.append("the E5b definition in step18_systems.py differs from the frozen system")
    if cfg["cache_files"] != cache_files(_chunks_by_module()):
        problems.append("expected cache file names differ (chunk ids, hashes or enrichment changed)")
    return problems


def load_system(chunks: list | None = None) -> dict[str, Retriever]:
    """Builds the frozen E5b retriever for each module (embeds only if the cache is missing)."""
    cfg = load_config()
    bad = check_config(cfg)
    if bad:
        raise RuntimeError("frozen config does not match the repository: " + "; ".join(bad))
    chunks = chunks if chunks is not None else load_chunks(CORPUS)
    return {m: Context18([c for c in chunks if c.module == m]).build(e5b()) for m in ("device", "medicine")}


def cache_status() -> dict[str, bool]:
    """Whether each expected dense cache file exists."""
    cfg = load_config()
    return {path: Path(path).exists() for files in cfg["cache_files"].values() for path in files.values()}


def main() -> None:
    ap = argparse.ArgumentParser(description="Freeze, check or rebuild the Step 18 E5b config.")
    ap.add_argument("action", choices=["freeze", "check", "cache-status", "rebuild-cache"])
    a = ap.parse_args()
    if a.action == "freeze":
        if CONFIG_PATH.exists():
            raise SystemExit(f"{CONFIG_PATH} exists; refusing to overwrite a frozen config")
        cfg = build_config()
        CONFIG_PATH.write_text(json.dumps(cfg, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {CONFIG_PATH}, settings_sha256 {cfg['settings_sha256']}")
    elif a.action == "check":
        problems = check_config(load_config())
        print("\n".join(problems) or "config intact")
        raise SystemExit(1 if problems else 0)
    elif a.action == "cache-status":
        for path, ok in cache_status().items():
            print(("present " if ok else "MISSING ") + path)
    else:
        load_system()
        print("cache ready:", all(cache_status().values()))


if __name__ == "__main__":
    main()
