"""The NDC to product table, built from the pinned SPL XML files of the corpus (every package NDC of each set id)."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from src.ndc.codes import from_segments

NDC_SYSTEM = "2.16.840.1.113883.6.69"
TABLE_PATH = Path(__file__).with_name("ndc_table.json")
NS = "{urn:hl7-org:v3}"


def spl_package_ndcs(xml_path: Path) -> list[str]:
    """Every NDC in one SPL file (product and package level), normalised to 11 digits, in document order."""
    root = ET.parse(xml_path).getroot()
    out: list[str] = []
    for code in root.iter(NS + "code"):
        if code.get("codeSystem") != NDC_SYSTEM or not code.get("code"):
            continue
        parts = code.get("code", "").split("-")
        if len(parts) == 3 and (norm := from_segments(*parts)):
            out.append(norm)
    return list(dict.fromkeys(out))


def build_table(xml_dir: Path, products_json: Path) -> dict:
    """``{"ndc11": {code: [setid]}, "setids": {...}}`` for the pinned products, with the XML hash as provenance."""
    products = json.loads(products_json.read_text(encoding="utf-8"))
    table: dict[str, list[str]] = {}
    meta: dict[str, dict] = {}
    for p in products:
        files = sorted(xml_dir.glob(f"{p['setid']}_v*.xml"))
        if not files:
            raise SystemExit(f"no pinned XML for {p['setid']}")
        if hashlib.sha256(files[-1].read_bytes()).hexdigest() != p["xml_sha256"]:
            raise SystemExit(f"hash mismatch for {files[-1].name}")
        codes = spl_package_ndcs(files[-1])
        meta[p["setid"]] = {"name": p["product_name"], "xml_sha256": p["xml_sha256"], "ndcs": codes}
        for c in codes:
            table.setdefault(c, [])
            if p["setid"] not in table[c]:
                table[c].append(p["setid"])
    return {"ndc11": table, "setids": meta}


def load_table(path: Path = TABLE_PATH) -> dict[str, list[str]]:
    """The committed table as ``{ndc11: [setid]}``."""
    return json.loads(path.read_text(encoding="utf-8"))["ndc11"]


if __name__ == "__main__":
    import sys

    result = build_table(Path(sys.argv[1]), Path(sys.argv[2]))
    TABLE_PATH.write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(len(result["ndc11"]), "NDCs for", len(result["setids"]), "products;",
          sum(1 for v in result["ndc11"].values() if len(v) > 1), "shared by more than one product")
