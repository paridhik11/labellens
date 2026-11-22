"""Write results/ndc_scan/results.md from final_summary.json and final_rows.jsonl (no new computation of results)."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("results/ndc_scan")


def pct(k: int, n: int, interval: list[float] | tuple[float, float] | None = None) -> str:
    """``k/n`` with an optional Wilson interval."""
    text = f"{k}/{n}"
    if interval:
        text += f" ({interval[0] * 100:.0f} to {interval[1] * 100:.0f}%)"
    return text


def main() -> None:
    """Render coverage, results, per-product and gate tables."""
    s = json.loads((OUT / "final_summary.json").read_text("utf-8"))
    g = s["gate"]
    lines = ["# NDC scan: frozen version scored once", "",
             f"Config commit `{s['config_commit'][:8]}`, config {s['config']}. Protocol: `protocol.md`. "
             "OCR seconds were measured with 2 readers running on a CPU shared with another session.", "",
             "## Gate", "",
             "| check | result | pass |", "|---|---|---|",
             f"| 1 wrong products on unused decoys ({g['1_decoy_products']} products) | new "
             f"{g['1_wrong_products_unused_decoys_new_method']}, E replay {g['1_wrong_products_unused_decoys_E_replay']}"  # noqa: E501
             f" | {g['pass_1']} |",
             f"| 2 timeouts, unused decoy photos | new {g['2_timeouts_unused_new']}, E replay "
             f"{g['2_timeouts_unused_E_replay']}, E recorded {g['2_timeouts_unused_E_recorded']} | |",
             f"| 2 timeouts, positives | new {g['2_timeouts_positives_new']}, E replay "
             f"{g['2_timeouts_positives_E_replay']} | {g['pass_2']} |",
             f"| 3 correct on {g['3_positive_photos']} positive photos | new {g['3_correct_positives_new']}, E replay "
             f"{g['3_correct_positives_E_replay']} | {g['pass_3']} |",
             f"| **all** | | **{g['pass_all']}** |", "",
             f"Decoy photos where any product was shown (review lists included): new "
             f"{g['1_decoy_photos_with_any_product_shown_new']}, E replay {g['1_decoy_photos_with_any_product_shown_E']}.",  # noqa: E501
             "", "## Coverage of each signal", "",
             "| set | photos | barcode NDC read | barcode in table | printed NDC-shaped | printed in table | "
             "either in table | NDC decided |", "|---|---|---|---|---|---|---|---|"]
    for name, c in s["coverage"].items():
        lines.append(f"| {name} | {c['photos']} | {c['barcode_ndc_read']} | {c['barcode_in_table']} | "
                     f"{c['printed_ndc_shaped']} | {c['printed_in_table']} | {c['either_in_table']} | {c['ndc_decided']} |")  # noqa: E501
    lines += ["", "## Results by set (Wilson 95%)", "",
              "| set | method | photos | correct | wrong | review | not identified | timeout | median s | max s |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for name in ("positives", "unused_decoy", "new_set"):
        for label, key in (("new", "new"), ("E replay", "e_replay")):
            r = s[key][name]
            c = r["counts"]
            lines.append(f"| {name} | {label} | {r['photos']} | {pct(c.get('correct', 0), r['photos'], r['correct_interval'])}"  # noqa: E501
                         f" | {pct(c.get('wrong', 0), r['photos'], r['wrong_interval'])} | {c.get('review', 0)} | "
                         f"{c.get('not_identified', 0)} | {c.get('timeout', 0)} | {r['seconds']['median']} | "
                         f"{r['seconds']['max']} |")
    lines += ["", "## Positives by condition", "", "| condition | new correct | E replay correct |", "|---|---|---|"]
    for cond in ("artwork", "moderate", "hard"):
        a = s["new_by_condition"]["positives"][cond]
        b = s["e_by_condition"]["positives"][cond]
        lines.append(f"| {cond} | {pct(a['counts'].get('correct', 0), a['photos'], a['correct_interval'])} | "
                     f"{pct(b['counts'].get('correct', 0), b['photos'], b['correct_interval'])} |")
    lines += ["", "## Per product (categories of artwork, moderate, hard in file order)", "",
              "| product | role | new | E replay | sources |", "|---|---|---|---|---|"]
    for p in s["per_product"]:
        lines.append(f"| {p['product'][:44]} | {p['role']} | {', '.join(p['new'])} | {', '.join(p['e'])} | "
                     f"{', '.join(p['sources'])} |")
    (OUT / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("written")


if __name__ == "__main__":
    main()
