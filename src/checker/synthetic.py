"""Builds extractions and product records from synthetic ground truth (the oracle layer of docs/CHECKER_SPEC.md).

An oracle extraction is what a perfect CV stage would return: every text line read with
confidence 1.0, the barcode decoded, and the expected symbols found. It measures the rules,
not the OCR. Nothing here allocates identifiers: AI 01 is whatever the generator used.
"""
from __future__ import annotations

from src.common.schemas import BarcodeResult, LabelExtraction, OcrBlock, ProductRecord, SymbolDetection

GS = "\x1d"
FIELD_ORDER = ("product_name", "manufacturer", "manufacturer_address", "model", "lot", "expiry")


def payload_from_ais(ais: dict[str, str]) -> str:
    """Raw GS1 element string as a decoder returns it: AIs 01, 17, 10, 21 with a group separator after AI 10."""
    return f"01{ais['01']}17{ais['17']}10{ais['10']}{GS}21{ais['21']}"


def extraction_from_truth(
    label_id: str, fields: dict[str, str], ais: dict[str, str], *,
    symbols: tuple[str, ...] = ("manufacturer", "expiry"), conf: float = 1.0, warnings: list[str] | None = None,
) -> LabelExtraction:
    """A perfect extraction: one OCR block per field, the barcode parsed, the named symbols detected."""
    blocks = [OcrBlock(text=text, bbox=(10.0, 10.0 + 20 * i, 200.0, 18.0), conf=conf)
              for i, text in enumerate(fields[name] for name in FIELD_ORDER if name in fields)]
    return LabelExtraction(
        label_id=label_id, fields=dict(fields), warnings=list(warnings or []), ocr_blocks=blocks,
        barcodes=[BarcodeResult(type="DataMatrix", raw=payload_from_ais(ais), parsed=dict(ais))],
        symbols=[SymbolDetection(name=n, bbox=(0.0, 0.0, 10.0, 10.0), conf=1.0) for n in symbols],
    )


def record_from_truth(fields: dict[str, str], ais: dict[str, str], *, product_id: str = "prd_test",
                      rx_only: bool = False) -> ProductRecord:
    """The product record a label was made from: printed text without keys, UDI-DI equal to AI 01 of the test label."""
    model = fields["model"].split(":", 1)[-1].strip()
    return ProductRecord(
        product_id=product_id, name=fields["product_name"], model=model, manufacturer=fields["manufacturer"],
        manufacturer_address=fields["manufacturer_address"], udi_di=ais["01"],
        extra={"rx_only": "true"} if rx_only else {},
    )
