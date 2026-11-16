"""Shared store for built dense indexes, outside any worktree and ignored by git.

Dense embedding files are named by model and corpus content hash (``dense_cache_<model>_<hash>``), so a file is
valid exactly when its name is wanted. The shared folder (default ``<main checkout>/data/cache/indexes``, or
``LABELLENS_INDEX_DIR``) holds one copy of each. ``pull`` copies missing files into ``data/processed`` (where
``src/ir`` looks), ``push`` copies new ones back. Nothing is rebuilt when the hash matches. ``src/ir`` is not edited.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from src.checker.retrieval import module_chunks
from src.ir.dense import _cache_paths, _corpus_fingerprint
from src.ir.step18_config import cache_files

LOCAL_DIR = Path("data/processed")
SMALL_MODEL = "BAAI_bge-small-en-v1.5"
MODULES = ("device", "medicine")


def shared_dir() -> Path:
    """LABELLENS_INDEX_DIR, else data/cache/indexes of the main checkout (found through git), else of this folder."""
    env = os.environ.get("LABELLENS_INDEX_DIR")
    if env:
        return Path(env)
    try:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True,
                                text=True, check=True).stdout.strip()
        return Path(common).parent / "data" / "cache" / "indexes"
    except (OSError, subprocess.CalledProcessError):
        return Path("data/cache/indexes").resolve()


def required_files() -> list[Path]:
    """Every dense cache file the frozen E5b system and the default hybrid (bge-small) need, as local paths."""
    chunks = {m: list(module_chunks(m).values()) for m in MODULES}
    files = [Path(p) for per_module in cache_files(chunks).values() for p in per_module.values()]
    for m in MODULES:
        fp = _corpus_fingerprint([f"{c.chunk_id}:{c.hash}" for c in chunks[m]])
        files += list(_cache_paths(fp, SMALL_MODEL, LOCAL_DIR))
    return files


def pull(files: list[Path] | None = None, store: Path | None = None) -> list[Path]:
    """Copy files that the shared store has and the local folder lacks. Never overwrites. Returns what was copied."""
    store = store or shared_dir()
    copied = []
    for path in files if files is not None else required_files():
        source = store / path.name
        if source.exists() and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, path)
            copied.append(path)
    return copied


def push(files: list[Path] | None = None, store: Path | None = None) -> list[Path]:
    """Copy local files into the shared store when it lacks them. Never overwrites. Returns what was copied."""
    store = store or shared_dir()
    copied = []
    for path in files if files is not None else required_files():
        if path.exists() and not (store / path.name).exists():
            store.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, store / path.name)
            copied.append(path)
    return copied


def missing(files: list[Path] | None = None) -> list[Path]:
    """Required files that do not exist locally."""
    return [p for p in (files if files is not None else required_files()) if not p.exists()]
