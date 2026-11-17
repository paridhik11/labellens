"""Step 25b: run the REAL print verification (real renderer, real extractor) and count what it gets wrong.

    python scripts/step25b_print_eval.py --n 8      # writes results/step25b_print_verify.md

Needs the CV libraries (opencv, zxing-cpp, rapidocr, reportlab) and pypdfium2. Everything goes through the API code
(in-process TestClient): register a product and template, generate a label with the real renderer, re-check it, approve
it, then verify photos of it.

The photos are SYNTHETIC. The approved PDF is rasterised and degraded by the project's own photo simulator
(`src.gen.augment`, conditions clean, moderate, hard) with seeds 5000 and up. They are not photographs of a physical
print, and nothing here was tuned on them: no threshold or rule of the verifier, the extractor or the quality gate is
changed. Two kinds of photo, each with a known right answer:
- positive: a photo of the approved label itself. The right outcome is `match`.
- negative: a photo of a different generated label (another lot, so the barcode and the lot text differ).
  The right outcome is `mismatch`.
`rescan_needed` is never counted as a wrong answer by itself; it is the verifier asking for a better photo, and it is
reported separately (a positive that ends rescan_needed is "not decided", a negative that does is "missed" too).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONDITIONS = ("clean", "moderate", "hard")
RECORD = {
    "name": "Golden Pump", "model": "GP-100", "manufacturer": "Demo Labs", "manufacturer_address": "12 Demo Road",
    "udi_di": "00000000000000", "sterilization": "EO", "storage": "Store dry",
    "extra": {"lot": "LOT1", "expiry": "2030-06-30", "serial": "SN1"}, "intended_market": ["US"],
}
EDITOR, REVIEWER = {"X-User-Id": "usr_demo_editor"}, {"X-User-Id": "usr_demo_reviewer"}


def render_page(pdf_bytes: bytes):
    """Page 1 of a PDF as a PIL image at 300 dpi (the resolution the photo simulator expects)."""
    import pypdfium2

    document = pypdfium2.PdfDocument(pdf_bytes)
    image = document[0].render(scale=300 / 72).to_pil().convert("RGB")
    document.close()
    return image


def png(image) -> bytes:
    """PNG bytes of a PIL image."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def main() -> int:
    """Build two approved-style labels, photograph them under the simulator, verify, count, write the report."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=8, help="photos per condition and kind")
    ap.add_argument("--out", default="results/step25b_print_verify.md")
    args = ap.parse_args()
    work = Path(tempfile.mkdtemp(prefix="pv_eval_"))
    os.environ["LABELLENS_FILES_DIR"] = str(work)

    from fastapi.testclient import TestClient

    from src.api.main import create_app
    from src.api.store import add_label_version
    from src.gen.augment import augment_label_detailed

    template = json.loads((ROOT / "src" / "gen" / "templates" / "test_device.json").read_text(encoding="utf-8"))
    with TestClient(create_app("sqlite://", seed=True)) as client:
        def call(method: str, path: str, user=EDITOR, **kw):
            response = client.request(method, path, headers=user, **kw)
            return response

        def wait(response):
            job = call("GET", f"/jobs/{response.json()['job_id']}").json()
            assert job["state"] == "done", job
            return job

        pid = call("POST", "/products", json=RECORD).json()["product"]["product_id"]
        call("POST", f"/products/{pid}/templates", json={"size_mm": template["size_mm"], "background": None,
                                                         "slots": template["slots"]})
        with client.app.state.session_factory() as session:
            label_id = add_label_version(session, "usr_demo_editor", pid, "uploads/" + "a" * 64 + ".png").label_id

        def generate(lot: str) -> tuple[str, str, bytes]:
            made = call("POST", "/changes", json={"product_id": pid, "edits": [{"field": "lot", "new_value": lot}]}).json()
            decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in made["affected"]]
            call("POST", f"/changes/{made['change']['change_id']}/confirm",
                 json={"parse_confirmed": True, "decisions": decisions})
            started = call("POST", f"/changes/{made['change']['change_id']}/generate",
                           json={"label_id": label_id, "test_data": True})
            art = call("GET", wait(started)["result_url"]).json()
            pdf = (work / "artifacts" / f"{art['artifact_sha256']}.pdf").read_bytes()
            return art["version_id"], art["artifact_sha256"], pdf

        wrong_version, wrong_sha, wrong_pdf = generate("LOT3")  # the print of another lot (negatives)
        version, sha, pdf = generate("LOT2")  # the approved one, newest so approval is not superseded
        check = call("GET", wait(call("POST", f"/label-versions/{version}/recheck"))["result_url"]).json()
        if not check["passed"]:
            print(f"the approved label's own re-check did not pass: {check['findings']}")
            return 1
        approved = call("POST", f"/label-versions/{version}/reviews", user=REVIEWER, json={
            "decision": "approve", "artifact_sha256": sha, "check_id": check["check_id"]})
        assert approved.status_code == 201, approved.text

        rows = []
        for kind, source_pdf in (("positive", pdf), ("negative", wrong_pdf)):
            page = render_page(source_pdf)
            for condition in CONDITIONS:
                for i in range(args.n):
                    seed = 5000 + i
                    photo, *_ = augment_label_detailed(page, condition, seed)
                    sent = call("POST", f"/label-versions/{version}/print-verifications",
                                files={"photo": ("p.png", png(photo), "image/png")},
                                data={"condition": "clean_print_scan" if condition == "clean" else "phone_photo"})
                    job = call("GET", f"/jobs/{sent.json()['job_id']}").json()
                    if job["state"] != "done":
                        rows.append((kind, condition, seed, "job_failed", job.get("error", {}).get("error", ""), [], {}))
                        print(kind, condition, seed, "JOB FAILED", job.get("error"), flush=True)
                        continue
                    body = call("GET", job["result_url"]).json()
                    rows.append((kind, condition, seed, body["outcome"], body.get("rescan_reason", ""), body["mismatches"],
                                 body))
                    print(kind, condition, seed, body["outcome"], flush=True)

    lines = ["# Step 25b: print verification, what the real verifier gets wrong", "",
             f"Real renderer, real extractor, real quality gate; {args.n} synthetic photos per condition and kind "
             "(seeds 5000 and up), made from the approved PDF with the project's photo simulator. No physical print was "
             "photographed. Nothing was tuned on these photos.", "",
             "Right answers: positive (the approved label) is `match`; negative (a label of another lot) is `mismatch`.", "",
             "| kind | condition | n | match | mismatch | rescan_needed | job failed | right |", "|---|---|---|---|---|---|---|---|"]
    for kind in ("positive", "negative"):
        for condition in CONDITIONS:
            sub = [r for r in rows if r[0] == kind and r[1] == condition]
            count = Counter(r[3] for r in sub)
            right = count["match" if kind == "positive" else "mismatch"]
            lines.append(f"| {kind} | {condition} | {len(sub)} | {count['match']} | {count['mismatch']} | "
                         f"{count['rescan_needed']} | {count['job_failed']} | {right}/{len(sub)} |")
    wrong_pos = [r for r in rows if r[0] == "positive" and r[3] == "mismatch"]
    missed_neg = [r for r in rows if r[0] == "negative" and r[3] == "match"]
    lines += ["", f"- False alarms (approved label called mismatch): {len(wrong_pos)} of "
                  f"{sum(1 for r in rows if r[0] == 'positive')}",
              f"- Missed differences (other lot called match): {len(missed_neg)} of "
              f"{sum(1 for r in rows if r[0] == 'negative')}"]
    fields = Counter(m["field"] for r in wrong_pos for m in r[5])
    lines.append(f"- Fields behind the false alarms: {dict(fields) or 'none'}")
    reasons = Counter((r[4] or "").split(":")[0][:60] for r in rows if r[3] == "rescan_needed")
    lines.append(f"- Rescan reasons: {dict(reasons) or 'none'}")
    lines += ["", "False alarm details (field, expected, observed):"]
    for r in wrong_pos[:12]:
        lines.append(f"- {r[1]} seed {r[2]}: " + "; ".join(f"{m['field']} {m['expected']!r} read as {m['observed']!r}" for m in r[5]))
    lines += ["", "Missed difference details (what the verifier said about the other lot):"]
    for r in missed_neg[:12]:
        fs = [(f["field"], f["observed"], f["status"]) for f in r[6]["fields"] if f["field"] == "lot"]
        lines.append(f"- {r[1]} seed {r[2]}: lot {fs}, barcode match {r[6].get('barcode', {}).get('match')}")
    lines += ["", "Symbols are not compared (the symbol detector is not trusted)."]
    out = ROOT / args.out
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
