"""Crawler for the Electronic Code of Federal Regulations (eCFR) API.

Fetches specified 21 CFR parts from the official public eCFR API endpoints,
with retries and rate limiting. The part list is configurable; callers supply
the parts they need. Default parts cover medical-device labeling, MDR, recalls,
registration, IVD, IDE, QSR, and pharmaceutical labeling/cGMP.
"""
from __future__ import annotations

import argparse
import datetime
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

DEFAULT_USER_AGENT = "LabelLensCourseProject/1.0 (cse.student.ir.project@university.edu)"
BASE_API_URL = "https://www.ecfr.gov/api/versioner/v1"

# Canonical part coverage descriptions, keyed by part number.
# Verified 2026-11-05 against eCFR API (all returned HTTP 200).
PART_COVERAGE: dict[int, str] = {
    # Device parts
    801: "Device labeling -- general requirements for labels on medical devices",
    803: "Medical Device Reporting (MDR) -- mandatory reporting of device malfunctions, serious injuries, and deaths",
    806: "Medical Devices -- Corrections and Removals (recall/correction reporting to FDA)",
    807: "Establishment Registration and Device Listing for manufacturers and distributors",
    809: "In Vitro Diagnostic (IVD) Products for Human Use -- labeling and performance standards",
    812: "Investigational Device Exemptions (IDE) -- rules for using unapproved devices in clinical studies",
    820: "Quality System Regulation (QSR) -- device quality management and manufacturing requirements",
    830: "Unique Device Identification (UDI) -- labeling and database submission rules",
    # Medicine parts
    201: "Drug Labeling -- comprehensive general labeling requirements for human prescription and OTC drugs",
    208: "Medication Guides for Prescription Drug Products -- when and how to distribute patient medication guides",
    211: "Current Good Manufacturing Practice (cGMP) for Finished Pharmaceuticals",
}

# Default parts fetched when none are specified on the command line.
DEFAULT_DEVICE_PARTS: list[int] = [801, 803, 806, 807, 809, 812, 820, 830]
DEFAULT_MEDICINE_PARTS: list[int] = [201, 208, 211]
DEFAULT_ALL_PARTS: list[int] = DEFAULT_DEVICE_PARTS + DEFAULT_MEDICINE_PARTS


def create_resilient_session(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    user_agent: str = DEFAULT_USER_AGENT,
) -> requests.Session:
    """Creates a requests.Session configured with automatic retries and custom headers."""
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": user_agent, "Accept": "application/xml, application/json"})
    return session


def get_title_issue_date(
    title: int = 21,
    session: Optional[requests.Session] = None,
) -> str:
    """Retrieves the latest valid issue date for a given CFR title from the eCFR API.

    Falls back to today's date if the API call is unavailable.
    """
    s = session or create_resilient_session()
    url = f"{BASE_API_URL}/titles.json"
    try:
        resp = s.get(url, timeout=15)
        if resp.status_code == 200:
            titles = resp.json().get("titles", [])
            for t in titles:
                if t.get("number") == title:
                    date_val = (
                        t.get("up_to_date_as_of")
                        or t.get("latest_amended_on")
                        or t.get("latest_issue_date")
                    )
                    if date_val:
                        return str(date_val)
    except Exception:
        pass
    return datetime.date.today().isoformat()


def fetch_part_xml(
    title: int,
    part: int,
    date: Optional[str] = None,
    session: Optional[requests.Session] = None,
) -> bytes:
    """Fetches the full XML text of a specific title and part for a given date."""
    s = session or create_resilient_session()
    issue_date = date or get_title_issue_date(title=title, session=s)
    url = f"{BASE_API_URL}/full/{issue_date}/title-{title}.xml"
    params = {"part": str(part)}
    resp = s.get(url, params=params, timeout=45)
    resp.raise_for_status()
    return resp.content


def clean_section_title(raw_title: str) -> str:
    """Removes leading section symbols and section numbering from heading text."""
    cleaned = raw_title.strip()
    cleaned = re.sub(r"^[\u00a7\s\d.]+", "", cleaned).strip()
    return cleaned if cleaned else raw_title.strip()


def parse_sections_from_xml(xml_content: str | bytes) -> list[dict]:
    """Parses section elements (DIV8 tags) from eCFR XML content.

    Returns a list of dicts with section, title, citation, text, and paragraphs count.
    """
    root = ET.fromstring(xml_content)
    sections: list[dict] = []
    for div in root.findall(".//DIV8"):
        if div.get("TYPE", "").upper() != "SECTION":
            continue
        sec_num = div.get("N", "").strip()
        head_elem = div.find("HEAD")
        raw_head = "".join(head_elem.itertext()).strip() if head_elem is not None else ""
        cleaned_head = clean_section_title(raw_head)

        paragraphs: list[str] = []
        for p in div.findall(".//P"):
            p_text = "".join(p.itertext()).strip()
            if p_text:
                paragraphs.append(p_text)

        full_text = "\n\n".join(paragraphs) if paragraphs else cleaned_head
        citation = f"21 CFR {sec_num}" if sec_num else ""
        canonical_url = (
            f"https://www.ecfr.gov/current/title-21/section-{sec_num}" if sec_num else ""
        )

        sections.append(
            {
                "section": sec_num,
                "title": cleaned_head,
                "citation": citation,
                "url": canonical_url,
                "text": full_text,
                "paragraphs": len(paragraphs),
            }
        )
    return sections


def crawl_ecfr_parts(
    parts: Optional[list[int]] = None,
    out_dir: str | Path = "data/raw",
    delay_seconds: float = 1.0,
    session: Optional[requests.Session] = None,
) -> dict[int, list[dict]]:
    """Crawls specified parts from 21 CFR, saves raw XML to disk, and extracts sections.

    Args:
        parts: List of CFR part numbers to fetch. Defaults to all device + medicine parts.
        out_dir: Directory to write raw XML files.
        delay_seconds: Polite delay between requests.
        session: Optional pre-built requests.Session for testability.

    Returns:
        Mapping from part number to list of parsed section dicts.
    """
    target_parts = parts if parts is not None else DEFAULT_ALL_PARTS
    output_path = Path(out_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    s = session or create_resilient_session()
    date_val = get_title_issue_date(title=21, session=s)
    results: dict[int, list[dict]] = {}

    for idx, part in enumerate(target_parts):
        if idx > 0 and delay_seconds > 0:
            time.sleep(delay_seconds)
        raw_xml = fetch_part_xml(title=21, part=part, date=date_val, session=s)
        save_file = output_path / f"ecfr_title21_part{part}.xml"
        save_file.write_bytes(raw_xml)

        parsed = parse_sections_from_xml(raw_xml)
        results[part] = parsed

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch 21 CFR parts from the eCFR API. Default: device + medicine corpus."
    )
    parser.add_argument(
        "--parts",
        nargs="+",
        type=int,
        default=DEFAULT_ALL_PARTS,
        help=(
            "CFR parts to fetch (default: device corpus 801 803 806 807 809 812 820 830"
            " + medicine 201 208 211)"
        ),
    )
    parser.add_argument("--out", default="data/raw", help="Directory to save raw XML responses")
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Rate limit delay in seconds between calls"
    )
    args = parser.parse_args()

    print(f"Fetching 21 CFR parts {args.parts} from eCFR API...")
    print("Verified coverage per part:")
    for p in args.parts:
        desc = PART_COVERAGE.get(p, "No description available")
        print(f"  Part {p}: {desc}")
    print()

    results = crawl_ecfr_parts(parts=args.parts, out_dir=args.out, delay_seconds=args.delay)
    total_sections = 0
    for part, sections in results.items():
        print(f"Part {part}: fetched and parsed {len(sections)} sections")
        total_sections += len(sections)
    print(f"Total sections fetched: {total_sections}")


if __name__ == "__main__":
    main()
