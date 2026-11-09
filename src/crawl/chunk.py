"""Chunking pipeline for regulatory texts.

Transforms parsed eCFR regulatory sections into standard Chunk objects,
splitting long sections into ~200-word pieces with small overlap and computing
content hashes for change tracking. The module ("device" or "medicine") and
source name are caller-supplied, not hardcoded.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path
from typing import Literal, Optional

from src.common.schemas import Chunk
from src.crawl.ecfr import (
    DEFAULT_DEVICE_PARTS,
    DEFAULT_MEDICINE_PARTS,
    parse_sections_from_xml,
)

# Map part numbers to their module assignment.
PART_MODULE: dict[int, Literal["device", "medicine"]] = {
    p: "device" for p in DEFAULT_DEVICE_PARTS
} | {p: "medicine" for p in DEFAULT_MEDICINE_PARTS}


def split_text_into_chunks(text: str, max_words: int = 200, overlap: int = 25) -> list[str]:
    """Splits text into word windows of max_words with an overlap between consecutive chunks.

    If the text has fewer than or equal to max_words words, returns [text] without splitting.
    """
    words = text.split()
    if len(words) <= max_words:
        return [text]

    step = max(1, max_words - overlap)
    chunks: list[str] = []
    for i in range(0, len(words), step):
        window = words[i : i + max_words]
        if window:
            chunks.append(" ".join(window))
        if i + max_words >= len(words):
            break
    return chunks


def compute_content_hash(text: str) -> str:
    """Computes a 16-character hexadecimal SHA-256 hash for the given text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def section_to_chunks(
    section: dict,
    part: str | int,
    fetch_date: str = "2026-11-09",
    max_words: int = 200,
    overlap: int = 25,
    module: Literal["device", "medicine"] = "device",
    source: str = "FDA",
) -> list[Chunk]:
    """Converts a parsed section dictionary into one or more Chunk schema objects.

    Args:
        section: Dict with keys section, title, text, url from parse_sections_from_xml.
        part: CFR part number (string or int) used to build the chunk_id.
        fetch_date: ISO date string when the XML was fetched.
        max_words: Max tokens per chunk window.
        overlap: Word overlap between consecutive windows.
        module: Regulatory module -- "device" for device parts, "medicine" for drug parts.
        source: Corpus source label (e.g. "FDA").
    """
    sec_num = str(section.get("section", "")).strip()
    sec_text = str(section.get("text", "")).strip()
    title = str(section.get("title", "")).strip()
    url = str(section.get("url", "")).strip()
    if not url and sec_num:
        url = f"https://www.ecfr.gov/current/title-21/section-{sec_num}"

    pieces = split_text_into_chunks(sec_text, max_words=max_words, overlap=overlap)
    chunks: list[Chunk] = []

    for idx, piece in enumerate(pieces, start=1):
        if len(pieces) == 1:
            chunk_id = f"fda_21cfr{part}_s{sec_num}"
        else:
            chunk_id = f"fda_21cfr{part}_s{sec_num}_c{idx}"

        c_hash = compute_content_hash(piece)
        chunk = Chunk(
            chunk_id=chunk_id,
            source=source,
            url=url,
            title=title,
            section=sec_num,
            text=piece,
            fetched=fetch_date,
            hash=c_hash,
            module=module,
        )
        chunks.append(chunk)

    return chunks


def build_regulatory_chunks(
    xml_paths: list[str | Path],
    fetch_date: Optional[str] = None,
    max_words: int = 200,
    overlap: int = 25,
) -> list[Chunk]:
    """Reads raw XML files from disk and generates a flattened list of Chunk objects.

    The module (device/medicine) and source label are inferred from the part number
    using PART_MODULE. Unknown parts default to module='device' and source='FDA'.
    """
    date_val = fetch_date or datetime.date.today().isoformat()
    all_chunks: list[Chunk] = []

    for path_item in xml_paths:
        p = Path(path_item)
        if not p.exists():
            continue
        match = re.search(r"part(\d+)", p.name)
        part_num = match.group(1) if match else "801"
        part_int = int(part_num)
        mod: Literal["device", "medicine"] = PART_MODULE.get(part_int, "device")
        sections = parse_sections_from_xml(p.read_bytes())
        for sec in sections:
            sec_chunks = section_to_chunks(
                sec,
                part=part_num,
                fetch_date=date_val,
                max_words=max_words,
                overlap=overlap,
                module=mod,
                source="FDA",
            )
            all_chunks.extend(sec_chunks)

    return all_chunks


def write_chunks_jsonl(chunks: list[Chunk], out_path: str | Path) -> None:
    """Writes a list of Chunk objects to a JSON Lines file in UTF-8."""
    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(chunk.model_dump_json() + "\n")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Build default list of raw files from all known device + medicine parts.
    _all_parts = list(DEFAULT_DEVICE_PARTS) + list(DEFAULT_MEDICINE_PARTS)
    _default_files = [f"data/raw/ecfr_title21_part{p}.xml" for p in _all_parts]

    parser = argparse.ArgumentParser(description="Chunk eCFR XML regulatory documents into JSONL.")
    parser.add_argument(
        "--raw-files",
        nargs="+",
        default=_default_files,
        help="Paths to raw eCFR XML files (default: all device + medicine parts)",
    )
    parser.add_argument(
        "--out",
        default="data/processed/regs.jsonl",
        help="Destination JSONL path",
    )
    parser.add_argument("--max-words", type=int, default=200, help="Target max words per chunk")
    parser.add_argument(
        "--overlap", type=int, default=25, help="Word overlap between consecutive chunks"
    )
    args = parser.parse_args()

    xml_files = [Path(f) for f in args.raw_files]
    # Only include files that exist on disk.
    existing = [f for f in xml_files if f.exists()]
    missing = [f for f in xml_files if not f.exists()]
    if missing:
        print(f"Warning: {len(missing)} file(s) not found, skipping: {[str(m) for m in missing]}")

    chunks = build_regulatory_chunks(
        existing,
        fetch_date=datetime.date.today().isoformat(),
        max_words=args.max_words,
        overlap=args.overlap,
    )
    write_chunks_jsonl(chunks, args.out)

    if not chunks:
        print("No chunks produced. Check that raw XML files are present.")
        return

    # Per-part stats.
    from collections import defaultdict
    per_part: dict[str, list[int]] = defaultdict(list)
    for c in chunks:
        # Extract part number from chunk_id e.g. fda_21cfr801_s801.1 -> 801
        m = re.search(r"21cfr(\d+)", c.chunk_id)
        part_key = m.group(1) if m else "?"
        per_part[part_key].append(len(c.text.split()))

    print(f"\nChunks per part:")
    for part_key in sorted(per_part, key=int):
        lens = per_part[part_key]
        print(f"  Part {part_key}: {len(lens)} chunks, avg {sum(lens)/len(lens):.0f} words")

    all_lengths = [len(c.text.split()) for c in chunks]
    avg_len = sum(all_lengths) / len(all_lengths)
    print(f"\nTotal chunks: {len(chunks)}")
    print(f"Average chunk length: {avg_len:.1f} words")

    sorted_chunks = sorted(chunks, key=lambda c: len(c.text.split()))
    print("\n5 shortest chunks:")
    for c in sorted_chunks[:5]:
        print(f"  [{c.chunk_id}] {len(c.text.split())} words")
    print("\n5 longest chunks:")
    for c in sorted_chunks[-5:]:
        print(f"  [{c.chunk_id}] {len(c.text.split())} words")


if __name__ == "__main__":
    main()
