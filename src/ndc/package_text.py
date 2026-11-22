"""Package-label text of each corpus product (SPL principal display panel sections) and the BM25 text ranking.

The text comes from the PINNED SPL XML: every section coded 51945-4 (package label, principal display panel) plus
the product name and generic name of the set id. The ranking uses our own BM25 (``src.ir.bm25``) with the default
parameters, queried with all OCR tokens of the photo. This is a candidate list only: it never accepts a product.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from src.ir.bm25 import BM25Retriever, InvertedIndex

NS = "{urn:hl7-org:v3}"
TEXT_PATH = Path(__file__).with_name("package_text.json")
PDP_CODE = "51945-4"


def pdp_text(xml_path: Path) -> str:
    """All text inside the package-label (51945-4) sections of one SPL file, whitespace-normalised."""
    root = ET.parse(xml_path).getroot()
    parts: list[str] = []
    for section in root.iter(NS + "section"):
        code = section.find(NS + "code")
        if code is not None and code.get("code") == PDP_CODE:
            parts.append(" ".join("".join(section.itertext()).split()))
    return " ".join(parts)


def build(xml_dir: Path, products_json: Path) -> dict[str, dict[str, str]]:
    """``{setid: {"name", "text"}}`` for the pinned products."""
    out: dict[str, dict[str, str]] = {}
    for p in json.loads(products_json.read_text(encoding="utf-8")):
        files = sorted(xml_dir.glob(f"{p['setid']}_v*.xml"))
        root = ET.parse(files[-1]).getroot()
        generic = " ".join(g.text or "" for g in root.iter(NS + "genericMedicine") for g in g.iter(NS + "name"))
        text = pdp_text(files[-1])
        out[p["setid"]] = {"name": p["product_name"], "text": f"{p['product_name']} {generic} {text}".strip()}
    return out


def make_retriever(texts: dict[str, dict[str, str]]) -> BM25Retriever:
    """BM25 over the package-label texts (document id = set id)."""
    index = InvertedIndex().build([(setid, v["text"]) for setid, v in texts.items()])
    return BM25Retriever(index)


def load_texts(path: Path = TEXT_PATH) -> dict[str, dict[str, str]]:
    """The committed derived texts."""
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys

    data = build(Path(sys.argv[1]), Path(sys.argv[2]))
    TEXT_PATH.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print({v["name"]: len(v["text"].split()) for v in data.values()})
