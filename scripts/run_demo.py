"""One command to start the whole product on a demo PC (Step 25).

    python scripts/run_demo.py                 # indexes, seed, API, warm-up, prints the URL
    python scripts/run_demo.py --port 8010 --fresh

What it does, in order:
 1. checks the environment (which of the real extractor, renderer, retrieval models and the local LLM are available)
 2. makes sure the dense indexes exist: copies them from the shared store, builds what is missing
    (the bge-large build takes about 40 minutes of CPU the first time; a PC with the shared folder needs seconds)
 3. seeds the demo database (users, an example product with a confirmed change and a draft ready for approval, and
    the golden package: product, template, label version from a rendered label, and a confirmed change)
 4. picks the checker retrieval: the frozen E5b system if it loads and a check stays under 10 s, else plain hybrid
 5. starts the API, serves a UI build when the repo has one (ui/dist, ui/out or ui/build), warms the models, prints URLs

Nothing is published or approved by this script. The demo reviewer does that live (or `scripts/demo_e2e.py` does).
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.chdir(ROOT)

E5B_CHECK_BUDGET_S = 10.0


def have(module: str) -> bool:
    """True when a module can be imported in this environment."""
    return importlib.util.find_spec(module) is not None


TESSERACT_DIRS = (r"C:\Program Files\Tesseract-OCR", r"C:\Program Files (x86)\Tesseract-OCR")


def ensure_tesseract(dirs: tuple[str, ...] = TESSERACT_DIRS) -> bool:
    """Make `tesseract` findable for the photo scan: add a standard Windows install folder to PATH when needed.

    Returns True when the program is on PATH (already, or after adding a folder). The photo scan reads text with it
    (`src/cv/ocr_vote.py`), so without it every public photo scan fails.
    """
    if shutil.which("tesseract"):
        return True
    for folder in dirs:
        if (Path(folder) / "tesseract.exe").exists():
            os.environ["PATH"] = os.environ.get("PATH", "") + os.pathsep + folder
            return shutil.which("tesseract") is not None
    return False


def check_environment() -> dict[str, bool]:
    """Report what the demo can do on this machine. Missing parts degrade a stage, they do not stop the start."""
    caps = {
        "real extractor (opencv, zxing-cpp, rapidocr)": all(have(m) for m in ("cv2", "zxingcpp", "rapidocr_onnxruntime")),
        "label renderer (reportlab, zxing-cpp)": all(have(m) for m in ("reportlab", "zxingcpp")),
        "PDF pages (pypdfium2)": have("pypdfium2"),
        "retrieval models (sentence-transformers)": have("sentence_transformers"),
    }
    print(f"python {sys.version.split()[0]} in {sys.prefix}")
    if ensure_tesseract():
        print(f"  ok      Tesseract found ({shutil.which('tesseract')}): the public photo scan can read text")
    else:
        print("  MISSING Tesseract not found: public photo scans will fail (install it, or use Type the name)")
    for name, ok in caps.items():
        print(f"  {'ok     ' if ok else 'MISSING'} {name}")
    if sys.version_info[:2] != (3, 12):
        print("  warning: the project is tested on Python 3.12")
    try:
        import requests

        requests.get("http://127.0.0.1:11434/api/tags", timeout=2).raise_for_status()
        print("  ok      Ollama is running (the optional AI answer can use a model)")
    except Exception:
        print("  note    Ollama is not running: the AI answer falls back to the extractive passages")
    return caps


# The retrieval models (frozen E5b and default hybrid) and the sentence reranker of the default extractive display
# (cross-encoder/ms-marco-MiniLM-L-6-v2, 87 MB, `src/rag/rerank.py`; without it the display falls back to chunk quotes).
MODELS = ("BAAI/bge-large-en-v1.5", "BAAI/bge-small-en-v1.5", "cross-encoder/ms-marco-MiniLM-L-6-v2")


def ensure_models() -> bool:
    """Download any retrieval model that is not in the local Hugging Face cache (once; the app then runs offline).

    src/ir loads models from the local cache only (HF_HUB_OFFLINE=1), so a fresh PC must have them before the
    indexes are built. Returns False when a model is missing and cannot be downloaded.
    """
    try:
        from huggingface_hub import snapshot_download, try_to_load_from_cache
    except ImportError:
        print("models: huggingface_hub is not installed, cannot check the model cache")
        return False
    ok = True
    for name in MODELS:
        cached = try_to_load_from_cache(name, "config.json")
        if isinstance(cached, str):
            print(f"models: {name} is cached")
            continue
        print(f"models: downloading {name} from Hugging Face (one time, up to 1.3 GB) ...", flush=True)
        try:
            snapshot_download(name)
        except Exception as error:
            print(f"models: could not download {name}: {type(error).__name__}: {error}")
            ok = False
    return ok


def sync_indexes(skip: bool) -> bool:
    """Copy or build every dense index; returns False when some are still missing afterwards."""
    if skip:
        print("indexes: skipped (--skip-indexes)")
        return True
    import build_indexes

    sys.argv = ["build_indexes"]
    started = time.time()
    code = build_indexes.main()
    print(f"indexes: {'all present' if code == 0 else 'SOME MISSING'} ({time.time() - started:.0f} s)")
    return code == 0


def choose_retrieval() -> str:
    """The frozen E5b system only if it loads from the cache and a check stays under 10 s; else plain hybrid RRF."""
    try:
        from src.checker.retrieval import default_retriever, e5b_system
        from src.checker.settings import RetrievalSettings

        started = time.time()
        e5b_system()
        load = time.time() - started
        retriever = default_retriever(RetrievalSettings(method="e5b", module="device"))
        started = time.time()
        retriever.search("expiration date format on the label", k=10)
        search = time.time() - started
        print(f"checker retrieval: E5b loaded in {load:.1f} s, one retrieval {search:.2f} s")
        if load > 120 or search > E5B_CHECK_BUDGET_S:
            print("checker retrieval: too slow, using plain hybrid RRF")
            return "hybrid_rrf"
        return "e5b"
    except Exception as error:
        print(f"checker retrieval: E5b unavailable ({type(error).__name__}: {error}), using plain hybrid RRF")
        return "hybrid_rrf"


def find_ui() -> Path | None:
    """A built UI (ui/dist, ui/out or ui/build), else the static UI in ui/ itself, else None."""
    for name in ("dist", "out", "build"):
        folder = ROOT / "ui" / name
        if (folder / "index.html").is_file():
            return folder
    if (ROOT / "ui" / "index.html").is_file():
        return ROOT / "ui"
    return None


def warm_and_seed(base: str, golden: bool, caps: dict[str, bool]) -> None:
    """After the server listens: load the models with real requests, then seed the golden package through the API."""
    import requests

    import demo_flow as f

    for _ in range(120):
        try:
            if requests.get(base + "/health", timeout=2).ok:
                break
        except Exception:
            time.sleep(0.5)
    for name, call in (
        ("medicine match", lambda: requests.post(base + "/public/match", json={"product_name": "Omeprazole"}, timeout=300)),
        ("public answer", lambda: requests.post(base + "/public/ask", json={
            "question": "what are the warnings", "product_id": "med_346141b5"}, timeout=300)),
        ("professional answer", lambda: requests.post(base + "/ask", json={"question": "date format on a label"}, timeout=300)),
    ):
        started = time.time()
        try:
            print(f"warm-up: {name} {call().status_code} in {time.time() - started:.1f} s", flush=True)
        except Exception as error:
            print(f"warm-up: {name} failed ({error})", flush=True)
    if not golden:
        return
    api = f.Api(base)
    existing = api.ok("GET", "/products")["items"]
    if any(p["record"]["name"] == "Golden Pump (demo)" for p in existing):
        print("golden package: already seeded")
        return
    runner = f.Runner(api)
    work = f.new_workdir()
    pdf = work / "golden_label.pdf"
    steps = [("golden product and template", lambda: f.register_golden(runner))]
    if caps["label renderer (reportlab, zxing-cpp)"]:
        steps.append(("golden label PDF", lambda: str(f.render_golden_pdf(pdf))))
        if caps["real extractor (opencv, zxing-cpp, rapidocr)"] and caps["PDF pages (pypdfium2)"]:
            steps += [("golden label version (upload and extract)", lambda: f.upload_and_extract(runner, pdf)),
                      ("golden confirmed extraction", lambda: f.confirm_fields(runner, f.golden_truth_fields(f.GOLDEN))),
                      ("golden change (lot)", lambda: f.make_change(runner)),
                      ("golden change confirmed", lambda: f.confirm_change(runner))]
    for name, run in steps:
        if not runner.stage("seed: " + name, run):
            break
    demo_dir = ROOT / "data" / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    if pdf.exists():
        shutil.copy2(pdf, demo_dir / "golden_label.pdf")
        print(f"golden package: label PDF kept at {demo_dir / 'golden_label.pdf'}")


def main() -> int:
    """Prepare everything, then serve until Ctrl+C."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--fresh", action="store_true", help="delete the demo database and stored files first")
    ap.add_argument("--skip-indexes", action="store_true", help="do not copy or build dense indexes")
    ap.add_argument("--no-golden", action="store_true", help="do not seed the golden package")
    args = ap.parse_args()

    caps = check_environment()
    have_models = caps["retrieval models (sentence-transformers)"] and (args.skip_indexes or ensure_models())
    indexes_ok = sync_indexes(args.skip_indexes) if have_models else False
    method = choose_retrieval() if indexes_ok or args.skip_indexes else "hybrid_rrf"

    data = ROOT / "data" / "api"
    db = data / "demo.db"
    if args.fresh:
        db.unlink(missing_ok=True)
        for sub in ("uploads", "artifacts"):
            shutil.rmtree(data / sub, ignore_errors=True)
    base = f"http://{args.host}:{args.port}"
    os.environ.update({
        "LABELLENS_DB_URL": f"sqlite:///{db.as_posix()}", "LABELLENS_PUBLIC_BASE_URL": base,
        "LABELLENS_CHECKER_RETRIEVAL": method, "LABELLENS_FILES_DIR": str(data),
    })
    data.mkdir(parents=True, exist_ok=True)

    import uvicorn

    from src.api.main import create_app

    app = create_app()
    ui = find_ui()
    if ui is not None:
        from fastapi.staticfiles import StaticFiles

        app.mount("/ui", StaticFiles(directory=ui, html=True), name="ui")
        # The static UI reads its mock responses from /src/api/mock (CONFIG.mode "mock" in ui/js/data.js).
        mock_dir = ROOT / "src" / "api" / "mock"
        if ui == ROOT / "ui" and mock_dir.is_dir():
            app.mount("/src/api/mock", StaticFiles(directory=mock_dir), name="ui-mocks")
    threading.Thread(target=warm_and_seed, args=(base, not args.no_golden, caps), daemon=True).start()
    print("\n" + "=" * 64)
    print(f"LabelLens demo   {base}")
    print(f"  API docs                {base}/docs")
    print(f"  public medicine page    {base}/public/medicine")
    print(f"  UI                      {base + '/ui/' if ui else 'no UI in the repo (ui/index.html); use /docs'}")
    print(f"  checker retrieval       {method}")
    print("  demo users (X-User-Id)  usr_demo_editor, usr_demo_reviewer, usr_demo_admin")
    print(f"  check everything        python scripts/demo_e2e.py --base {base}")
    print("=" * 64 + "\n", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
