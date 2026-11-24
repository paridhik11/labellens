"""Measure whether a score gate would fold on-topic answers for curated medicine products (final_polish P2.9).

    python scripts/measure_curated_gate.py --base http://127.0.0.1:8000 [--gate 0.02] [--out file.json]

Same design as reports/abstain_display.md: 3 curated products, 8 on-topic and 8 off-topic questions, asked through
askPublic (extractive, curated products are asked without a gate). It reports each top score and how many on-topic
questions a gate at --gate would fold. A gate is only worth adding if it folds no on-topic question. Nothing is graded:
on-topic and off-topic are fixed by the question lists below.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

PRODUCTS = ("Childrens Ibuprofen", "Atorvastatin Calcium", "Amoxicillin")
ON_TOPIC = ("what is it used for", "what is the recommended dose", "what are the warnings", "who should not take it",
            "can I take it when pregnant", "what are the side effects", "what are the contraindications",
            "how should I take it")
OFF_TOPIC = ("how to repair a car engine", "what is the capital of France", "who won the world cup",
             "how to bake bread", "how to learn python", "weather in Paris tomorrow", "how to change a tire",
             "best pizza toppings")


def measure(base: str, gate: float) -> dict[str, Any]:
    """Ask every question for every product; return per-product scores and fold counts at the gate."""
    import requests

    out: dict[str, Any] = {"gate": gate, "products": []}
    for name in PRODUCTS:
        match = requests.post(f"{base}/public/match", json={"product_name": name}, timeout=120).json()
        pid = match["candidates"][0]["product_id"]
        row: dict[str, Any] = {"name": name, "product_id": pid, "outcome": match["outcome"], "on": [], "off": []}
        for key, questions in (("on", ON_TOPIC), ("off", OFF_TOPIC)):
            for q in questions:
                body = requests.post(f"{base}/public/ask", json={"question": q, "product_id": pid}, timeout=120).json()
                row[key].append({"q": q, "reason": body.get("reason"), "score": body.get("score")})
        scored_on = [x["score"] for x in row["on"] if x["score"] is not None]
        scored_off = [x["score"] for x in row["off"] if x["score"] is not None]
        row["on_folded"] = sum(s < gate for s in scored_on)
        row["off_folded"] = sum(s < gate for s in scored_off)
        row["on_scored"], row["off_scored"] = len(scored_on), len(scored_off)
        row["on_range"] = [min(scored_on), max(scored_on)] if scored_on else None
        row["off_range"] = [min(scored_off), max(scored_off)] if scored_off else None
        out["products"].append(row)
    out["on_folded_total"] = sum(p["on_folded"] for p in out["products"])
    out["decision"] = "add the gate" if out["on_folded_total"] == 0 else "no gate (on-topic answers would be folded)"
    return out


def main() -> int:
    """Run the measurement and print a short table."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--gate", type=float, default=0.02)
    ap.add_argument("--out")
    args = ap.parse_args()
    result = measure(args.base, args.gate)
    for p in result["products"]:
        print(f"{p['name']}: on-topic {p['on_range']} ({p['on_scored']} scored, {p['on_folded']} under the gate); "
              f"off-topic {p['off_range']} ({p['off_scored']} scored, {p['off_folded']} under the gate)")
    print(f"on-topic folded in all: {result['on_folded_total']}; decision: {result['decision']}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
