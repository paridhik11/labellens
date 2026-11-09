"""Tests for eCFR crawler parsing and utilities."""
import xml.etree.ElementTree as ET

from src.crawl.ecfr import (
    clean_section_title,
    create_resilient_session,
    parse_sections_from_xml,
)

SAMPLE_XML_FIXTURE = """<?xml version="1.0"?>
<DIV5 N="801" TYPE="PART">
  <HEAD>PART 801 - LABELING</HEAD>
  <DIV8 N="801.1" TYPE="SECTION">
    <HEAD>§ 801.1 Medical devices; name and place of business.</HEAD>
    <P>(a) The label of a device shall specify name and place of business.</P>
    <P>(b) The requirement for declaration includes address.</P>
  </DIV8>
  <DIV8 N="801.3" TYPE="SECTION">
    <HEAD>§ 801.3 Definitions.</HEAD>
    <P>For the purposes of this part, automatic identification means barcodes.</P>
  </DIV8>
</DIV5>
"""


def test_clean_section_title() -> None:
    raw = "§ 801.1 Medical devices; name and place of business."
    cleaned = clean_section_title(raw)
    assert cleaned == "Medical devices; name and place of business."


def test_parse_sections_from_xml() -> None:
    sections = parse_sections_from_xml(SAMPLE_XML_FIXTURE)
    assert len(sections) == 2
    sec1 = sections[0]
    assert sec1["section"] == "801.1"
    assert sec1["title"] == "Medical devices; name and place of business."
    assert sec1["citation"] == "21 CFR 801.1"
    assert sec1["paragraphs"] == 2
    assert "The label of a device" in sec1["text"]
    assert "The requirement for declaration" in sec1["text"]

    sec2 = sections[1]
    assert sec2["section"] == "801.3"
    assert sec2["paragraphs"] == 1
    assert "automatic identification" in sec2["text"]


def test_create_resilient_session() -> None:
    session = create_resilient_session(max_retries=2, backoff_factor=0.1)
    assert "LabelLens" in session.headers["User-Agent"]
    assert "https://" in session.adapters
