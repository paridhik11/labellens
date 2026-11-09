"""Chunking pipeline for regulatory texts.

Transforms parsed eCFR regulatory sections into standard Chunk objects,
splitting long sections into ~200-word pieces with small overlap and computing
content hashes for change tracking.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional

from src.common.schemas import Chunk
from src.crawl.ecfr import parse_sections_from_xml


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
) -> list[Chunk]:
    """Converts a parsed section dictionary into one or more Chunk schema objects."""
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
            source="FDA",
            url=url,
            title=title,
            section=sec_num,
            text=piece,
            fetched=fetch_date,
            hash=c_hash,
            module="device",
        )
        chunks.append(chunk)

    return chunks


def build_regulatory_chunks(
    xml_paths: list[str | Path],
    fetch_date: Optional[str] = None,
    max_words: int = 200,
    overlap: int = 25,
) -> list[Chunk]:
    """Reads raw XML files from disk and generates a flattened list of Chunk objects."""
    date_val = fetch_date or datetime.date.today().isoformat()
    all_chunks: list[Chunk] = []

    for path_item in xml_paths:
        p = Path(path_item)
        if not p.exists():
            continue
        match = re.search(r"part(\d+)", p.name)
        part_num = match.group(1) if match else "801"
        sections = parse_sections_from_xml(p.read_bytes())
        for sec in sections:
            sec_chunks = section_to_chunks(
                sec,
                part=part_num,
                fetch_date=date_val,
                max_words=max_words,
                overlap=overlap,
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

    parser = argparse.ArgumentParser(description="Chunk eCFR XML regulatory documents into JSONL.")
    parser.add_argument(
        "--raw-files",
        nargs="+",
        default=["data/raw/ecfr_title21_part801.xml", "data/raw/ecfr_title21_part830.xml"],
        help="Paths to raw eCFR XML files",
    )
    parser.add_argument(
        "--out",
        default="data/processed/regs.jsonl",
        help="Destination JSONL path",
    )
    parser.add_argument("--max-words", type=int, default=200, help="Target max words per chunk")
    parser.add_argument("--overlap", type=int, default=25, help="Word overlap between consecutive chunks")
    args = parser.parse_args()

    xml_files = [Path(f) for f in args.raw_files]
    chunks = build_regulatory_chunks(
        xml_files,
        fetch_date="2026-11-09",
        max_words=args.max_words,
        overlap=args.overlap,
    )
    write_chunks_jsonl(chunks, args.out)

    lengths = [len(c.text.split()) for c in chunks]
    avg_len = sum(lengths) / len(lengths) if lengths else 0.0

    print(f"Total chunks written to {args.out}: {len(chunks)}")
    print(f"Average chunk length: {avg_len:.1f} words")
    print(f"Min length: {min(lengths)} words, Max length: {max(lengths)} words")
    print("\n--- Sample Chunk 1 ---")
    print(chunks[0].model_dump_json(indent=2))
    print("\n--- Sample Chunk 2 ---")
    print(chunks[min(15, len(chunks) - 1)].model_dump_json(indent=2))
    print("\n--- Sample Chunk 3 ---")
    print(chunks[-1].model_dump_json(indent=2))


if __name__ == "__main__":
    main()
