"""Build every dense index once and keep it in the shared store (data/cache/indexes, git-ignored).

    python scripts/build_indexes.py            # pull from the shared store, build what is missing, push
    python scripts/build_indexes.py --check    # only report, build nothing

Indexes: frozen E5b (bge-large with headings, device and medicine) and the default hybrid (bge-small). Files are
keyed by model and corpus hash, so a matching file is never rebuilt. The bge-large build takes about 40 minutes of
CPU on the first run; a demo PC that has the shared folder (or copies it) needs seconds.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.checker.retrieval import build_retriever, module_chunks  # noqa: E402
from src.checker.settings import RetrievalSettings  # noqa: E402
from src.rag import indexes  # noqa: E402


def main() -> int:
    """Pull, build what is missing, push, report. Returns 0 when every required file exists."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only, build nothing")
    args = ap.parse_args()
    print(f"shared store: {indexes.shared_dir()}")
    for path in indexes.pull():
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
    for path in indexes.push():
        print(f"saved to shared store: {path.name}")
    todo = indexes.missing()
    for path in todo:
        print(f"MISSING: {path}")
    print("all indexes present" if not todo else "some indexes are missing")
    return 1 if todo else 0


if __name__ == "__main__":
    raise SystemExit(main())
