"""Step 25c: why do correct prints end as rescan_needed? Record, per photo, which check or field failed and why.

    python scripts/step25c_diagnose.py --seed-base 7000 --n 8 --out results/step25c_diagnosis.md

Same setup as step25b_print_eval.py (real renderer, extractor, quality gate, approved label), but only correct prints
(photos of the approved label), on seeds that step 25b did not use (it used 5000 to 5007). For each photo the stored
verification row is read back (fields with status, observed text and OCR confidence; the rescan reason; the engine's
warnings) and the barcode result. Nothing is tuned; this only reads what the verifier already stored.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from step25b_print_eval import EDITOR, RECORD, REVIEWER, png, render_page  # noqa: E402


def main() -> int:
    """Approve a label, photograph it on fresh seeds, verify, and write one line per photo."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-base", type=int, default=7000)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", default="results/step25c_diagnosis.md")
    ap.add_argument("--title", default="Step 25c: why correct prints end as rescan_needed")
    args = ap.parse_args()
    work = Path(tempfile.mkdtemp(prefix="pd_"))
    os.environ["LABELLENS_FILES_DIR"] = str(work)

    from fastapi.testclient import TestClient

    from src.api.main import create_app
    from src.api.store import add_label_version
    from src.gen.augment import augment_label_detailed

    template = json.loads((ROOT / "src" / "gen" / "templates" / "test_device.json").read_text(encoding="utf-8"))
    records = []
    with TestClient(create_app("sqlite://", seed=True)) as client:
        def call(method: str, path: str, user=EDITOR, **kw):
            return client.request(method, path, headers=user, **kw)

        def job_of(response):
            job = call("GET", f"/jobs/{response.json()['job_id']}").json()
            assert job["state"] == "done", job
            return job

        pid = call("POST", "/products", json=RECORD).json()["product"]["product_id"]
        call("POST", f"/products/{pid}/templates", json={"size_mm": template["size_mm"], "background": None,
                                                         "slots": template["slots"]})
        with client.app.state.session_factory() as session:
            label_id = add_label_version(session, "usr_demo_editor", pid, "uploads/" + "a" * 64 + ".png").label_id
        made = call("POST", "/changes", json={"product_id": pid, "edits": [{"field": "lot", "new_value": "LOT2"}]}).json()
        decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in made["affected"]]
        change = made["change"]["change_id"]
        call("POST", f"/changes/{change}/confirm", json={"parse_confirmed": True, "decisions": decisions})
        art = call("GET", job_of(call("POST", f"/changes/{change}/generate",
                                      json={"label_id": label_id, "test_data": True}))["result_url"]).json()
        version, sha = art["version_id"], art["artifact_sha256"]
        pdf = (work / "artifacts" / f"{sha}.pdf").read_bytes()
        check = call("GET", job_of(call("POST", f"/label-versions/{version}/recheck"))["result_url"]).json()
        assert check["passed"], check["findings"]
        assert call("POST", f"/label-versions/{version}/reviews", user=REVIEWER, json={
            "decision": "approve", "artifact_sha256": sha, "check_id": check["check_id"]}).status_code == 201
        page = render_page(pdf)
        for condition in ("clean", "moderate", "hard"):
            for i in range(args.n):
                seed = args.seed_base + i
                photo, *_ = augment_label_detailed(page, condition, seed)
                sent = call("POST", f"/label-versions/{version}/print-verifications",
                            files={"photo": ("p.png", png(photo), "image/png")},
                            data={"condition": "clean_print_scan" if condition == "clean" else "phone_photo"})
                job = call("GET", f"/jobs/{sent.json()['job_id']}").json()
                if job["state"] != "done":
                    records.append({"condition": condition, "seed": seed, "outcome": "job_failed", "error": job.get("error")})
                    continue
                body = call("GET", job["result_url"]).json()
                records.append({"condition": condition, "seed": seed, "outcome": body["outcome"],
                                "reason": body.get("rescan_reason", ""), "fields": body.get("fields", []),
                                "mismatches": body["mismatches"], "barcode": body.get("barcode"),
                                "warnings": body["notes"].get("warnings", [])})
                print(condition, seed, body["outcome"], flush=True)

    lines = [f"# {args.title}", "", f"Correct prints only, seeds {args.seed_base} to {args.seed_base + args.n - 1}, "
             f"{args.n} per condition. Synthetic photos of the approved label. Read-back of the stored verification rows.", "",
             "| condition | n | match | mismatch | rescan_needed | job failed |", "|---|---|---|---|---|---|"]
    for condition in ("clean", "moderate", "hard"):
        sub = [r for r in records if r["condition"] == condition]
        c = Counter(r["outcome"] for r in sub)
        lines.append(f"| {condition} | {len(sub)} | {c['match']} | {c['mismatch']} | {c['rescan_needed']} | {c['job_failed']} |")
    lines += ["", "## Which check failed, per rescan", "",
              "| condition | seed | field statuses (status, OCR confidence) | barcode | reason | warnings |", "|---|---|---|---|---|---|"]
    causes: Counter = Counter()
    for r in records:
        if r["outcome"] != "rescan_needed":
            continue
        fs = "; ".join(f"{f['field']}: {f['status']}" + (f" {f['confidence']:.2f}" if f["confidence"] is not None else " none")
                       + ("" if f["status"] == "MATCH" else f" (read {f['observed']!r})") for f in r["fields"])
        bc = r["barcode"]
        bcs = "none decoded" if not bc else f"decoded, match {bc['match']}"
        lines.append(f"| {r['condition']} | {r['seed']} | {fs} | {bcs} | {r['reason'][:110]} | {', '.join(w.split(':')[0] for w in r['warnings'])} |")
        for f in r["fields"]:
            if f["status"] != "MATCH":
                causes[f"{f['field']} {f['status']} ({'no evidence' if f['confidence'] is None else 'low conf'})"] += 1
        if not bc:
            causes["barcode not decoded"] += 1
        elif not bc["match"]:
            causes["barcode decoded but differs"] += 1
        for w in r["warnings"]:
            causes["warning " + w.split(":")[0]] += 1
    lines += ["", "## Cause counts (one per rescan and failing item)", ""]
    lines += [f"- {k}: {v}" for k, v in causes.most_common()] or ["- none"]
    out = ROOT / args.out
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
