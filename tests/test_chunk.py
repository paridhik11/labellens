"""Tests for regulatory chunking pipeline."""
import json
from pathlib import Path

from src.crawl.chunk import (
    compute_content_hash,
    section_to_chunks,
    split_text_into_chunks,
    write_chunks_jsonl,
)


def test_split_text_into_chunks_short() -> None:
    text = "Short text with only six words."
    chunks = split_text_into_chunks(text, max_words=20, overlap=5)
    assert chunks == [text]


def test_split_text_into_chunks_long() -> None:
    words = [f"word{i}" for i in range(100)]
    text = " ".join(words)
    chunks = split_text_into_chunks(text, max_words=40, overlap=10)
    assert len(chunks) == 3
    # First chunk has 40 words (0..39)
    assert len(chunks[0].split()) == 40
    # Second chunk starts at 40 - 10 = 30 and has 40 words (30..69)
    assert chunks[1].split()[0] == "word30"
    assert len(chunks[1].split()) == 40
    # Third chunk starts at 60 and ends at 99 (40 words)
    assert chunks[2].split()[0] == "word60"


def test_compute_content_hash() -> None:
    h1 = compute_content_hash("Some regulatory text")
    h2 = compute_content_hash("Some regulatory text")
    h3 = compute_content_hash("Different text")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 16


def test_section_to_chunks_single() -> None:
    sec = {
        "section": "801.1",
        "title": "General labeling.",
        "text": "Device label must state manufacturer.",
        "url": "https://example.org/801.1",
    }
    chunks = section_to_chunks(sec, part="801", fetch_date="2026-11-09", max_words=200)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.chunk_id == "fda_21cfr801_s801.1"
    assert c.source == "FDA"
    assert c.section == "801.1"
    assert c.module == "device"
    assert c.fetched == "2026-11-09"
    assert c.hash != ""


def test_section_to_chunks_multiple() -> None:
    long_text = " ".join(["word"] * 300)
    sec = {
        "section": "801.109",
        "title": "Prescription devices.",
        "text": long_text,
    }
    chunks = section_to_chunks(sec, part="801", fetch_date="2026-11-09", max_words=200, overlap=25)
    assert len(chunks) > 1
    assert chunks[0].chunk_id == "fda_21cfr801_s801.109_c1"
    assert chunks[1].chunk_id == "fda_21cfr801_s801.109_c2"


def test_write_chunks_jsonl(tmp_path: Path) -> None:
    sec = {
        "section": "830.20",
        "title": "UDI requirement.",
        "text": "Every medical device must bear a UDI.",
    }
    chunks = section_to_chunks(sec, part="830", fetch_date="2026-11-09")
    out_file = tmp_path / "regs_test.jsonl"
    write_chunks_jsonl(chunks, out_file)

    lines = out_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["chunk_id"] == "fda_21cfr830_s830.20"
    assert data["text"] == "Every medical device must bear a UDI."

def test_section_to_chunks_medicine_module() -> None:
    """Verifies that module and source are propagated into Chunk objects."""
    sec = {
        "section": "201.100",
        "title": "Prescription drugs.",
        "text": "Every prescription drug must bear adequate directions for use.",
        "url": "https://example.org/201.100",
    }
    chunks = section_to_chunks(
        sec, part="201", fetch_date="2026-11-09", module="medicine", source="FDA"
    )
    assert len(chunks) == 1
    c = chunks[0]
    assert c.module == "medicine"
    assert c.source == "FDA"
    assert c.chunk_id == "fda_21cfr201_s201.100"


def test_section_to_chunks_skips_under_min_words() -> None:
    """Verifies that sections under min_words threshold (e.g. [Reserved]) are skipped."""
    reserved_sec = {
        "section": "820.5",
        "title": "[Reserved]",
        "text": "[Reserved]",
    }
    chunks = section_to_chunks(reserved_sec, part="820", min_words=5)
    assert chunks == []


def test_section_to_chunks_keeps_exact_min_words() -> None:
    """Verifies that sections with at least min_words words are retained."""
    short_sec = {
        "section": "211.44",
        "title": "Lighting.",
        "text": "Adequate lighting shall be provided.",
    }
    chunks = section_to_chunks(short_sec, part="211", min_words=5)
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "fda_21cfr211_s211.44"
