"""Offline checks for the pinned device artwork and AI symbol annotations."""

from __future__ import annotations

import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import patch
from zipfile import ZipFile

import pytest

pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from scripts.real import fetch_dailymed as collector  # noqa: E402


@pytest.fixture
def example() -> tuple[bytes, dict[str, Any]]:
    """Make an in-memory device SPL and image without any network or real data."""
    image = BytesIO()
    pixels = Image.new("RGB", (40, 30))
    for y in range(30):
        for x in range(40):
            pixels.putpixel((x, y), (x, y, x + y))
    pixels.save(image, format="PNG")
    xml = ('<document xmlns="urn:hl7-org:v3"><code code="55439-4"/>'
           '<setId root="test-set"/><versionNumber value="1"/></document>')
    payload = BytesIO()
    with ZipFile(payload, "w") as archive:
        archive.writestr("nested/device.xml", xml)
        archive.writestr("nested/label.png", image.getvalue())
    raw = payload.getvalue()
    entry = {
        "id": "device_01", "module": "device", "setid": "test-set", "version": "1",
        "url": "https://dailymed.nlm.nih.gov/dailymed/getFile.cfm?type=zip&version=1",
        "member": "nested/label.png", "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "image_sha256": hashlib.sha256(image.getvalue()).hexdigest(), "size_px": [40, 30],
        "symbols": [{"name": "sterile_eo", "bbox_xyxy_px": [2, 3, 12, 15],
                     "origin": "LLM-labelled", "uncertainty": "Not human reviewed"}],
    }
    return raw, entry


def test_catalog_provenance_and_scope(tmp_path: Path, example: tuple[bytes, dict[str, Any]]) -> None:
    """Reject module mixing, unsafe ids, duplicate entries and missing AI attribution."""
    _, entry = example
    path = tmp_path / "SOURCES.md"
    path.write_text('<!-- device-catalog -->\n```json\n' + json.dumps([entry]) + '\n```')
    assert collector.load_catalog(path) == [entry]
    mutations = [({"module": "medicine"}), ({"id": "../escape"}),
                 ({"url": "http://example.org"}), ({"symbols": []}),
                 ({"symbols": [{**entry["symbols"][0], "origin": "human"}]})]
    for mutation in mutations:
        path.write_text('<!-- device-catalog -->\n```json\n' + json.dumps([{**entry, **mutation}]) + '\n```')
        with pytest.raises(ValueError):
            collector.load_catalog(path)
    path.write_text('<!-- device-catalog -->\n```json\n' + json.dumps([entry, entry]) + '\n```')
    with pytest.raises(ValueError, match="Duplicate"):
        collector.load_catalog(path)
    path.write_text("No catalog")
    with pytest.raises(ValueError, match="missing"):
        collector.load_catalog(path)


@pytest.mark.parametrize("field,value", [
    ("archive_sha256", "bad"), ("image_sha256", "bad"), ("setid", "other"), ("version", "2"),
])
def test_archive_identity(example: tuple[bytes, dict[str, Any]], field: str, value: str) -> None:
    """Reject changed content and a different source document or version."""
    raw, entry = example
    with pytest.raises(ValueError):
        collector.read_member(raw, {**entry, field: value})


def test_medicine_spl_rejected(example: tuple[bytes, dict[str, Any]]) -> None:
    """Reject a medicine document even if its catalog entry says device."""
    raw, entry = example
    revised = BytesIO()
    with ZipFile(BytesIO(raw)) as source, ZipFile(revised, "w") as target:
        for name in source.namelist():
            target.writestr(name, source.read(name).replace(b"55439-4", b"34391-3"))
    payload = revised.getvalue()
    with pytest.raises(ValueError, match="not a medical-device"):
        collector.read_member(payload, {**entry, "archive_sha256": hashlib.sha256(payload).hexdigest()})


def test_repeatable_crops_and_offline_rebuild(tmp_path: Path, example: tuple[bytes, dict[str, Any]]) -> None:
    """Rebuild exactly the requested pixel rectangle and preserve originals and AI origin."""
    raw, entry = example
    with patch.object(collector, "download", side_effect=AssertionError("Network forbidden")):
        with pytest.raises(FileNotFoundError):
            collector.materialize([entry], tmp_path, offline=True)
        assert collector.materialize([entry], tmp_path, lambda _: raw) == {"images": 1, "symbol_crops": 1}
        before = (tmp_path / "crops/device_01_00.png").read_bytes()
        collector.materialize([entry], tmp_path, offline=True)
    assert (tmp_path / "crops/device_01_00.png").read_bytes() == before
    with Image.open(tmp_path / "crops/device_01_00.png") as crop:
        assert crop.size == (10, 12)
        assert crop.getpixel((0, 0)) == (2, 3, 5)
        assert crop.getpixel((9, 11)) == (11, 14, 25)
    manifest = json.loads((tmp_path / "annotations.json").read_text())
    assert manifest["symbols"][0]["origin"] == "LLM-labelled"
    assert manifest["human_review"] == "NOT_RUN"
    assert hashlib.sha256((tmp_path / "images/device_01.png").read_bytes()).hexdigest() == entry["image_sha256"]


@pytest.mark.parametrize("box", [[-1, 0, 10, 10], [1, 1, 41, 10], [2, 2, 2, 5], [1.5, 1, 10, 10]])
def test_invalid_crop_rejected(
    tmp_path: Path, example: tuple[bytes, dict[str, Any]], box: list[int | float],
) -> None:
    """Reject clipping and noninteger coordinates rather than silently padding crops."""
    raw, entry = example
    entry["symbols"][0]["bbox_xyxy_px"] = box
    with pytest.raises(ValueError, match="crop|Crop"):
        collector.materialize([entry], tmp_path, lambda _: raw)
    assert not (tmp_path / "images/device_01.png").exists()


def test_download_bounded_and_timed() -> None:
    """The network helper limits payload size and supplies a timeout."""
    with patch.object(collector, "urlopen") as opener:
        opener.return_value.__enter__.return_value.read.return_value = b"ok"
        assert collector.download("https://dailymed.nlm.nih.gov/example") == b"ok"
        assert opener.call_args.kwargs["timeout"] == 90
        with patch.object(collector, "MAX_BYTES", 1), pytest.raises(ValueError, match="size limit"):
            collector.download("https://dailymed.nlm.nih.gov/example")


def test_main_is_independent_of_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI defaults resolve to the checkout rather than the caller's current folder."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["fetch_dailymed.py", "--offline"])
    with patch.object(collector, "load_catalog", return_value=[]) as load:
        with patch.object(collector, "materialize", return_value={"images": 0}) as build:
            collector.main()
    assert load.call_args.args[0] == collector.ROOT / "data/real/SOURCES.md"
    assert build.call_args.kwargs["offline"] is True


def test_versioned_catalog_has_reviewed_device_symbols() -> None:
    """The committed catalog supplies crops and source rights for each selected original."""
    entries = collector.load_catalog(collector.ROOT / "data/real/SOURCES.md")
    assert len(entries) >= 18
    assert len({e["image_sha256"] for e in entries}) == len(entries)
    for entry in entries:
        assert entry["rights"] and entry["source_page"] and entry["family"]
        assert all(symbol["origin"] == "LLM-labelled" for symbol in entry["symbols"])


def test_transient_download_retry_is_bounded() -> None:
    """Recover from a timeout but stop after three failed attempts."""
    with patch.object(collector, "urlopen") as opener:
        response = opener.return_value
        response.__enter__.return_value.read.return_value = b"recovered"
        opener.side_effect = [TimeoutError("temporary"), response]
        assert collector.download("https://dailymed.nlm.nih.gov/example") == b"recovered"
        assert opener.call_count == 2
    with patch.object(collector, "urlopen", side_effect=TimeoutError("persistent")) as opener:
        with pytest.raises(TimeoutError, match="persistent"):
            collector.download("https://dailymed.nlm.nih.gov/example")
        assert opener.call_count == 3
