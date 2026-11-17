"""End-to-end demo check against a RUNNING LabelLens API (Step 25).

    python scripts/run_demo.py            # terminal 1: starts the API
    python scripts/demo_e2e.py            # terminal 2: golden package, synthetic photo, public medicine mode

Stages for the golden package: register product and template, render the golden PDF, upload, extract, confirm,
check, change, assess, confirm change, generate, re-check, approve, publish, export. Then the same upload, extract,
confirm and check for one synthetic photo (the photo's label is not made from the golden template, so it stops there),
and the public medicine answers (extractive, then the optional AI answer).

Each stage prints PASS, PASS (mock), FALLBACK or FAIL. FALLBACK means the real stage failed and the seeded demo data
was used so the demo can go on; PASS (mock) means the server answered from mock JSON (header X-Mock). The summary at
the end lists both, so nothing is hidden. Exit code 0 when no stage ended FAIL.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import demo_flow as f  # noqa: E402


def main() -> int:
    """Run every stage and print the summary."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--skip-ai", action="store_true", help="skip the optional AI answer (it can take a minute)")
    args = ap.parse_args()
    api = f.Api(args.base)
    r = f.Runner(api)
    work = f.new_workdir()
    stamp = time.strftime("%H%M%S")

    def health() -> str:
        for _ in range(60):
            try:
                if api.call("GET", "/health", user=None, timeout=3).status_code == 200:
                    me = api.ok("GET", "/me")
                    return f"API up at {args.base}, user {me['name']} ({me['role']})"
            except Exception:
                time.sleep(1)
        raise f.StageError("the API did not answer /health within 60 s")

    if not r.stage("0 health", health):
        print("\nThe API is not running. Start it with: python scripts/run_demo.py")
        return 1

    print("\n--- golden package ---")
    golden_pdf = work / "golden_label.pdf"
    r.stage("1 register product and template", lambda: f.register_golden(r, f"Golden Pump (e2e {stamp})"))
    pid = r.ctx.get("product_id")
    def render() -> str:
        path = f.render_golden_pdf(golden_pdf)
        return f"{path.name}, {path.stat().st_size} bytes, DRAFT marked test data"

    r.stage("2 render golden package (local)", render)

    def use_seed_label() -> str:
        r.ctx.update(product_id="prd_exampledevice", label_id="lbl_exampledevice_carton",
                     version_id="lbv_exampledevice_carton_l2", edit=("storage", "Store below 25 C"))
        r.ctx["seeded"] = True
        return "continuing with the seeded product prd_exampledevice and its label version L2"

    r.stage("3 upload and extract (real extractor)", lambda: f.upload_and_extract(r, golden_pdf),
                       fallback=use_seed_label)
    truth = f.golden_truth_fields(f.GOLDEN)
    r.stage("4 confirm extraction", lambda: f.confirm_fields(r, truth),
            fallback=lambda: "no extraction to confirm (seeded label version)")

    def seeded_inspection() -> str:
        check = api.ok("GET", "/check-results/chk_0001")
        return f"stored check {check['check_id']}: {len(check['findings'])} findings (seed data)"

    r.stage("5 check (inspect)", lambda: f.inspect(r), fallback=seeded_inspection)
    edit = r.ctx.get("edit", ("lot", "LOT2"))
    r.stage("6 change request", lambda: f.make_change(r, *edit))
    r.stage("7 assess impact", lambda: f.assess(r))
    r.stage("8 confirm change", lambda: f.confirm_change(r))

    r.stage("9 generate artwork (real renderer)", lambda: f.generate(r), fallback=lambda: f.seeded_check_fallback(r))
    def recheck() -> str:
        if r.ctx.get("seeded_l3"):
            return f"skipped: the seeded draft already has its passed check {f.SEED_L3_CHECK}"
        return f.recheck(r)

    r.stage("10 re-check generated artwork", recheck, fallback=lambda: f.seeded_check_fallback(r))
    r.stage("11 approve (reviewer)", lambda: f.approve(r), fallback=lambda: f.seeded_approve(r))
    r.stage("12 publish and open public page", lambda: f.publish(r))
    r.stage("13 export and verify hash", lambda: f.export(r),
            fallback=lambda: "the seeded draft has no stored files (only generated artwork exports), nothing to download")

    print("\n--- synthetic photo ---")
    photo_ok = r.stage("14 generate synthetic photo (local)", lambda: _photo(r, work))
    if photo_ok:
        photo_runner = f.Runner(api, ctx={})
        photo_runner.stages = r.stages
        p = r.ctx["photo"]
        photo_runner.ctx.update(product_id=p["product_id"])
        r.stage("15 photo: upload and extract", lambda: f.upload_and_extract(photo_runner, p["image"], "camera"))
        photo_runner.ctx["extraction"] = photo_runner.ctx.get("extraction", {"fields": {}})
        r.stage("16 photo: confirm extraction", lambda: f.confirm_fields(photo_runner, p["truth"]))
        r.stage("17 photo: check (inspect)", lambda: f.inspect(photo_runner))

    print("\n--- public medicine mode ---")
    r.stage("18 match and extractive answer", lambda: f.answers(r))
    if not args.skip_ai:
        r.stage("19 AI answer (optional job)", lambda: f.ai_answer(r))

    print("\n--- summary ---")
    for s in r.stages:
        print(f"{s.status:<12} {s.name}")
    failed = [s for s in r.stages if s.status == "FAIL"]
    fallbacks = [s for s in r.stages if s.status == "FALLBACK"]
    print(f"\n{len(r.stages) - len(failed) - len(fallbacks)} passed, {len(fallbacks)} used fallback data, {len(failed)} failed")
    print("stages answered from mock JSON:", ", ".join(sorted(set(api.mocks))) or "none")
    print("stages that used seeded data instead of the real result:", ", ".join(s.name for s in fallbacks) or "none")
    return 1 if failed else 0


def _photo(r: f.Runner, work: Path) -> str:
    """Make the photo and register a product whose record matches the label it shows."""
    image, truth = f.synthetic_photo(work)
    fields = truth.get("fields") or truth.get("field_values") or {}
    ais = truth.get("barcode_ais") or truth.get("ais") or {}
    if not fields:
        raise f.StageError(f"unexpected ground truth keys: {sorted(truth)}")
    record = {
        "name": fields["product_name"], "model": fields["model"].split(":", 1)[-1].strip(),
        "manufacturer": fields["manufacturer"], "manufacturer_address": fields["manufacturer_address"],
        "udi_di": ais.get("01", "00000000000000"), "sterilization": "EO", "storage": "Store dry",
        "extra": {"lot": fields["lot"].split(":", 1)[-1].strip(), "expiry": fields["expiry"].split(":", 1)[-1].strip(),
                  "serial": ais.get("21", "")},
        "intended_market": ["US"],
    }
    product = r.api.ok("POST", "/products", json=record)
    r.ctx["photo"] = {"image": image, "truth": {k: fields[k] for k in f.golden_truth_fields(f.GOLDEN) if k in fields},
                      "product_id": product["product"]["product_id"]}
    return f"{image.name} ({image.stat().st_size // 1024} KB, condition hard), product {r.ctx['photo']['product_id']}"


if __name__ == "__main__":
    raise SystemExit(main())
