import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

CONDS = ("clean", "moderate", "hard", "hard_original", "very_hard")


def work(job):
    import cv2
    import numpy as np
    from PIL import Image

    from src.cv.barcode_blind import decode_barcodes_blind, locate_barcode_candidates
    from src.cv.preprocess import find_label_corners, rectify_label

    p = Path(job)
    truth = json.loads(p.with_suffix(".json").read_text())
    img = np.asarray(Image.open(p).convert("RGB"))
    out = {"cond": truth["condition"], "seed": p.parts[-3], "name": p.stem}
    # candidate recall: does any candidate cover the true barcode slot centre
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    centre = np.asarray(truth["slot_quads_px"]["udi"]).mean(axis=0)
    cands = locate_barcode_candidates(gray)
    out["cand_rank"] = next(
        (i for i, b in enumerate(cands) if cv2.pointPolygonTest(b, (float(centre[0]), float(centre[1])), False) >= 0),
        None,
    )
    out["n_cands"] = len(cands)
    t = time.time()
    res, _, how = decode_barcodes_blind(img, whole_image_fallback=False)
    out["photo_nofallback"] = [len(res) == 1 and res[0].parsed == truth["barcode_ais"], how, round(time.time() - t, 2)]
    t = time.time()
    res, _, how = decode_barcodes_blind(img)
    out["photo"] = [len(res) == 1 and res[0].parsed == truth["barcode_ais"], how, round(time.time() - t, 2)]
    c = find_label_corners(img)
    out["label"] = c is not None
    if c is not None:
        rect, _ = rectify_label(img, c)
        t = time.time()
        res, _, how = decode_barcodes_blind(rect)
        out["rect"] = [len(res) == 1 and res[0].parsed == truth["barcode_ais"], how, round(time.time() - t, 2)]
    return out


if __name__ == "__main__":
    jobs = [
        str(p) for ds in ("dev42", "dev43") for c in CONDS
        for p in sorted((Path("data/synthetic") / ds / c).glob("*.png"))
    ]
    with ProcessPoolExecutor(int(sys.argv[2])) as ex:
        res = list(ex.map(work, jobs))
    json.dump(res, open(sys.argv[1], "w"))
    for seed in ("dev42", "dev43"):
        for c in CONDS:
            rs = [r for r in res if r["cond"] == c and r["seed"] == seed]
            line = [f"{seed} {c} n={len(rs)}"]
            line.append("cand_found=%d" % sum(r["cand_rank"] is not None for r in rs))
            for k in ("photo_nofallback", "photo", "rect"):
                got = [r[k] for r in rs if k in r]
                line.append(f"{k}={sum(g[0] for g in got)}/{len(got)} t_med={sorted(g[2] for g in got)[len(got) // 2] if got else 0}")
            either = sum((r.get("rect", [False])[0] or r["photo"][0]) for r in rs)
            line.append(f"either={either}")
            print(" ".join(line))
            print("   fails:", [(r["name"][11:14], r["cand_rank"]) for r in rs if not r["photo"][0]])
