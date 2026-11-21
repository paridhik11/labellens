"""Offline provenance and chunk-contract checks for the medicine collector."""
from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.real import build_medicine_corpus as medicine
from src.common.schemas import Chunk


def sample() -> tuple[bytes, dict]:
    """Create a small explicitly fictitious medicine SPL for parser tests."""
    xml = b'''<document xmlns="urn:hl7-org:v3"><code code="34391-3"/>
    <setId root="12345678-1234-1234-1234-123456789abc"/><versionNumber value="2"/>
    <effectiveTime value="20260102"/><manufacturedProduct><manufacturedProduct>
    <name>TEST MEDICINE</name></manufacturedProduct></manufacturedProduct>
    <section><code code="34067-9"/><title>Uses</title><text>These are five test words only.</text></section>
    <section><code code="34071-1"/><title>Warnings</title><text>These warning words are source text only.</text>
    <component><section><code code="42229-5"/><title>Nested warning</title>
    <text>Keep this nested warning in the corpus.</text></section></component></section>
    <section><code code="34068-7"/><title>Directions</title><text>These are test dosage words only.</text></section>
    </document>'''
    entry = {"product_name": "TEST MEDICINE", "setid": "12345678-1234-1234-1234-123456789abc",
             "version": 2, "effective_date": "2026-01-02", "fetched": "2026-11-16",
             "xml_sha256": hashlib.sha256(xml).hexdigest()}
    return xml, entry


def test_parse_and_offline_rebuild(tmp_path: Path) -> None:
    """Preserve nested text once, exact Chunk keys and deterministic cached bytes."""
    xml, entry = sample()
    chunks, product = medicine.parse_product(xml, entry)
    assert len(chunks) == 4
    assert len({c.chunk_id for c in chunks}) == 4
    assert all(c.module == "medicine" and c.hash == medicine.compute_content_hash(c.text) for c in chunks)
    assert sum("nested warning in" in c.text for c in chunks) == 1
    assert product["effective_date"] == "2026-01-02"
    first = medicine.build_corpus([entry], tmp_path, fetch=lambda _: xml)
    content = (tmp_path / "corpus.jsonl").read_bytes()
    assert medicine.build_corpus([entry], tmp_path, offline=True) == first
    assert content == (tmp_path / "corpus.jsonl").read_bytes()
    for line in content.splitlines():
        row = json.loads(line)
        assert set(row) == set(Chunk.model_fields)
        Chunk.model_validate(row)
    with pytest.raises(SystemExit) as exit_info:
        medicine.main(["--help"])
    assert exit_info.value.code == 0


@pytest.mark.parametrize("field,value", [
    ("setid", "wrong"), ("version", 3), ("product_name", "wrong"),
    ("effective_date", "2026-01-03"), ("xml_sha256", "0" * 64),
])
def test_identity_mismatches(field: str, value: object) -> None:
    """Reject changed bytes, stale identities, names and dates."""
    xml, entry = sample()
    entry[field] = value
    with pytest.raises(ValueError):
        medicine.parse_product(xml, entry)


def test_missing_sections_and_device_rejected() -> None:
    """Do not substitute device labels or incomplete source sections."""
    xml, entry = sample()
    for old, new in [(b'34391-3', b'55439-4'), (b'34068-7', b'99999-9')]:
        modified = xml.replace(old, new)
        entry["xml_sha256"] = hashlib.sha256(modified).hexdigest()
        with pytest.raises(ValueError):
            medicine.parse_product(modified, entry)


def test_catalog_and_offline_errors(tmp_path: Path) -> None:
    """Validate the committed catalog and fail clearly when cache is absent."""
    catalog = medicine.load_catalog(Path("data/medicine/SOURCES.md"))
    assert len(catalog) == 30
    xml, entry = sample()
    with pytest.raises(FileNotFoundError):
        medicine.build_corpus([entry], tmp_path, offline=True)
    path = tmp_path / "SOURCES.md"
    path.write_text('<!-- medicine-catalog -->\n```json\n' + json.dumps([entry, entry]) + '\n```')
    with pytest.raises(ValueError, match="Duplicate"):
        medicine.load_catalog(path)
    path.write_text("missing catalog")
    with pytest.raises(ValueError, match="missing"):
        medicine.load_catalog(path)


def test_fetch_versioned_archive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Download only the pinned version and read XML without extracting paths."""
    xml, entry = sample()
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("source.xml", xml)
    seen = []

    def fake_open(request: object, timeout: int) -> BytesIO:
        """Record the requested URL and serve a small offline archive."""
        seen.append(request.full_url)
        return BytesIO(buffer.getvalue())

    monkeypatch.setattr(medicine, "urlopen", fake_open)
    assert medicine.fetch_xml(entry) == xml
    assert f"setid={entry['setid']}&version=2" in seen[0]
