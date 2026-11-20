"""Build every dense index once and keep it in the shared store (data/cache/indexes, git-ignored).

    python scripts/build_indexes.py            # pull from the shared store, build what is missing, push
    python scripts/build_indexes.py --check    # only report, build nothing

Indexes: frozen E5b (bge-large with headings, device and medicine) and the default hybrid (bge-small). Files are
keyed by model and corpus hash, so a matching file is never rebuilt. The bge-large build takes about 40 minutes of
CPU on the first run; a demo PC that has the shared folder (or copies it) needs seconds.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.checker.retrieval import build_retriever, module_chunks  # noqa: E402
from src.checker.settings import RetrievalSettings  # noqa: E402
from src.rag import indexes  # noqa: E402


def medicine_reference_files() -> list[Path]:
    """Every dense cache file in data/processed (the reference-product indexes of the public medicine mode live there too)."""
    return sorted(indexes.LOCAL_DIR.glob("dense_cache_*"))


def pull_all() -> list[Path]:
    """Copy every dense cache file the shared store has and this checkout lacks (includes the medicine reference ones)."""
    store = indexes.shared_dir()
    copied = []
    for source in sorted(store.glob("dense_cache_*")) if store.exists() else []:
        target = indexes.LOCAL_DIR / source.name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target)
    return copied


def warm_medicine() -> None:
    """Build the public medicine mode indexes (ten product documents and the 147 product chunks) when not cached."""
    from src.api.medicine import MedicineService

    service = MedicineService()
    print("building the medicine reference indexes (small) ...")
    service.matcher._load()
    service.scoped_retriever(next(iter(service.catalog.products)))


def main() -> int:
    """Pull, build what is missing, push, report. Returns 0 when every required file exists."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only, build nothing")
    args = ap.parse_args()
    print(f"shared store: {indexes.shared_dir()}")
    for path in pull_all() + indexes.pull():
        print(f"copied from shared store: {path.name}")
    todo = indexes.missing()
    print(f"required {len(indexes.required_files())} files, missing {len(todo)}")
    if todo and not args.check:
        if any("bge-large" in p.name for p in todo):
            from src.ir.step18_config import load_system

            print("building frozen E5b (bge-large), this is the slow part ...")
            load_system()
        if any("bge-small" in p.name for p in todo):
            for module in indexes.MODULES:
                print(f"building bge-small for {module} ...")
                build_retriever(RetrievalSettings(method="hybrid_rrf", module=module), module_chunks(module))
    if not args.check:
        try:
            warm_medicine()
        except Exception as error:  # models not installed or offline cache incomplete: reported, not fatal here
            print(f"medicine reference indexes not built: {type(error).__name__}: {error}")
    for path in indexes.push(indexes.required_files() + medicine_reference_files()):
        print(f"saved to shared store: {path.name}")
    todo = indexes.missing()
    for path in todo:
        print(f"MISSING: {path}")
    print("all indexes present" if not todo else "some indexes are missing")
    return 1 if todo else 0


if __name__ == "__main__":
    raise SystemExit(main())
