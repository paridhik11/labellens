"""Rebuild a separate, pinned DailyMed medicine corpus without touching retrieval.

The source catalog is data/medicine/SOURCES.md. Original SPL XML, corpus.jsonl
and product metadata stay local. Run with --offline after the first download.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from src.common.schemas import Chunk
from src.crawl.chunk import compute_content_hash, split_text_into_chunks

ROOT = Path(__file__).resolve().parents[2]
NS = {"s": "urn:hl7-org:v3"}
BASE = "https://dailymed.nlm.nih.gov/dailymed/"
MAX_BYTES = 40_000_000
CATEGORIES = {
    "34067-9": "labelling", "34089-3": "labelling", "51945-4": "labelling",
    "34066-1": "warnings", "34070-3": "warnings", "34071-1": "warnings",
    "43685-7": "warnings", "34072-9": "warnings", "34076-0": "warnings",
    "50570-1": "warnings", "50569-3": "warnings", "50568-5": "warnings",
    "50567-7": "warnings", "50566-9": "warnings", "53414-9": "warnings",
    "50565-1": "warnings", "34068-7": "dosage",
}


def load_catalog(path: Path) -> list[dict[str, Any]]:
    """Read unique pinned SPL identities from the versioned source catalog."""
    match = re.search(r"<!-- medicine-catalog -->\s*```json\s*(.*?)\s*```", path.read_text(), re.S)
    if not match:
        raise ValueError("Medicine catalog block missing")
    entries = json.loads(match[1])
    seen = set()
    for entry in entries:
        identity = entry["setid"]
        if not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", identity):
            raise ValueError("Invalid SPL identity")
        if identity in seen or type(entry["version"]) is not int or entry["version"] < 1:
            raise ValueError("Duplicate identity or invalid version")
        if not re.fullmatch(r"[0-9a-f]{64}", entry["xml_sha256"]):
            raise ValueError("Invalid XML fingerprint")
        date.fromisoformat(entry["effective_date"])
        date.fromisoformat(entry["fetched"])
        seen.add(identity)
    if not entries:
        raise ValueError("Empty medicine catalog")
    return entries


def fetch_xml(entry: dict[str, Any]) -> bytes:
    """Download one bounded versioned archive and read its sole SPL in memory."""
    url = BASE + f"getFile.cfm?type=zip&setid={entry['setid']}&version={entry['version']}"
    request = Request(url, headers={"User-Agent": "LabelLens-medicine-research/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=60) as response:
                payload = response.read(MAX_BYTES + 1)
            break
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
    if len(payload) > MAX_BYTES:
        raise ValueError("Archive exceeds download limit")
    with ZipFile(BytesIO(payload)) as archive:
        infos = archive.infolist()
        if sum(info.file_size for info in infos) > 200_000_000:
            raise ValueError("Archive expansion exceeds limit")
        xmls = [info for info in infos if info.filename.lower().endswith(".xml")]
        if len(xmls) != 1:
            raise ValueError("Expected exactly one SPL document")
        return archive.read(xmls[0])


def parse_product(xml: bytes, entry: dict[str, Any]) -> tuple[list[Chunk], dict[str, Any]]:
    """Verify product identity and retain sourced section text, never generated advice.

    Own section bodies are read once, including nested warning/dosage sections.
    Section indexes preserve repeated LOINC codes. Five-word minimum, 200-word
    windows and 25-word overlap match the regulatory corpus convention.
    """
    if hashlib.sha256(xml).hexdigest() != entry["xml_sha256"]:
        raise ValueError("XML fingerprint mismatch")
    root = ET.fromstring(xml)
    code, identity = root.find("s:code", NS), root.find("s:setId", NS)
    version, effective = root.find("s:versionNumber", NS), root.find("s:effectiveTime", NS)
    if code is None or code.get("code") not in {"34390-5", "34391-3"}:
        raise ValueError("Expected a human medicine SPL, not device or veterinary data")
    if identity is None or identity.get("root") != entry["setid"]:
        raise ValueError("SPL identity mismatch")
    if version is None or version.get("value") != str(entry["version"]):
        raise ValueError("SPL version mismatch")
    actual_date = effective.get("value", "") if effective is not None else ""
    if actual_date != entry["effective_date"].replace("-", ""):
        raise ValueError("SPL effective date mismatch")
    product_names = root.findall(".//s:manufacturedProduct/s:manufacturedProduct/s:name", NS)
    product_names += root.findall(".//s:manufacturedMedicine/s:name", NS)
    names = {" ".join(" ".join(node.itertext()).split()) for node in product_names}
    if names != {entry["product_name"]}:
        raise ValueError("Product name mismatch or ambiguous product")
    url = BASE + f"drugInfo.cfm?setid={entry['setid']}&version={entry['version']}"
    categories = set()
    chunks = []
    section_metadata = []
    parents = {child: parent for parent in root.iter() for child in parent}
    for index, section in enumerate(root.findall(".//s:section", NS), 1):
        current = section
        category = None
        while current is not None and category is None:
            section_code = current.find("s:code", NS)
            category = CATEGORIES.get(section_code.get("code")) if section_code is not None else None
            current = parents.get(current)
        body = section.find("s:text", NS)
        if category is None or body is None:
            continue
        # Join at element boundaries so table cells and list items remain separate words.
        text = " ".join(" ".join(body.itertext()).split())
        if len(text.split()) < 5:
            continue
        title = section.find("s:title", NS)
        title_text = " ".join(" ".join(title.itertext()).split()) if title is not None else category
        code_node = section.find("s:code", NS)
        loinc = code_node.get("code", "unknown") if code_node is not None else "unknown"
        key = f"{category}/{loinc}/{index}"
        ids = []
        for number, piece in enumerate(split_text_into_chunks(text), 1):
            chunk_id = f"dailymed_{entry['setid']}_v{entry['version']}_s{index}_c{number}"
            chunks.append(Chunk(chunk_id=chunk_id, source="DailyMed", url=url,
                                title=f"{entry['product_name']}: {title_text}", section=key,
                                text=piece, fetched=entry["fetched"], hash=compute_content_hash(piece),
                                module="medicine"))
            ids.append(chunk_id)
        categories.add(category)
        section_metadata.append({"section": key, "title": title_text, "chunk_ids": ids})
    if categories != {"labelling", "warnings", "dosage"}:
        raise ValueError("Product must include labelling, warnings and dosage text")
    return chunks, {**entry, "url": url, "module": "medicine", "sections": section_metadata}


def build_corpus(
    entries: list[dict[str, Any]], output: Path, *, offline: bool = False,
    fetch: Callable[[dict[str, Any]], bytes] = fetch_xml,
) -> dict[str, Any]:
    """Validate every source before replacing the corpus and metadata files."""
    chunks, products = [], []
    source = output / "source"
    source.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        path = source / f"{entry['setid']}_v{entry['version']}.xml"
        if offline and not path.exists():
            raise FileNotFoundError(path)
        xml = path.read_bytes() if path.exists() else fetch(entry)
        rows, product = parse_product(xml, entry)
        path.write_bytes(xml)
        chunks.extend(rows)
        products.append(product)
    content = "".join(row.model_dump_json() + "\n" for row in chunks)
    (output / "corpus.jsonl").write_text(content, encoding="utf-8")
    (output / "products.json").write_text(json.dumps(products, indent=2) + "\n", encoding="utf-8")
    summary = {"products": len(products), "chunks": len(chunks), "module": "medicine",
               "corpus_sha256": hashlib.sha256(content.encode()).hexdigest(), "retrieval_evaluation": "NOT_RUN"}
    (output / "manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main(argv: list[str] | None = None) -> int:
    """Build the local corpus from a pinned, versioned sources list."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=ROOT / "data/medicine/SOURCES.md")
    parser.add_argument("--output", type=Path, default=ROOT / "data/medicine")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(build_corpus(load_catalog(args.sources), args.output, offline=args.offline), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
