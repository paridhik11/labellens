import json
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REFS = Path(sys.argv[1])


def work(job):
    import numpy as np
    from PIL import Image

    from src.cv.eval_v2 import _quad_box, box_iou
    from src.cv.preprocess import find_label_corners, find_label_corners_fallback, rectify_label
    from src.cv.symbols import detect_symbols_blind

    p = Path(job)
    t = json.loads(p.with_suffix(".json").read_text())
    img = np.asarray(Image.open(p).convert("RGB"))
    c = find_label_corners(img)
    if c is None:
        c = find_label_corners_fallback(img)
    rect, fwd = rectify_label(img, c)
    inv = np.linalg.inv(fwd)
    from src.cv.extract import project_box

    out = {"case": t["case"], "seed": p.parts[-4], "matched": 0, "present": len(t["present_symbols"]),
           "absent_reported": 0, "absent": 0}
    present = {s["name"]: _quad_box(s["quad_px"]) for s in t["present_symbols"]}
    absent = [n for n in t["expected_symbols"] if n not in present]
    out["absent"] = len(absent)
    for s in detect_symbols_blind(rect, reference_dir=REFS):
        box = project_box(s.bbox, inv, (img.shape[1], img.shape[0]))
        if s.name in absent:
            out["absent_reported"] += 1
        elif box_iou(box, present[s.name]) >= 0.5:
            out["matched"] += 1
    return out


if __name__ == "__main__":
    from PIL import Image, ImageDraw

    from src.cv.symbols import REFERENCE_DIR
    from src.gen.alt_symbols import draw_alt_symbol

    REFS.mkdir(parents=True, exist_ok=True)
    for f in REFERENCE_DIR.glob("*.png"):
        shutil.copy(f, REFS / f.name)
    for name in ("manufacturer", "expiry"):
        im = Image.new("L", (94, 94), 255)
        draw_alt_symbol(ImageDraw.Draw(im), name, (0, 0, 94, 94))
        im.save(REFS / f"test_{name}_alt.png")
    jobs = [str(p) for ds in ("neg42", "neg43") for p in sorted((Path("data/synthetic") / ds).rglob("*.png"))
            if p.parts[-3] in ("alt_style", "missing_expiry", "missing_manufacturer", "wrong_symbol")]
    with ProcessPoolExecutor(5) as ex:
        res = list(ex.map(work, jobs))
    for seed in ("neg42", "neg43"):
        for case in ("alt_style", "missing_expiry", "missing_manufacturer", "wrong_symbol"):
            rs = [r for r in res if r["case"] == case and r["seed"] == seed]
            print(seed, case, "matched %d/%d" % (sum(r["matched"] for r in rs), sum(r["present"] for r in rs)),
                  "absent reported %d/%d" % (sum(r["absent_reported"] for r in rs), sum(r["absent"] for r in rs)))
