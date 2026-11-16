"""Build and validate a pinned DailyMed medicine-artwork dataset without OCR.

Sources: https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm
https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_api.cfm
https://www.nlm.nih.gov/web_policies.html#copyright
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import time
import zipfile
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from PIL import Image

BASE = "https://dailymed.nlm.nih.gov/dailymed/"
NS = {"s": "urn:hl7-org:v3"}
NDC_SYSTEM = "2.16.840.1.113883.6.69"
MAX_TOTAL = 200_000_000
MAX_DOWNLOAD = 20_000_000
QUERIES = (
    "acetaminophen",
    "ibuprofen",
    "cetirizine",
    "loratadine",
    "diphenhydramine",
    "omeprazole",
    "famotidine",
    "hydrocortisone",
    "clotrimazole",
    "lidocaine",
    "benzoyl peroxide",
    "povidone iodine",
    "sodium chloride",
    "metformin",
    "amoxicillin",
    "albuterol",
    "atorvastatin",
    "levothyroxine",
    "insulin",
    "naproxen",
)
FIELDS = (
    "id",
    "setid",
    "spl_version",
    "image_path",
    "product_name",
    "ndc",
    "strength",
    "manufacturer",
    "labeler",
    "lot",
    "expiry",
    "ground_truth_scope",
    "visible_fields_verified",
)
TRUTH_FIELDS = ("product_name", "ndc", "strength", "manufacturer", "labeler", "lot", "expiry")
Fetch = Callable[[str], bytes]
GIT_ATTRIBUTES = (
    "# Downloaded XML is original evidence: preserve every byte, including whitespace.\n"
    "source/*.xml -text -whitespace\nimages/* -text\n*.json text eol=lf\n"
    "truth.csv text eol=lf\n*.md text eol=lf\n"
)


class DownloadError(RuntimeError):
    """Network failure that stops collection instead of silently shrinking it."""


class UnusableLabel(ValueError):
    """A label lacks an unambiguous product or usable package-artwork reference."""


def digest(data: bytes) -> str:
    """Return the SHA-256 fingerprint used to pin downloaded evidence."""
    return hashlib.sha256(data).hexdigest()


def download(url: str) -> bytes:
    """Fetch a documented DailyMed URL with bounded size, timeout and retries."""
    if not url.startswith(BASE):
        raise DownloadError("Only documented DailyMed HTTPS downloads are supported")
    for attempt in range(3):
        try:
            time.sleep(0.2)
            request = Request(url, headers={"User-Agent": "LabelLens-artwork-research/1.0"})
            with urlopen(request, timeout=45) as response:
                data = response.read(MAX_DOWNLOAD + 1)
            if len(data) > MAX_DOWNLOAD:
                raise UnusableLabel("Single download exceeds 20 MB")
            return data
        except HTTPError as error:
            if error.code == 404:
                raise UnusableLabel(f"Source returned HTTP 404: {url}") from error
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise DownloadError(f"HTTP {error.code}: {url}") from error
        except (URLError, TimeoutError) as error:
            if attempt == 2:
                raise DownloadError(f"Network failure for {url}: {error}") from error
        time.sleep(attempt + 1)
    raise DownloadError(f"Download failed: {url}")


def text(node: ET.Element | None) -> str:
    """Read source text with normalized whitespace, preserving its words."""
    return " ".join(" ".join(node.itertext()).split()) if node is not None else ""


def normalize(value: str) -> str:
    """Normalize case and spacing only for evidence-presence checks."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def unpack_bundle(data: bytes) -> tuple[bytes, dict[str, bytes]]:
    """Read an SPL archive in memory without extracting untrusted paths."""
    with zipfile.ZipFile(BytesIO(data)) as archive:
        infos = [item for item in archive.infolist() if not item.is_dir()]
        if sum(item.file_size for item in infos) > MAX_TOTAL:
            raise UnusableLabel("Expanded archive exceeds 200 MB")
        xmls = [item for item in infos if item.filename.lower().endswith(".xml")]
        if len(xmls) != 1:
            raise UnusableLabel("Archive must contain exactly one SPL XML document")
        media: dict[str, bytes] = {}
        for item in infos:
            name = PurePosixPath(item.filename).name
            if name.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
                if name in media:
                    raise UnusableLabel("Ambiguous duplicate image filename in archive")
                media[name] = archive.read(item)
        return archive.read(xmls[0]), media


def parse_spl(xml: bytes) -> dict[str, Any]:
    """Extract one product's structured fields and explicitly linked display panels.

    Reject multi-product documents so an image cannot inherit another strength's
    values. Labeler is retained separately and never renamed manufacturer. A
    display-panel text mention is evidence, not verified transcription of pixels.
    """
    root = ET.fromstring(xml)
    document_type = root.find("s:code", NS)
    if document_type is None or document_type.get("code") not in {"34390-5", "34391-3"}:
        raise UnusableLabel("Not a human OTC or prescription medicine label")
    identity, version = root.find("s:setId", NS), root.find("s:versionNumber", NS)
    if identity is None or version is None:
        raise UnusableLabel("SPL identity/version is missing")
    products = []
    for node in root.findall(".//s:manufacturedProduct", NS) + root.findall(".//s:manufacturedMedicine", NS):
        code = node.find("s:code", NS)
        if code is not None and code.get("codeSystem") == NDC_SYSTEM and node.find("s:name", NS) is not None:
            products.append(node)
    if len(products) != 1:
        raise UnusableLabel("Expected one unambiguous structured product")
    product = products[0]
    name = text(product.find("s:name", NS))
    labeler = text(root.find("s:author/s:assignedEntity/s:representedOrganization/s:name", NS))
    manufacturer = text(product.find("s:manufacturerOrganization/s:name", NS))
    strengths = []
    for ingredient in product.findall("s:ingredient", NS):
        if ingredient.get("classCode") not in {"ACTIB", "ACTIM", "ACTIR"}:
            continue
        numerator = ingredient.find("s:quantity/s:numerator", NS)
        denominator = ingredient.find("s:quantity/s:denominator", NS)
        if numerator is None or denominator is None:
            continue
        strengths.append(
            {
                "ingredient": text(ingredient.find("s:ingredientSubstance/s:name", NS)),
                "numerator_value": numerator.get("value", ""),
                "numerator_unit": numerator.get("unit", ""),
                "denominator_value": denominator.get("value", ""),
                "denominator_unit": denominator.get("unit", ""),
            }
        )
    if not name or not labeler or not strengths:
        raise UnusableLabel("Product name, labeler or structured strength is missing")
    ndcs = sorted(
        {
            node.get("code")
            for node in product.findall(".//s:code", NS)
            if node.get("codeSystem") == NDC_SYSTEM and node.get("code")
        }
    )
    observations = {node.get("ID"): node for node in root.findall(".//s:observationMedia", NS)}
    panels = []
    for section in root.findall(".//s:section", NS):
        code = section.find("s:code", NS)
        if code is None or code.get("code") != "51945-4":
            continue
        body = section.find("s:text", NS)
        caption = text(body)
        references = sorted(
            {
                node.get("referencedObject")
                for node in section.findall(".//s:renderMultiMedia", NS)
                if node.get("referencedObject")
            }
        )
        # One image per selected panel avoids assigning a shared caption to an
        # arbitrary image when the panel contains multiple separate artworks.
        if len(references) != 1:
            continue
        observation = observations.get(references[0])
        reference = observation.find("s:value/s:reference", NS) if observation is not None else None
        if reference is None or not reference.get("value"):
            continue
        named_ndcs = re.findall(r"(?<!\d)\d{4,5}-\d{3,4}-\d{1,2}(?!\d)", caption)
        matched_ndcs = sorted(set(named_ndcs) & set(ndcs))
        if len(matched_ndcs) != 1:
            continue
        panels.append(
            {
                "image_name": PurePosixPath(reference.get("value")).name,
                "media_id": references[0],
                "section_id": section.find("s:id", NS).get("root", "") if section.find("s:id", NS) is not None else "",
                "section_code": "51945-4",
                "section_text": caption,
                "ndc": matched_ndcs[0],
            }
        )
    if not panels:
        raise UnusableLabel("No single-image display panel with an exact structured package NDC")
    return {
        "setid": identity.get("root"),
        "spl_version": int(version.get("value")),
        "document_type": document_type.get("code"),
        "product_name": name,
        "labeler": labeler,
        "manufacturer": manufacturer,
        "strengths": strengths,
        "package_ndcs": ndcs,
        "panels": sorted(panels, key=lambda panel: (panel["image_name"], panel["section_id"])),
    }


def image_details(data: bytes) -> dict[str, Any]:
    """Verify an original image opens and report objective geometry, not OCR quality."""
    with Image.open(BytesIO(data)) as image:
        width, height = image.size
        if min(width, height) < 100 or width * height > 30_000_000:
            raise UnusableLabel("Image is too small or too large for this set")
        result = {
            "width_px": width,
            "height_px": height,
            "format": image.format,
            "layout_shape": "wide" if width / height > 1.4 else "tall" if height / width > 1.4 else "compact",
        }
        image.verify()
    with Image.open(BytesIO(data)) as image:
        image.load()
    return result


def discover(fetch: Fetch, seed: int) -> list[dict[str, Any]]:
    """Freeze a seeded, interleaved candidate list across medicine-name queries."""
    groups = []
    rng = random.Random(seed)
    for query in QUERIES:
        url = BASE + "services/v2/spls.json?" + urlencode({"drug_name": query, "pagesize": 30})
        records = json.loads(fetch(url))["data"]
        records = sorted(records, key=lambda entry: (entry["setid"], int(entry["spl_version"])))
        rng.shuffle(records)
        groups.append([{**record, "query": query, "discovery_url": url} for record in records])
    result, seen = [], set()
    for position in range(max(map(len, groups), default=0)):
        for group in groups:
            if position < len(group) and group[position]["setid"] not in seen:
                candidate = group[position]
                seen.add(candidate["setid"])
                result.append(candidate)
    return result


def select_record(candidate: dict[str, Any], data: bytes, date: str) -> tuple[dict[str, Any], bytes, bytes]:
    """Match an original panel image with XML from exactly the same versioned ZIP."""
    xml, media = unpack_bundle(data)
    parsed = parse_spl(xml)
    if (parsed["setid"], parsed["spl_version"]) != (candidate["setid"], int(candidate["spl_version"])):
        raise UnusableLabel("Archive identity/version differs from requested source")
    for panel in parsed.pop("panels"):
        if panel["image_name"] not in media:
            continue
        image = media[panel["image_name"]]
        try:
            details = image_details(image)
        except (OSError, ValueError, Image.DecompressionBombError):
            continue
        identity = f"{parsed['setid']}_v{parsed['spl_version']}"
        suffix = Path(panel["image_name"]).suffix.lower()
        caption = normalize(panel["section_text"])
        evidence = {
            "product_name": normalize(parsed["product_name"]) in caption,
            "ndc": True,
            "strength": all(
                normalize(item["numerator_value"] + item["numerator_unit"]) in caption for item in parsed["strengths"]
            ),
            "labeler": normalize(parsed["labeler"]) in caption,
            "manufacturer": bool(parsed["manufacturer"]) and normalize(parsed["manufacturer"]) in caption,
        }
        record = {
            **parsed,
            **details,
            **panel,
            "id": identity,
            "module": "medicine",
            "image_path": f"images/{identity}{suffix}",
            "xml_path": f"source/{identity}.xml",
            "source_url": BASE + "drugInfo.cfm?setid=" + parsed["setid"],
            "archive_url": BASE
            + "getFile.cfm?"
            + urlencode({"type": "zip", "setid": parsed["setid"], "version": parsed["spl_version"]}),
            "discovery_query": candidate.get("query", ""),
            "downloaded_at": date,
            "image_sha256": digest(image),
            "xml_sha256": digest(xml),
            "image_bytes": len(image),
            "xml_bytes": len(xml),
            "lot": "",
            "expiry": "",
            "field_evidence": evidence,
            "ground_truth_scope": "same-version SPL product plus explicitly linked display-panel text",
            "visible_fields_verified": False,
            "lot_expiry_status": "not independently verified; never inferred from document dates",
            "symbols_status": "not annotated",
            "barcode_status": "not decoded or annotated",
            "rights_status": "company-contributed artwork; no blanket open-license assertion",
        }
        return record, xml, image
    raise UnusableLabel("No referenced package image opens with usable dimensions")


def truth_row(record: dict[str, Any]) -> dict[str, str]:
    """Serialize source-backed fields without equating labeler with manufacturer."""
    row = {key: str(record.get(key, "")) for key in FIELDS}
    row["strength"] = json.dumps(record["strengths"], sort_keys=True, ensure_ascii=False)
    row["visible_fields_verified"] = "false"
    return row


def write_snapshot(output: Path, manifest: dict[str, Any]) -> None:
    """Save the manifest and CSV from the same records, never from independent lists."""
    output.mkdir(parents=True, exist_ok=True)
    (output / ".gitattributes").write_text(GIT_ATTRIBUTES, encoding="utf-8")
    for record in manifest["labels"]:
        row = truth_row(record)
        record["fields_available"] = [field for field in TRUTH_FIELDS if row[field]]
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (output / "truth.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(truth_row(record) for record in manifest["labels"])


def collect(output: Path, count: int, seed: int, fetch: Fetch = download, *, resume: bool = False) -> dict[str, Any]:
    """Collect exactly count diverse labels or leave an explicitly incomplete snapshot."""
    if count < 1:
        raise ValueError("Count must be positive")
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        if not resume:
            raise FileExistsError("Dataset snapshot already exists; use --resume for an incomplete snapshot")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["complete"] or (manifest["target_count"], manifest["seed"]) != (count, seed):
            raise ValueError("Resume requires an incomplete snapshot with the same count and seed")
        candidates = json.loads((output / "candidates.json").read_text(encoding="utf-8"))
        for record in manifest["labels"]:
            for prefix in ("image", "xml"):
                if digest((output / record[f"{prefix}_path"]).read_bytes()) != record[f"{prefix}_sha256"]:
                    raise ValueError("Cannot resume changed source bytes")
    else:
        candidates = discover(fetch, seed)
        output.mkdir(parents=True, exist_ok=True)
        (output / "candidates.json").write_text(json.dumps(candidates, indent=2) + "\n", encoding="utf-8")
        manifest = {
            "dataset": "DailyMed medicine package artwork",
            "schema_version": 1,
            "seed": seed,
            "target_count": count,
            "complete": False,
            "labels": [],
            "rejections": [],
            "terms_url": "https://www.nlm.nih.gov/web_policies.html#copyright",
            "source_attribution": "Source: National Library of Medicine",
            "ocr_run": False,
        }
    labelers = Counter(record["labeler"].casefold() for record in manifest["labels"])
    hashes = {record["image_sha256"] for record in manifest["labels"]}
    total = sum(record["image_bytes"] + record["xml_bytes"] for record in manifest["labels"])
    attempted = {record["setid"] for record in manifest["labels"] + manifest["rejections"]}
    try:
        for candidate in candidates:
            if candidate["setid"] in attempted:
                continue
            url = (
                BASE
                + "getFile.cfm?"
                + urlencode({"type": "zip", "setid": candidate["setid"], "version": candidate["spl_version"]})
            )
            try:
                preview = parse_spl(fetch(BASE + "services/v2/spls/" + candidate["setid"] + ".xml"))
                if (preview["setid"], preview["spl_version"]) != (candidate["setid"], int(candidate["spl_version"])):
                    raise UnusableLabel("Current XML changed since discovery; refusing mixed versions")
                if labelers[preview["labeler"].casefold()] >= 3:
                    raise UnusableLabel("Labeler cap")
                record, xml, image = select_record(candidate, fetch(url), datetime.now(timezone.utc).isoformat())
                if labelers[record["labeler"].casefold()] >= 3 or record["image_sha256"] in hashes:
                    raise UnusableLabel("Labeler cap or duplicate artwork")
                if total + len(xml) + len(image) > MAX_TOTAL - 2_000_000:
                    raise UnusableLabel("Dataset byte budget would be exceeded")
            except (UnusableLabel, ET.ParseError, zipfile.BadZipFile) as error:
                manifest["rejections"].append({"setid": candidate["setid"], "reason": str(error)})
                if len(manifest["rejections"]) % 20 == 0:
                    print(f"Examined {len(manifest['rejections'])} excluded candidates; continuing", flush=True)
                continue
            for key, content in (("xml_path", xml), ("image_path", image)):
                path = output / record[key]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            manifest["labels"].append(record)
            labelers[record["labeler"].casefold()] += 1
            hashes.add(record["image_sha256"])
            total += len(xml) + len(image)
            print(
                f"Collected {len(manifest['labels'])}/{count}: {record['product_name']} [{record['labeler']}]",
                flush=True,
            )
            write_snapshot(output, manifest)
            if len(manifest["labels"]) == count:
                break
    finally:
        manifest["complete"] = len(manifest["labels"]) == count
        write_snapshot(output, manifest)
    if not manifest["complete"]:
        raise UnusableLabel(f"Only {len(manifest['labels'])}/{count} usable labels; snapshot marked incomplete")
    return manifest


def validate_dataset(output: Path) -> dict[str, Any]:
    """Check IDs, CSV values, source XML evidence, image integrity and fingerprints."""
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    records = manifest["labels"]
    if not manifest["complete"] or len(records) != manifest["target_count"]:
        raise ValueError("Incomplete dataset")
    with (output / "truth.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(records) or len({record["id"] for record in records}) != len(records):
        raise ValueError("Duplicate IDs or manifest/truth count mismatch")
    if len({record["image_sha256"] for record in records}) != len(records):
        raise ValueError("Duplicate artwork bytes")
    if any(value > 3 for value in Counter(record["labeler"].casefold() for record in records).values()):
        raise ValueError("Labeler cap exceeded")
    field_counts = Counter({field: 0 for field in TRUTH_FIELDS})
    text_evidence = Counter({field: 0 for field in TRUTH_FIELDS})
    for row, record in zip(rows, records, strict=True):
        if row != truth_row(record):
            raise ValueError(f"Truth CSV differs from manifest: {record['id']}")
        if record.get("fields_available") != [field for field in TRUTH_FIELDS if row[field]]:
            raise ValueError("Available-field list differs from source-backed values")
        contents = {}
        for prefix in ("xml", "image"):
            path = (output / record[f"{prefix}_path"]).resolve()
            if not path.is_relative_to(output.resolve()):
                raise ValueError("Dataset path escapes its root")
            contents[prefix] = path.read_bytes()
            if len(contents[prefix]) != record[f"{prefix}_bytes"]:
                raise ValueError(f"Changed {prefix} byte count: {record['id']}")
            if digest(contents[prefix]) != record[f"{prefix}_sha256"]:
                raise ValueError(f"Changed {prefix} bytes: {record['id']}")
        parsed = parse_spl(contents["xml"])
        for key in ("setid", "spl_version", "product_name", "labeler", "manufacturer", "strengths"):
            if parsed[key] != record[key]:
                raise ValueError(f"Field does not match source XML: {key}")
        if not any(all(panel[key] == record[key] for key in panel) for panel in parsed["panels"]):
            raise ValueError("Selected display panel does not match source XML")
        if any(record[key] != value for key, value in image_details(contents["image"]).items()):
            raise ValueError("Image dimensions or format changed")
        if record["lot"] or record["expiry"] or record["visible_fields_verified"] is not False:
            raise ValueError("Unsupported lot, expiry or pixel-verification claim")
        if record["module"] != "medicine" or manifest["ocr_run"] is not False:
            raise ValueError("Unexpected module or OCR claim")
        caption = normalize(record["section_text"])
        expected_evidence = {
            "product_name": normalize(parsed["product_name"]) in caption,
            "ndc": True,
            "strength": all(
                normalize(item["numerator_value"] + item["numerator_unit"]) in caption for item in parsed["strengths"]
            ),
            "labeler": normalize(parsed["labeler"]) in caption,
            "manufacturer": bool(parsed["manufacturer"]) and normalize(parsed["manufacturer"]) in caption,
        }
        if record["field_evidence"] != expected_evidence:
            raise ValueError("Display-panel evidence flags differ from source text")
        for field in TRUTH_FIELDS:
            field_counts[field] += bool(row[field])
            text_evidence[field] += bool(record["field_evidence"].get(field))
    total = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
    if total >= MAX_TOTAL:
        raise ValueError("Dataset exceeds 200 MB")
    return {
        "labels": len(records),
        "bytes": total,
        "labelers": len({record["labeler"].casefold() for record in records}),
        "layout_shapes": dict(Counter(record["layout_shape"] for record in records)),
        "source_field_counts": dict(field_counts),
        "display_panel_text_evidence_counts": dict(text_evidence),
        "image_visible_fields_verified": 0,
        "ocr_run": False,
    }


def rebuild(manifest_path: Path, output: Path, fetch: Fetch = download) -> dict[str, Any]:
    """Recreate exactly the pinned images/XML; fail if a source version's bytes differ."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if output.exists():
        raise FileExistsError("Rebuild output must be a new directory")
    for record in manifest["labels"]:
        xml, images = unpack_bundle(fetch(record["archive_url"]))
        image = images[record["image_name"]]
        if digest(xml) != record["xml_sha256"] or digest(image) != record["image_sha256"]:
            raise ValueError(f"Pinned source bytes changed for {record['id']}")
        for key, content in (("xml_path", xml), ("image_path", image)):
            path = (output / record[key]).resolve()
            if not path.is_relative_to(output.resolve()):
                raise ValueError("Rebuild path escapes its root")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    write_snapshot(output, manifest)
    return validate_dataset(output)


def main(argv: list[str] | None = None) -> int:
    """Collect, validate offline or rebuild a version-pinned dataset from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/real"))
    parser.add_argument("--count", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--resume", action="store_true")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--validate", action="store_true")
    modes.add_argument("--rebuild-from", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.rebuild_from:
            summary = rebuild(args.rebuild_from, args.output)
        else:
            if not args.validate:
                collect(args.output, args.count, args.seed, resume=args.resume)
            summary = validate_dataset(args.output)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (DownloadError, UnusableLabel, ValueError, OSError, KeyError) as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
