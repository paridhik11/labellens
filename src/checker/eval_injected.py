"""Injected-error evaluation of the checker (docs/CHECKER_SPEC.md section 7).

Three commands. ``generate`` and ``extract`` need the CV libraries (cv2, zxingcpp, rapidocr), the
others do not, so the work can be split across two virtual environments:

  generate  render base labels, each with injected errors, in three photo conditions
  extract   run the unchanged CV extractor on every image (template and blind mode)
  evaluate  run the checker on oracle extractions and on the real extractions, write a report

Kinds: clean (no error), expiry_format, barcode_mismatch, missing_symbol, wrong_name (all printed on
the image), and udi_mismatch, rx_missing (record side, on the clean image). Only the checker reads
the injection record; the extractor reads the image alone.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from src.checker import gs1
from src.checker.citations import CITATION_SPECS, find_citation
from src.checker.models import CheckerResult
from src.checker.retrieval import build_retriever, module_chunks
from src.checker.runner import run_checks
from src.checker.settings import CheckerSettings, RetrievalSettings
from src.checker.synthetic import extraction_from_truth, record_from_truth
from src.cv.intervals import wilson_interval
from src.ir.base import Retriever

CONDITIONS = ("clean", "moderate", "hard")
ALL_CONDITIONS = (*CONDITIONS, "very_hard")  # very_hard reuses the hard augmentation seed
KINDS = ("clean", "expiry_format", "barcode_mismatch", "missing_symbol", "wrong_name", "udi_mismatch", "rx_missing")
IMAGE_KINDS = KINDS[:5]
KIND_RULES = {
    "expiry_format": ("D-FMT",), "barcode_mismatch": ("B-LOT", "B-EXP"), "missing_symbol": ("S-MFR", "S-EXP"),
    "wrong_name": ("P-NAME",), "udi_mismatch": ("P-UDI",), "rx_missing": ("R-RX",),
}
OTHER_UDI_DI = "00000000000017"  # test-only record value that differs from the generator placeholder, valid check digit
BAD_FORMATS = ("{d:%d/%m/%Y}", "{d:%Y/%m/%d}", "{d:%m-%d-%Y}", "{d:%d.%m.%Y}")
SAFE_CHARS = "234679"


def wilson(k: int, n: int) -> str:
    """'k/n = rate [lo, hi]' with a 95% Wilson interval, or 'n=0'."""
    if n == 0:
        return "n=0"
    lo, hi = wilson_interval(k, n)
    return f"{k}/{n} = {k / n:.2f} [{lo:.2f}, {hi:.2f}]"


# ----------------------------------------------------------------------------------- generate


def _variants(index: int, rng: np.random.Generator) -> dict[str, Any]:
    """Draw one base label and the injected versions of it (printed values and injection records)."""
    from src.gen.generate_dataset import _variant_values

    fields, ais = _variant_values(index, rng)
    expiry = date(2000 + int(ais["17"][:2]), int(ais["17"][2:4]), int(ais["17"][4:]))
    out: dict[str, Any] = {"fields": fields, "ais": ais, "variants": {}}
    out["variants"]["clean"] = {"field_values": {}, "overrides": None, "mismatch": False, "expected": []}
    fmt = BAD_FORMATS[index % len(BAD_FORMATS)]
    out["variants"]["expiry_format"] = {
        "field_values": {"expiry": "EXP: " + fmt.format(d=expiry)}, "overrides": None, "mismatch": True,
        "expected": ["D-FMT"],
    }
    if index % 2:
        other = expiry + timedelta(days=1 + index % 9)
        out["variants"]["barcode_mismatch"] = {
            "field_values": {"expiry": f"EXP: {other.isoformat()}"}, "overrides": None, "mismatch": True,
            "expected": ["B-EXP"],
        }
    else:
        lot = ais["10"]
        pos = len(lot) - 1 - index % 3
        new = SAFE_CHARS[int(rng.integers(0, len(SAFE_CHARS)))]
        while new == lot[pos]:
            new = SAFE_CHARS[int(rng.integers(0, len(SAFE_CHARS)))]
        out["variants"]["barcode_mismatch"] = {
            "field_values": {"lot": f"LOT: {lot[:pos]}{new}{lot[pos + 1:]}"}, "overrides": None, "mismatch": True,
            "expected": ["B-LOT"],
        }
    name = "manufacturer" if index % 2 else "expiry"
    out["variants"]["missing_symbol"] = {
        "field_values": {}, "overrides": {name: {"draw": None}}, "mismatch": False,
        "expected": ["S-MFR" if name == "manufacturer" else "S-EXP"],
    }
    base_name = fields["product_name"]
    new_char = SAFE_CHARS[(index + 3) % len(SAFE_CHARS)]
    if new_char == base_name[-1]:
        new_char = SAFE_CHARS[(index + 4) % len(SAFE_CHARS)]
    out["variants"]["wrong_name"] = {
        "field_values": {"product_name": base_name[:-1] + new_char}, "overrides": None, "mismatch": False,
        "expected": ["P-NAME"],
    }
    return out


def generate(seeds: list[int], per_seed: int, out_dir: Path, conditions: tuple[str, ...] = CONDITIONS) -> None:
    """Render every base label x variant x condition into out_dir as png plus a json sidecar."""
    from PIL import Image

    from src.gen.augment import augment_label_detailed
    from src.gen.smoke_label import build_label

    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for seed in seeds:
        for index, sequence in enumerate(np.random.SeedSequence(seed).spawn(per_seed), start=1):
            rng = np.random.default_rng(sequence)
            base = _variants(index, rng)
            aug_seeds = {c: int(rng.integers(0, 2**32)) for c in CONDITIONS}
            aug_seeds["very_hard"] = aug_seeds["hard"]
            for kind, var in base["variants"].items():
                label_id = f"test_s{seed}_{index:03d}_{kind}"
                paths = build_label(
                    out_dir / "_source", label_id=label_id, field_values={**base["fields"], **var["field_values"]},
                    barcode_ais=base["ais"], symbol_overrides=var["overrides"],
                    allow_print_barcode_mismatch=var["mismatch"],
                )
                truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
                with Image.open(paths["image"]) as source:
                    for condition in conditions:
                        photo, _, _, _ = augment_label_detailed(source, condition, aug_seeds[condition])
                        stem = f"{label_id}_{condition}"
                        photo.save(out_dir / f"{stem}.png")
                        side = {
                            "stem": stem, "seed": seed, "index": index, "kind": kind, "condition": condition,
                            "expected": var["expected"], "printed": truth["fields"], "ais": base["ais"],
                            "true_fields": base["fields"], "symbols": [s["name"] for s in truth["symbols"]
                                                                       if s["name"] not in (var["overrides"] or {})],
                        }
                        (out_dir / f"{stem}.json").write_text(json.dumps(side, indent=2) + "\n", encoding="utf-8")
                        count += 1
    print(f"generated {count} images in {out_dir}")


# ----------------------------------------------------------------------------------- extract


def extract(in_dir: Path, shard: tuple[int, int] = (0, 1), reverse: bool = False) -> None:
    """Run the unchanged extractor on every image, in template and blind mode, and store the results.

    ``shard`` = (k, n) handles every n-th image starting at k, so several processes can share the work.
    Images that already have a result are skipped, so a run can be resumed.
    """
    from src.cv.extract import extract_label_modes

    out = in_dir / "extractions"
    out.mkdir(exist_ok=True)
    images = sorted(in_dir.glob("*.png"), reverse=reverse)[shard[0]::shard[1]]
    for i, image in enumerate(images, start=1):
        target = out / f"{image.stem}.json"
        if target.exists():
            continue
        try:
            results = extract_label_modes(image, modes=("template", "blind"))
            payload: dict[str, Any] = {m: results[m][0].model_dump(mode="json") for m in results}
        except Exception as error:  # an unrecoverable geometry error is a result, not a crash
            payload = {"error": f"{type(error).__name__}: {error}"}
        target.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        if i % 25 == 0:
            print(f"extracted {i}/{len(images)}", flush=True)
    print(f"extracted {len(images)} images")


# ----------------------------------------------------------------------------------- evaluate


GENERATOR_GTIN = "00000000000000"  # the generator's fixed test placeholder for AI 01


def _ais(side: dict[str, Any]) -> dict[str, str]:
    """AIs of a label: the sidecar holds 10, 17 and 21; AI 01 is the generator's placeholder."""
    return {"01": GENERATOR_GTIN, **side["ais"]}


def _record(side: dict[str, Any], kind: str):
    """Product record for one label: the true values, with the record-side injections applied."""
    rec = record_from_truth(side["true_fields"], _ais(side), rx_only=kind == "rx_missing")
    if kind == "udi_mismatch":
        assert gs1.check_digit_ok(OTHER_UDI_DI)
        rec = rec.model_copy(update={"udi_di": OTHER_UDI_DI})
    return rec


def _expected(side: dict[str, Any], kind: str) -> list[str]:
    return list(KIND_RULES[kind]) if kind in ("udi_mismatch", "rx_missing") else side["expected"]


def _run_layer(
    in_dir: Path, layer: str, retriever: Retriever, chunks: dict, settings: CheckerSettings
) -> list[dict[str, Any]]:
    """One record per (label, kind): which rules flagged, with needs_human, for one layer (oracle, template, blind)."""
    from src.common.schemas import LabelExtraction

    rows: list[dict[str, Any]] = []
    for path in sorted(in_dir.glob("test_*.json")):
        side = json.loads(path.read_text(encoding="utf-8"))
        kinds = [side["kind"]] + (["udi_mismatch", "rx_missing"] if side["kind"] == "clean" else [])
        for kind in kinds:
            row = {"stem": side["stem"], "kind": kind, "condition": side["condition"],
                   "expected": _expected(side, kind),
                   "error": None, "flags": {}, "n_flags": 0}
            if layer == "oracle":
                x = extraction_from_truth(side["stem"], side["printed"], _ais(side), symbols=tuple(side["symbols"]))
            else:
                stored = json.loads((in_dir / "extractions" / f"{side['stem']}.json").read_text(encoding="utf-8"))
                if "error" in stored:
                    row["error"] = stored["error"]
                    rows.append(row)
                    continue
                x = LabelExtraction.model_validate(stored[layer])
            result: CheckerResult = run_checks(x, _record(side, kind), settings=settings, retriever=retriever,
                                               chunks=chunks)
            row["flags"] = {f.rule_id: {"needs_human": f.needs_human, "severity": f.severity,
                                        "cited": bool(f.citations)} for f in result.findings}
            row["n_flags"] = len(result.findings)
            row["cited_ok"] = all(c.quote in chunks[c.chunk_id].text for f in result.findings for c in f.citations)
            rows.append(row)
    return rows


def _recall_table(rows: list[dict[str, Any]], conditions: tuple[str, ...]) -> list[str]:
    out = ["| kind | condition | n | flagged (any flag of the expected rule) | confident (needs_human false) | "
           "extraction raised |", "|---|---|---|---|---|---|"]
    for kind in KINDS[1:]:
        for cond in conditions:
            sel = [r for r in rows if r["kind"] == kind and r["condition"] == cond]
            hit = [r for r in sel if r["error"] is None and any(rule in r["flags"] for rule in r["expected"])]
            conf = [r for r in hit if any(rule in r["flags"] and not r["flags"][rule]["needs_human"]
                                          for rule in r["expected"])]
            out.append(f"| {kind} | {cond} | {len(sel)} | {wilson(len(hit), len(sel))} | {wilson(len(conf), len(sel))}"
                       f" | {sum(r['error'] is not None for r in sel)} |")
    return out


def _precision_table(rows: list[dict[str, Any]], conditions: tuple[str, ...]) -> list[str]:
    """Precision of each kind's rule group: expected rule flagged on injected labels over all group flags."""
    out = ["| kind | condition | TP | FP (group flags on labels not expecting that rule) | precision |",
           "|---|---|---|---|---|"]
    for kind, group in KIND_RULES.items():
        for cond in conditions:
            sel = [r for r in rows if r["condition"] == cond and r["error"] is None]
            tp = sum(1 for r in sel if r["kind"] == kind for rule in r["expected"] if rule in r["flags"])
            fp = sum(1 for r in sel for rule in group if rule in r["flags"] and rule not in r["expected"])
            out.append(f"| {kind} | {cond} | {tp} | {fp} | {wilson(tp, tp + fp)} |")
    return out


def _false_alarm_tables(rows: list[dict[str, Any]], conditions: tuple[str, ...]) -> list[str]:
    clean = [r for r in rows if r["kind"] == "clean"]
    rules = sorted({rule for r in clean for rule in r["flags"]})
    out = ["Share of clean labels (no injected error, true record) with at least one finding, per condition.", "",
           "| condition | n clean | any finding | any confident finding (needs_human false) | extraction raised |",
           "|---|---|---|---|---|"]
    for cond in conditions:
        sel = [r for r in clean if r["condition"] == cond]
        ok = [r for r in sel if r["error"] is None]
        any_f = sum(1 for r in ok if r["flags"])
        conf = sum(1 for r in ok if any(not v["needs_human"] for v in r["flags"].values()))
        out.append(f"| {cond} | {len(sel)} | {wilson(any_f, len(sel))} | {wilson(conf, len(sel))} | "
                   f"{len(sel) - len(ok)} |")
    out += ["", "Per rule (share of clean labels where that rule raised a finding):", "",
            "| rule | " + " | ".join(conditions) + " |", "|---|" + "---|" * len(conditions)]
    for rule in rules or ["(no rule raised a finding on any clean label)"]:
        cells = []
        for cond in conditions:
            sel = [r for r in clean if r["condition"] == cond]
            cells.append(wilson(sum(1 for r in sel if r["error"] is None and rule in r["flags"]), len(sel)))
        out.append(f"| {rule} | " + " | ".join(cells) + " |")
    return out


def _citation_table(rows: list[dict[str, Any]], retriever: Retriever, chunks: dict, k: int) -> list[str]:
    out = ["| rule | n findings | finding has a citation (hit@10 for the accepted section) | quote verbatim |",
           "|---|---|---|---|"]
    seen: dict[str, list[bool]] = defaultdict(list)
    for r in rows:
        for rule, info in r["flags"].items():
            if rule in CITATION_SPECS:
                seen[rule].append(info["cited"])
    for rule in sorted(CITATION_SPECS):
        hits = seen.get(rule, [])
        cite = find_citation(CITATION_SPECS[rule], retriever, chunks, k)
        out.append(f"| {rule} | {len(hits)} | {wilson(sum(hits), len(hits))} | "
                   f"{'ok' if cite and cite.quote in chunks[cite.chunk_id].text else 'NO CITATION'} |")
    return out


def _rank_table(chunks: dict, methods: tuple[str, ...]) -> list[str]:
    systems = {m: build_retriever(RetrievalSettings(method=m), chunks) for m in methods}
    out = ["| rule | accepted section | " + " | ".join(methods) + " |", "|---|---|" + "---|" * len(methods)]
    for rule, spec in sorted(CITATION_SPECS.items()):
        cells = []
        for m in methods:
            cite = find_citation(spec, systems[m], chunks, 10)
            cells.append(f"rank {cite.rank}" if cite else "not in top 10")
        out.append(f"| {rule} | {', '.join(sorted(spec.sections))} | " + " | ".join(cells) + " |")
    return out


def evaluate(in_dir: Path, report: Path, final: bool) -> None:
    """Run the checker on every layer and write a markdown report with Wilson intervals."""
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "src/checker", "docs/CHECKER_SPEC.md"],
                           capture_output=True, text=True).stdout.strip()
    if final and (dirty or report.exists()):
        raise SystemExit("final evaluation runs once on a clean tree: commit src/checker, use a new report path")
    settings = CheckerSettings()
    chunks = module_chunks(settings.retrieval.module)
    retriever = build_retriever(settings.retrieval, chunks)
    layers = ["oracle"] + (["template", "blind"] if (in_dir / "extractions").exists() else [])
    sides = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(in_dir.glob("test_*.json"))]
    seeds = sorted({s["seed"] for s in sides})
    bases = len({(s["seed"], s["index"]) for s in sides})
    md = [f"# Checker evaluation: {in_dir.name}", "",
          f"Commit {commit}{' (src/checker has uncommitted changes)' if dirty else ''}. Seeds {seeds}, "
          f"{bases} base labels, {len(sides)} images (5 image variants x 3 conditions per base; the udi_mismatch "
          f"and rx_missing kinds reuse the "
          f"clean image with a changed record). Retrieval: {settings.retrieval.echo()}. Symbol detector trusted: "
          f"{settings.symbol_detector_trusted}. Wilson 95% intervals, n in every cell, conditions never blended.", ""]
    for layer in layers:
        rows = _run_layer(in_dir, layer, retriever, chunks, settings)
        present = {s["condition"] for s in sides}
        conds = ("clean",) if layer == "oracle" else tuple(c for c in ALL_CONDITIONS if c in present)
        scope = {"oracle": "oracle extraction (perfect CV, so the photo condition does not apply; shown once)",
                 "template": "real extraction, template mode", "blind": "real extraction, blind mode"}[layer]
        md += [f"## Layer: {scope}", "", "### Recall on injected errors", ""]
        md += _recall_table(rows, conds)
        md += ["", "### Precision", ""] + _precision_table(rows, conds)
        md += ["", "### False alarms on clean labels", ""] + _false_alarm_tables(rows, conds)
        md += ["", "### Citations", ""] + _citation_table(rows, retriever, chunks, settings.retrieval.k)
        bad = [r["stem"] for r in rows if r.get("cited_ok") is False]
        md += ["", f"Citations whose quote is not a verbatim substring of its chunk: {len(bad)}", ""]
        (report.parent / f"{report.stem}_{layer}_rows.json").write_text(json.dumps(rows) + "\n", encoding="utf-8")
    md += ["## Citation retrieval by method (rank of the first accepted-section chunk, k = 10)", ""]
    md += _rank_table(chunks, ("bm25", "tfidf", "dense", "hybrid_rrf"))
    report.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {report}")


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--seeds", type=int, nargs="+", required=True)
    g.add_argument("--per-seed", type=int, default=17)
    g.add_argument("--conditions", nargs="+", default=list(CONDITIONS), choices=ALL_CONDITIONS)
    g.add_argument("--out", type=Path, required=True)
    e = sub.add_parser("extract")
    e.add_argument("--dir", type=Path, required=True)
    e.add_argument("--shard", type=int, nargs=2, default=(0, 1), metavar=("K", "N"))
    e.add_argument("--reverse", action="store_true")
    v = sub.add_parser("evaluate")
    v.add_argument("--dir", type=Path, required=True)
    v.add_argument("--report", type=Path, required=True)
    v.add_argument("--final", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "generate":
        generate(args.seeds, args.per_seed, args.out, tuple(args.conditions))
    elif args.cmd == "extract":
        extract(args.dir, tuple(args.shard), args.reverse)
    else:
        evaluate(args.dir, args.report, args.final)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
