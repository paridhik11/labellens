"""Show that CV output plugs into the shared schemas without changing ``schemas.py``.

Run from the repo root:

    python -m src.cv.integration

It renders five synthetic test labels, runs ``extract_label`` in blind mode on
each, prints the validated ``LabelExtraction``, and passes the result on to the
shared ``ProductRecord`` and ``Flag`` classes.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from src.common.schemas import Flag, LabelExtraction, ProductRecord
from src.cv.consistency import check_extraction
from src.cv.fields import strip_key


def to_product_record(extraction: LabelExtraction) -> ProductRecord:
    """Build a ``ProductRecord`` from what was read on one label.

    Printed keys are removed (``REF: TEST-M001`` becomes ``TEST-M001``). The
    UDI-DI is copied from AI 01 of the barcode only when exactly one barcode
    was decoded; it is never made up. On the synthetic labels it is the
    all-zero test placeholder, not an allocated identifier. Lot and expiry are
    kept in ``extra`` because ``ProductRecord`` has no fields for them.
    """
    fields = extraction.fields
    parsed = extraction.barcodes[0].parsed if len(extraction.barcodes) == 1 else {}
    extra = {key: strip_key(fields[key]) for key in ("lot", "expiry") if key in fields}
    if "21" in parsed:
        extra["serial"] = parsed["21"]
    return ProductRecord(
        product_id=f"test_product_{extraction.label_id}",
        name=fields.get("product_name", ""),
        model=strip_key(fields["model"]) if "model" in fields else "",
        manufacturer=fields.get("manufacturer", ""),
        manufacturer_address=fields.get("manufacturer_address", ""),
        udi_di=parsed.get("01", ""),
        extra=extra,
    )


def run_demo(
    count: int = 5, seed: int = 7, condition: str = "moderate"
) -> list[tuple[LabelExtraction, ProductRecord, list[Flag]]]:
    """Generate ``count`` test labels, extract them and return validated shared objects."""
    from src.cv.extract import extract_label
    from src.gen.generate_dataset import generate_dataset

    results = []
    with TemporaryDirectory(prefix="labellens_integration_") as temporary:
        folder = Path(temporary)
        generate_dataset(folder, seed=seed, labels_per_condition=count, conditions=(condition,))
        for image in sorted((folder / condition).glob("*.png")):
            extraction = LabelExtraction.model_validate(
                extract_label(image, mode="blind", postcorrect=True).model_dump()
            )
            record = ProductRecord.model_validate(to_product_record(extraction).model_dump())
            flags = [Flag.model_validate(flag.model_dump()) for flag in check_extraction(extraction)]
            results.append((extraction, record, flags))
    return results


def main(argv: list[str] | None = None) -> int:
    """Print the extraction, product record and flags of five synthetic labels."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--condition", default="moderate")
    args = parser.parse_args(argv)
    results = run_demo(args.count, args.seed, args.condition)
    for extraction, record, flags in results:
        print(f"=== {extraction.label_id} ===")
        print("LabelExtraction (validated):")
        print(extraction.model_dump_json(indent=2, exclude={"ocr_blocks"}))
        print(f"ocr_blocks: {len(extraction.ocr_blocks)} text lines (omitted here)")
        print("ProductRecord (validated):")
        print(record.model_dump_json(indent=2))
        print(f"Flags: {[flag.model_dump() for flag in flags]}")
    print(f"{len(results)} labels passed through LabelExtraction, ProductRecord and Flag without schema changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
