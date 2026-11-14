"""Run the extractor exactly as it was at an older git commit, for before and after tables.

The code of the requested commit is exported with ``git archive`` into a
temporary folder and executed in a separate Python process, so later edits to
``src/cv`` cannot change the "before" numbers. Results are cached per commit
and dataset under ``<dataset>/.ref_cache``.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
# Commit before the hard blur and noise were reduced and before barcode-slot recovery.
OLD_REF = "ecc9869"
# Last commit of the parth-cv branch, the starting point of the cv-fixes work.
START_REF = "05869b6"

_RUNNER = '''
import json, sys
from concurrent.futures import ProcessPoolExecutor


def work(args):
    path, full = args
    import numpy as np
    from PIL import Image
    from src.cv import barcode as B
    from src.cv.preprocess import find_label_corners, rectify_label
    out = {"image": path}
    with Image.open(path) as photo:
        img = np.asarray(photo.convert("RGB"))
    results, _ = B.decode_barcodes(img)
    method = "original_image"
    corners = find_label_corners(img)
    if not results and corners is not None:
        rect, _ = rectify_label(img, corners)
        results, _ = B.decode_barcodes(rect)
        method = "rectified_image"
        if not results and hasattr(B, "decode_barcode_slot"):
            results, _ = B.decode_barcode_slot(rect)
            method = "template_slot"
    out["barcode_parsed"] = [item.parsed for item in results]
    out["barcode_method"] = method if results else None
    out["corners"] = None if corners is None else np.asarray(corners).tolist()
    if full:
        from src.cv.extract import extract_label
        try:
            out["extraction"] = extract_label(path).model_dump()
        except Exception as error:
            out["extraction_error"] = f"{type(error).__name__}: {error}"
    return out


if __name__ == "__main__":
    job = json.loads(open(sys.argv[1], encoding="utf-8").read())
    with ProcessPoolExecutor(max_workers=job["workers"]) as pool:
        records = list(pool.map(work, [(path, job["full"]) for path in job["images"]]))
    open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(records))
'''


def run_ref(
    ref: str,
    dataset_dir: Path,
    *,
    conditions: tuple[str, ...] | None = None,
    full: bool = False,
    workers: int = 6,
) -> dict[str, dict[str, Any]]:
    """Return per-image records produced by the code at ``ref``, keyed by manifest image path.

    Every record has the barcode-only pipeline of that commit (whole image,
    then rectified label, then the template slot if that commit has it) and
    the detected label corners. With ``full`` it also has ``extract_label``.
    """
    dataset_dir = dataset_dir.resolve()
    manifest_bytes = (dataset_dir / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    images = [
        entry["image"] for entry in manifest["files"]
        if conditions is None or entry["image"].split("/")[0] in conditions
    ]
    key = hashlib.sha256(
        manifest_bytes + json.dumps([ref, full, images]).encode("utf-8")
    ).hexdigest()[:16]
    cache_path = dataset_dir / ".ref_cache" / f"{ref}_{key}.json"
    if cache_path.is_file():
        return json.loads(cache_path.read_text(encoding="utf-8"))
    archive = subprocess.run(
        ["git", "archive", "--format=zip", ref, "src"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    with TemporaryDirectory(prefix="labellens_ref_") as temporary:
        zipfile.ZipFile(io.BytesIO(archive)).extractall(temporary)
        Path(temporary, "_ref_runner.py").write_text(_RUNNER, encoding="utf-8")
        job = {"images": [str(dataset_dir / image) for image in images], "full": full, "workers": workers}
        Path(temporary, "job.json").write_text(json.dumps(job), encoding="utf-8")
        subprocess.run(
            [sys.executable, "_ref_runner.py", "job.json", "out.json"], cwd=temporary, check=True
        )
        records = json.loads(Path(temporary, "out.json").read_text(encoding="utf-8"))
    result = {image: record for image, record in zip(images, records, strict=True)}
    cache_path.parent.mkdir(exist_ok=True)
    cache_path.write_text(json.dumps(result), encoding="utf-8")
    return result
