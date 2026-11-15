import json, sys, time
from pathlib import Path
import cv2, numpy as np, zxingcpp
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
def work(p):
    from src.cv.barcode import parse_gs1
    from src.cv.preprocess import find_label_corners, rectify_label
    DM = zxingcpp.BarcodeFormat.DataMatrix
    def dec(g):
        for r in zxingcpp.read_barcodes(np.ascontiguousarray(g), formats=DM):
            if r.content_type == zxingcpp.ContentType.GS1:
                try: return parse_gs1(r.bytes.decode("latin-1"))
                except ValueError: pass
        return None
    def wiener(g, sigma, k=0.02):
        f = np.fft.rfft2(g.astype(np.float32))
        fy = np.fft.fftfreq(g.shape[0])[:, None]; fx = np.fft.rfftfreq(g.shape[1])[None, :]
        h = np.exp(-2 * np.pi**2 * sigma**2 * (fx**2 + fy**2))
        return np.clip(np.fft.irfft2(f * h / (h**2 + k), s=g.shape), 0, 255).astype(np.uint8)
    p = Path(p)
    truth = json.loads(p.with_suffix(".json").read_text())["barcode_ais"]
    img = np.asarray(Image.open(p).convert("RGB"))
    g0 = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    c = find_label_corners(img)
    out = {"label": c is not None}
    srcs = {"orig": g0}
    if c is not None: srcs["rect"] = cv2.cvtColor(rectify_label(img, c)[0], cv2.COLOR_RGB2GRAY)
    for sn, g in srcs.items():
        for sig in (1.8, 1.4, 1.0, 0.6):
            t = time.time()
            r = dec(cv2.resize(wiener(g, sig), None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
            out[(sn, sig)] = (r == truth, round(time.time() - t, 2))
    return out
if __name__ == "__main__":
    for cond in sys.argv[1:]:
        ps = [str(p) for ds in ("dev42", "dev43") for p in sorted((Path("data/synthetic")/ds/cond).glob("*.png"))]
        with ProcessPoolExecutor(8) as ex: res = list(ex.map(work, ps))
        keys = [k for k in res[0] if k != "label"] if True else []
        allk = sorted({k for r in res for k in r if k != "label"}, key=str)
        print(cond, "n", len(res), "label found", sum(r["label"] for r in res))
        for k in allk: print("  ", k, sum(r.get(k, (False,))[0] for r in res), "t~", np.median([r[k][1] for r in res if k in r]))
        for grp in ("orig", "rect"):
            print("  any", grp, sum(any(r.get((grp, s), (False,))[0] for s in (1.8, 1.4, 1.0, 0.6)) for r in res))
        print("  any all", sum(any(v[0] for k, v in r.items() if k != "label") for r in res))
