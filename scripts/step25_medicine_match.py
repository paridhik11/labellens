"""Step 25a: fit and report the product-name match threshold (bge-large cosine of the top reference product).

    python scripts/step25_medicine_match.py          # prints the table and writes results/step25_medicine_match.md

The queries below are hand-written for this check (no real photo OCR): the exact corpus names, noisy variants a pack
reader could produce, and names of products that are NOT in the corpus. The threshold is the midpoint between the
best-scoring negative and the worst-scoring positive, so it is fitted on the same queries it is reported on: treat
the accuracy as a sanity check, not as a measured error rate.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.medicine import MedicineCatalog, ProductMatcher  # noqa: E402

NOISY = {
    "tylenol extra strength acetaminophen caplets": "Pain Relief Extra Strength",
    "Omeprazole 20 mg delayed release tablets": "Omeprazole",
    "Famotadine oral suspension": "FAMOTIDINE",
    "Amoxicilin 500mg capsules": "Amoxicillin",
    "metformin": "METFORMIN HYDROCHLORIDE",
    "levothyroxine 75 mcg": "Levothyroxine Sodium",
    "atorvastatin 40 mg tablets": "Atorvastatin Calcium",
    "childrens loratadine allergy relief": "Loratadine",
}
NEGATIVES = [
    "Losartan potassium tablets", "Lipitor", "Lisinopril", "Aspirin 81 mg", "Vitamin C gummies", "Advil",
    "Cetirizine", "Ozempic pen", "Sertraline 50 mg", "Prednisone", "Zzyzx Gummies", "Digital thermometer",
]


def main() -> None:
    """Score every query, fit the threshold, write the report."""
    catalog = MedicineCatalog()
    matcher = ProductMatcher(catalog, threshold=0.0)
    matcher._load()
    rows = []  # (kind, query, expected, top name, cosine)
    queries = [("exact", p.name, p.name) for p in catalog.products.values()]
    queries += [("noisy", q, name) for q, name in NOISY.items()] + [("negative", q, "") for q in NEGATIVES]
    started = time.perf_counter()
    for kind, query, expected in queries:
        found = matcher.match(query)
        top = catalog.products[found["candidates"][0][0]].name if found["candidates"] else ""
        rows.append((kind, query, expected, top, found["score"]))
    per_query = (time.perf_counter() - started) / len(queries)
    worst_positive = min(r[4] for r in rows if r[0] != "negative")
    best_negative = max(r[4] for r in rows if r[0] == "negative")
    threshold = round((worst_positive + best_negative) / 2, 2)
    lines = ["# Step 25a: medicine product-name matching", "",
             f"Retriever: frozen E5b recipe over {len(catalog.products)} product documents; decision: bge-large cosine of the "
             "top product. Queries are hand-written for this check; the threshold is fitted on them, so the figures below "
             "are a sanity check and not an error rate.", "",
             f"- worst positive cosine {worst_positive:.4f}, best negative cosine {best_negative:.4f}, "
             f"threshold = midpoint {threshold}",
             f"- mean time per match after the models are loaded: {per_query:.2f} s", "",
             "| kind | query | expected | top product | cosine | decision |", "|---|---|---|---|---|---|"]
    wrong = 0
    for kind, query, expected, top, score in rows:
        accepted = score >= threshold
        ok = (accepted and top == expected) if kind != "negative" else not accepted
        wrong += not ok
        lines.append(f"| {kind} | {query} | {expected or '(none)'} | {top} | {score:.4f} | "
                     f"{'accept' if accepted else 'no_reference_match'}{'' if ok else ' WRONG'} |")
    lines += ["", f"Wrong decisions at threshold {threshold}: {wrong} of {len(rows)}."]
    out = Path("results/step25_medicine_match.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
