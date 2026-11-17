"""The demo workflow as HTTP calls against a running LabelLens API (Step 25). Used by demo_e2e.py and run_demo.py.

Nothing here touches the database or the renderer on the server side: every stage is an ordinary API call, so the
same code drives a demo, a smoke test and the seed of the golden package. Two things need local libraries and run in
this process (the server never sees them): rendering the golden PDF with the label renderer, and generating the
synthetic photo. Without those libraries those stages fail and their fallback stage uses the seeded demo data.

"Mock" has one meaning here. The server answers operations it does not implement for real from mock JSON and says so
with the header `X-Mock: true`; `Api.call` records every such answer, and a stage that received one is reported as
`PASS (mock)`. A `FALLBACK` stage means the real stage failed and the seeded data (the demo seed, not a mock) was
used instead, so the demo can go on.
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EDITOR, REVIEWER = "usr_demo_editor", "usr_demo_reviewer"
SEED_L3 = "lbv_exampledevice_carton_l3"  # the seeded generated draft with a passed self-check
SEED_L3_SHA = "23f81fcd260e85a1086f09eaf733427f7cbb09becdf887a081ee857dcad90b74"
SEED_L3_CHECK = "chk_0003"
GOLDEN = {  # what the golden label prints; all values are test data and the identifier is the GS1 test placeholder
    "name": "Golden Pump", "model": "GP-100", "manufacturer": "Demo Labs", "manufacturer_address": "12 Demo Road",
    "udi_di": "00000000000000", "sterilization": "EO", "storage": "Store dry",
    "extra": {"lot": "LOT1", "expiry": "2030-06-30", "serial": "SN1"},
}
TEMPLATE_PATH = ROOT / "src" / "gen" / "templates" / "test_device.json"


class StageError(Exception):
    """A stage failed. The message is what the demo prints."""


class Api:
    """A thin client: one base URL, the X-User-Id stub header, and a list of the mock answers it has seen."""

    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.http = requests.Session()
        self.mocks: list[str] = []

    def call(self, method: str, path: str, user: str | None = EDITOR, timeout: float = 60, **kwargs: Any) -> requests.Response:
        """One request. Records `METHOD path` when the server answered from a mock."""
        headers = {"X-User-Id": user} if user else {}
        response = self.http.request(method, self.base + path, headers=headers, timeout=timeout, **kwargs)
        if response.headers.get("X-Mock") == "true":
            self.mocks.append(f"{method} {path.split('?')[0]}")
        return response

    def ok(self, method: str, path: str, expect: tuple[int, ...] = (200, 201, 202), **kwargs: Any) -> Any:
        """A request that must answer one of `expect`; returns the parsed JSON, raises StageError otherwise."""
        response = self.call(method, path, **kwargs)
        if response.status_code not in expect:
            raise StageError(f"{method} {path} -> {response.status_code} {response.text[:300]}")
        return response.json() if response.content and "json" in response.headers.get("content-type", "") else response

    def wait(self, job: dict[str, Any], limit: float = 180) -> dict[str, Any]:
        """Poll a 202 job until it is done; raises StageError when it fails or runs out of time."""
        end = time.time() + limit
        while time.time() < end:
            state = self.ok("GET", f"/jobs/{job['job_id']}", user=None)
            if state["state"] == "done":
                return state
            if state["state"] == "failed":
                raise StageError(f"job {job['job_id']} failed: {json.dumps(state.get('error'))[:300]}")
            time.sleep(1.0)
        raise StageError(f"job {job['job_id']} did not finish within {limit:.0f} s")


@dataclass
class Stage:
    """The outcome of one stage."""

    name: str
    status: str  # PASS, PASS (mock), FALLBACK, FAIL
    detail: str
    seconds: float


@dataclass
class Runner:
    """Runs stages in order, prints one line each, keeps the shared context between them."""

    api: Api
    ctx: dict[str, Any] = field(default_factory=dict)
    stages: list[Stage] = field(default_factory=list)

    def stage(self, name: str, run: Callable[[], str], fallback: Callable[[], str] | None = None) -> bool:
        """Run one stage. A failure runs `fallback` when there is one. Returns True unless the stage ended FAIL."""
        started, mocks_before = time.time(), len(self.api.mocks)
        try:
            detail = run()
            used_mock = len(self.api.mocks) > mocks_before
            status = "PASS (mock)" if used_mock else "PASS"
            if used_mock:
                detail += "  [answered from mock: " + ", ".join(self.api.mocks[mocks_before:]) + "]"
        except Exception as error:  # a stage must never stop the demo
            reason = f"{type(error).__name__}: {error}"[:400]
            if fallback is None:
                status, detail = "FAIL", reason
            else:
                try:
                    status, detail = "FALLBACK", f"{fallback()}  [real stage failed: {reason}]"
                except Exception as second:
                    status, detail = "FAIL", f"{reason}; fallback also failed: {second}"[:500]
        elapsed = time.time() - started
        self.stages.append(Stage(name, status, detail, elapsed))
        print(f"[{status:<11}] {name:<34} {elapsed:6.1f}s  {detail}", flush=True)
        return status != "FAIL"


# ---------------------------------------------------------------- local helpers (need the CV libraries)


def golden_template() -> dict[str, Any]:
    """The template of the golden package: Parth's test device template (no background image, millimetres)."""
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def golden_truth_fields(record: dict[str, Any]) -> dict[str, str]:
    """The text the golden label prints for a product record, keyed like the extractor's fields."""
    extra = record["extra"]
    return {
        "product_name": record["name"], "manufacturer": record["manufacturer"],
        "manufacturer_address": record["manufacturer_address"], "model": f"REF: {record['model']}",
        "lot": f"LOT: {extra['lot']}", "expiry": f"EXP: {extra['expiry']}",
    }


def render_golden_pdf(path: Path, record: dict[str, Any] | None = None) -> Path:
    """Render the golden label with the real renderer (needs zxing-cpp and reportlab). Test data, so it is marked DRAFT."""
    from src.common.schemas import ProductRecord
    from src.export.pdf import render_pdf
    from src.export.template import from_product

    record = record or GOLDEN
    product = ProductRecord(product_id="golden", **{k: v for k, v in record.items()})
    label = from_product(golden_template(), product, version_id="golden-v1", actor="demo", reason="golden package",
                         test_data=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
        Path(str(path) + ".json").unlink(missing_ok=True)
    return render_pdf(label, path)


def synthetic_photo(folder: Path, seed: int = 4242) -> tuple[Path, dict[str, Any]]:
    """One synthetic phone-style photo of a generated label (condition `hard`) and its ground truth."""
    from src.gen.generate_dataset import generate_dataset

    target = folder / f"photo_{seed}"
    generate_dataset(target, seed=seed, labels_per_condition=1, conditions=("hard",))
    image = next((target / "hard").glob("*.png"))
    return image, json.loads(image.with_suffix(".json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- the stages


def register_golden(r: Runner, label: str = "Golden Pump (demo)") -> str:
    """Register the golden product and its template (an editor does this once per product)."""
    api = r.api
    body = {**GOLDEN, "name": label, "intended_market": ["US"]}
    product = api.ok("POST", "/products", json=body)
    pid = product["product"]["product_id"]
    template = golden_template()
    api.ok("POST", f"/products/{pid}/templates", json={"size_mm": template["size_mm"], "background": None,
                                                       "slots": template["slots"]})
    r.ctx.update(product_id=pid, record=product["record"])
    return f"product {pid}, template {template['template_id']} ({template['size_mm']['w']} x {template['size_mm']['h']} mm)"


def upload_and_extract(r: Runner, file: Path, source: str = "upload") -> str:
    """Upload a scan, wait for its job (quality gate, then the real extractor), read the extraction."""
    api = r.api
    with file.open("rb") as handle:
        mime = "application/pdf" if file.suffix == ".pdf" else "image/png"
        job = api.ok("POST", "/scans", files={"file": (file.name, handle, mime)},
                     data={"source": source, "product_id": r.ctx["product_id"]})
    done = api.wait(job)
    scan = api.ok("GET", done["result_url"]) if done.get("result_url") else {}
    if scan.get("state") != "done":
        raise StageError(f"scan ended {scan.get('state')}: {json.dumps(scan.get('error'))[:300]}")
    r.ctx.update(label_id=scan["label_id"], version_id=scan["version_id"])
    ex = api.ok("GET", f"/label-versions/{scan['version_id']}/extraction")
    r.ctx["extraction"] = ex
    unclear = ex.get("unclear_fields", ex.get("unclear", []))
    return f"version {scan['version_id']}, {len(ex['fields'])} fields read, {len(unclear)} unclear"


def confirm_fields(r: Runner, truth: dict[str, str]) -> str:
    """The user confirms the extraction, correcting every field that differs from what the label prints."""
    ex = r.ctx["extraction"]["fields"]
    corrections = {k: v for k, v in truth.items() if ex.get(k, "").strip() != v}
    body = {"fields": {**{k: v for k, v in ex.items() if k in truth}, **corrections}}
    confirmed = r.api.ok("POST", f"/label-versions/{r.ctx['version_id']}/extraction/confirm", json=body)
    return f"confirmed {len(body['fields'])} fields, {len(corrections)} corrected by the user ({', '.join(corrections) or 'none'})"


def inspect(r: Runner, user: str = EDITOR) -> str:
    """Check the uploaded label: extraction against the record, with cited requirements."""
    api = r.api
    response = api.call("POST", f"/label-versions/{r.ctx['version_id']}/inspect", user=user)
    if response.status_code == 202:
        response = api.call("GET", api.wait(response.json())["result_url"], user=user)
    if response.status_code != 200:
        raise StageError(f"inspect -> {response.status_code} {response.text[:300]}")
    check = response.json()
    r.ctx["inspection"] = check
    config = check.get("retrieval_config", {})
    note = f", fell back from {config['fallback_from']}" if config.get("fallback_from") else ""
    return (f"{len(check['findings'])} findings, {check.get('needs_human_count', 0)} need a human, "
            f"retrieval {config.get('method')}{note}")


def make_change(r: Runner, field: str = "lot", new_value: str = "LOT2") -> str:
    """Create a change request from a structured edit; the server assesses its impact."""
    made = r.api.ok("POST", "/changes", json={"product_id": r.ctx["product_id"], "edits": [
        {"field": field, "new_value": new_value}]})
    r.ctx["change"] = made
    r.ctx["change_id"] = made["change"]["change_id"]
    return f"change {r.ctx['change_id']}: {field} -> {new_value}"


def assess(r: Runner) -> str:
    """Report the assessment the change was created with (parser, affected items, barcode decision)."""
    made = r.ctx["change"]
    items = made.get("affected", [])
    cited = sum(1 for i in items if i.get("citations") or i.get("evidence"))
    return f"parser {made['parser']}, {len(items)} affected item(s), {cited} with cited evidence"


def confirm_change(r: Runner) -> str:
    """A human confirms the parsed change and every checklist decision."""
    items = r.ctx["change"].get("affected", [])
    decisions = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in items]
    body = {"parse_confirmed": True, "decisions": decisions}
    r.api.ok("POST", f"/changes/{r.ctx['change_id']}/confirm", json=body)
    return f"confirmed parse and {len(decisions)} decision(s)"


def generate(r: Runner) -> str:
    """Fill the template with the confirmed values (renderer job); never invents an identifier (test data flag)."""
    job = r.api.ok("POST", f"/changes/{r.ctx['change_id']}/generate",
                   json={"label_id": r.ctx["label_id"], "test_data": True})
    done = r.api.wait(job)
    art = r.api.ok("GET", done["result_url"])
    r.ctx.update(gen_version=art["version_id"], gen_sha=art["artifact_sha256"], artwork=art)
    decision = art["barcode_decision"]["decision"]
    return f"version {art['version_id']}, barcode {decision}, DRAFT mark {art['draft_watermark']}, sha {art['artifact_sha256'][:12]}"


def recheck(r: Runner, version: str | None = None) -> str:
    """Read the rendered PDF back as an image with the real extractor and run the checker on it."""
    version = version or r.ctx["gen_version"]
    response = r.api.call("POST", f"/label-versions/{version}/recheck")
    if response.status_code == 202:
        response = r.api.call("GET", r.api.wait(response.json())["result_url"])
    if response.status_code != 200:
        raise StageError(f"recheck -> {response.status_code} {response.text[:300]}")
    check = response.json()
    r.ctx["recheck"] = check
    if not check["passed"]:
        kinds = ", ".join(sorted({f"{f.get('rule_id', f['kind'])}" for f in check["findings"]}))
        raise StageError(f"re-check did not pass ({len(check['findings'])} findings: {kinds}); approval needs a passed check")
    return f"check {check['check_id']} passed, {len(check['findings'])} findings, {check.get('needs_human_count', 0)} need a human"


def approve(r: Runner, version: str | None = None, sha: str | None = None, check: str | None = None) -> str:
    """A reviewer approves exactly this version: its artifact hash and a passed re-check."""
    version = version or r.ctx["gen_version"]
    review = r.api.ok("POST", f"/label-versions/{version}/reviews", user=REVIEWER, json={
        "decision": "approve", "artifact_sha256": sha or r.ctx["gen_sha"],
        "check_id": check or r.ctx["recheck"]["check_id"], "comment": "demo approval"})
    r.ctx["approved_version"] = version
    return f"review {review['review_id']} by a reviewer, status {review['resulting_status']}"


def publish(r: Runner) -> str:
    """Publish the approved version and open its public page, the page the QR points at."""
    version = r.ctx["approved_version"]
    page = r.api.ok("POST", f"/label-versions/{version}/publish", user=REVIEWER)
    path = "/" + page["url"].split("://", 1)[-1].split("/", 1)[-1]
    html = r.api.call("GET", path, user=None)
    if html.status_code != 200 or version not in html.text:
        raise StageError(f"public page {path} -> {html.status_code}")
    r.ctx["page"] = page
    return f"page {page['page_id']} at {page['url']} (opened, {len(html.text)} bytes)"


def export(r: Runner) -> str:
    """Download the stored PDF and check it against its recorded hash."""
    import hashlib

    version = r.ctx["approved_version"]
    package = r.api.ok("GET", f"/label-versions/{version}/exports")
    pdf = r.api.call("GET", package["pdf"]["url"])
    if pdf.status_code != 200:
        raise StageError(f"download -> {pdf.status_code}")
    digest = hashlib.sha256(pdf.content).hexdigest()
    if digest != package["pdf"]["sha256"]:
        raise StageError("downloaded PDF does not match its recorded hash")
    qr = package.get("qr")
    return f"PDF {len(pdf.content)} bytes, hash verified, status {package['status']}, QR page {'yes' if qr else 'no'}"


def answers(r: Runner) -> str:
    """Public medicine mode: match a name, ask the extractive answer from that product's chunks, then the AI answer."""
    api = r.api
    match = api.ok("POST", "/public/match", user=None, json={"product_name": "Childrens Ibuprofen"})
    best = match["candidates"][0]
    ask = {"question": "what are the warnings", "product_id": best["product_id"]}
    extractive = api.ok("POST", "/public/ask", user=None, json=ask)
    n = len(extractive.get("sources", []))
    unknown = api.ok("POST", "/public/match", user=None, json={"product_name": "Zzyzx Gummies"})
    return (f"match {best['product_name']} ({match['outcome']}, cosine {match['score']}), extractive answer "
            f"{'abstained' if extractive['abstained'] else 'answered'} with {n} passages, "
            f"unknown name -> {unknown['outcome']}")


def ai_answer(r: Runner) -> str:
    """The optional AI answer (mode=ai job). It always ends done; a missing model falls back to the passages."""
    api = r.api
    started = api.ok("POST", "/public/ask?mode=ai", user=None, json={
        "question": "what does the label say about stomach bleeding", "product_id": r.ctx.get("medicine_id", "med_0faa3b41")})
    done = api.wait(started, limit=240)
    result = done.get("result", {})
    return (f"model {result.get('model')}, model_used {result.get('model_used')}, "
            f"fallback {result.get('fallback_reason', 'none')}, {result.get('latency_s')} s")


def seeded_check_fallback(r: Runner) -> str:
    """Used when generation or the re-check failed: continue with the demo seed's draft L3 (approvable as it is)."""
    r.ctx.update(gen_version=SEED_L3, gen_sha=SEED_L3_SHA, recheck={"check_id": SEED_L3_CHECK}, seeded_l3=True)
    return f"continuing with the seeded draft {SEED_L3} and its passed check {SEED_L3_CHECK}"


def seeded_approve(r: Runner) -> str:
    """Approve the seeded L3 as a reviewer (used after a fallback)."""
    return approve(r, SEED_L3, SEED_L3_SHA, SEED_L3_CHECK)


def new_workdir() -> Path:
    """A scratch folder for the golden PDF and the synthetic photo."""
    return Path(tempfile.mkdtemp(prefix="labellens_demo_"))
