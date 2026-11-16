"""Rebuild the reviewed device-symbol collection from the catalog in SOURCES.md.

Run from the repository root with the CV environment. Artwork and annotations
remain local. No OCR or detection metric is computed by this data collector.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from http.client import HTTPException
from io import BytesIO
from pathlib import Path
from typing import Any, Callable
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
NS = {"h": "urn:hl7-org:v3"}
MAX_BYTES = 40_000_000
DEVICE_CODES = {"55439-4", "69404-2"}


def load_catalog(path: Path) -> list[dict[str, Any]]:
    """Read the pinned, device-only JSON block embedded in the source catalog."""
    match = re.search(r"<!-- device-catalog -->\s*```json\s*(.*?)\s*```", path.read_text(), re.S)
    if not match:
        raise ValueError("Device catalog block missing")
    entries = json.loads(match[1])
    seen: set[str] = set()
    for entry in entries:
        if entry["module"] != "device" or not re.fullmatch(r"device_\d{2}", entry["id"]):
            raise ValueError("Expected a safe device-only catalog entry")
        if entry["id"] in seen:
            raise ValueError("Duplicate image id")
        seen.add(entry["id"])
        url = urlsplit(entry["url"])
        if url.scheme != "https" or url.netloc != "dailymed.nlm.nih.gov":
            raise ValueError("Expected an official HTTPS DailyMed source")
        if not entry["symbols"]:
            raise ValueError("Every selected device image needs a reviewed symbol crop")
        for symbol in entry["symbols"]:
            if symbol["origin"] != "LLM-labelled" or not symbol["uncertainty"]:
                raise ValueError("Symbol provenance and uncertainty are required")
    return entries


def download(url: str) -> bytes:
    """Download a bounded archive, retrying transient network failures at most twice."""
    request = Request(url, headers={"User-Agent": "LabelLens-academic-source-collector/1.0"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=90) as response:
                payload = response.read(MAX_BYTES + 1)
            break
        except (TimeoutError, URLError, HTTPException):
            if attempt == 2:
                raise
    if len(payload) > MAX_BYTES:
        raise ValueError("Download exceeds size limit")
    return payload


def read_member(payload: bytes, entry: dict[str, Any]) -> bytes:
    """Verify archive identity and device SPL metadata before reading an image."""
    if hashlib.sha256(payload).hexdigest() != entry["archive_sha256"]:
        raise ValueError("Archive checksum mismatch")
    with ZipFile(BytesIO(payload)) as archive:
        infos = archive.infolist()
        if sum(info.file_size for info in infos) > MAX_BYTES * 5:
            raise ValueError("Archive expansion exceeds size limit")
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive members")
        xml_names = [name for name in names if name.lower().endswith(".xml")]
        if len(xml_names) != 1:
            raise ValueError("Expected one SPL document")
        root = ET.fromstring(archive.read(xml_names[0]))
        code = root.find("h:code", NS)
        set_id = root.find("h:setId", NS)
        version = root.find("h:versionNumber", NS)
        if code is None or code.get("code") not in DEVICE_CODES:
            raise ValueError("SPL is not a medical-device document")
        if set_id is None or set_id.get("root") != entry["setid"]:
            raise ValueError("SPL set id mismatch")
        if version is None or version.get("value") != str(entry["version"]):
            raise ValueError("SPL version mismatch")
        image = archive.read(entry["member"])
    if hashlib.sha256(image).hexdigest() != entry["image_sha256"]:
        raise ValueError("Image checksum mismatch")
    return image


def materialize(
    entries: list[dict[str, Any]], output: Path, fetch: Callable[[str], bytes] = download, *, offline: bool = False,
) -> dict[str, int]:
    """Save verified originals and bounded symbol crops with explicit AI provenance."""
    annotations: list[dict[str, Any]] = []
    for folder in ("source", "images", "crops"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    for entry in entries:
        cached = output / "source" / f"{entry['archive_sha256']}.zip"
        if cached.exists():
            payload = cached.read_bytes()
        elif offline:
            raise FileNotFoundError(f"Missing cached archive: {cached.name}")
        else:
            payload = fetch(entry["url"])
        image_bytes = read_member(payload, entry)
        with Image.open(BytesIO(image_bytes)) as image:
            if list(image.size) != entry["size_px"]:
                raise ValueError("Image dimensions mismatch")
            crops: list[tuple[Path, Image.Image]] = []
            for index, symbol in enumerate(entry["symbols"]):
                x0, y0, x1, y1 = symbol["bbox_xyxy_px"]
                if not all(type(v) is int for v in (x0, y0, x1, y1)):
                    raise ValueError("Crop coordinates must be integer pixels")
                if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
                    raise ValueError("Symbol crop outside image bounds")
                crops.append((output / "crops" / f"{entry['id']}_{index:02d}.png", image.crop((x0, y0, x1, y1))))
            cached.write_bytes(payload)
            image_path = Path("images") / f"{entry['id']}{Path(entry['member']).suffix.lower()}"
            (output / image_path).write_bytes(image_bytes)
            for (crop_path, crop), symbol in zip(crops, entry["symbols"], strict=True):
                crop.save(crop_path)
                annotations.append({
                    "image": image_path.as_posix(), "crop": crop_path.relative_to(output).as_posix(),
                    "module": "device", **symbol,
                })
    result = {"images": len(entries), "symbol_crops": len(annotations)}
    manifest = {"summary": result, "sources": entries, "symbols": annotations,
                "human_review": "NOT_RUN", "detection_evaluation": "NOT_RUN"}
    (output / "annotations.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return result


def main() -> None:
    """Run the deterministic collector from any working directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=ROOT / "data/real/SOURCES.md")
    parser.add_argument("--output", type=Path, default=ROOT / "data/real/devices")
    parser.add_argument("--offline", action="store_true", help="Verify and rebuild using cached archives only")
    args = parser.parse_args()
    result = materialize(load_catalog(args.sources), args.output, offline=args.offline)
    print(json.dumps({**result, "module": "device", "tags": "LLM-labelled", "evaluation": "NOT_RUN"}, sort_keys=True))


if __name__ == "__main__":
    main()
