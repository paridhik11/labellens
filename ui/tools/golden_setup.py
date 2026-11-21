"""Prepare the golden package for the UI end-to-end run (ui/tools/live_flows.cjs).

Registers the golden product and its template through the API and renders the golden label PDF with the real
renderer. It does NOT upload, extract, confirm or change anything: the browser flow does that. Prints one JSON line
with the product id, the PDF path and the text the label really prints (used to correct unclear fields).

    python ui/tools/golden_setup.py --base http://127.0.0.1:8011 --out <folder>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import demo_flow as f  # noqa: E402


def main() -> int:
    """Register the golden product and write its label PDF."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    runner = f.Runner(f.Api(args.base))
    f.register_golden(runner, label="Golden Pump (ui run)")
    # A second product for the template-register check, so the end-to-end product keeps exactly one template.
    other = f.Runner(f.Api(args.base))
    f.register_golden(other, label="Golden Pump (ui template check)")
    pdf = f.render_golden_pdf(Path(args.out) / "golden_label.pdf")
    print(json.dumps({
        "product_id": runner.ctx["product_id"], "template_product_id": other.ctx["product_id"], "pdf": str(pdf),
        "truth": f.golden_truth_fields(f.GOLDEN), "template": f.golden_template(),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
