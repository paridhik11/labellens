"""Offline source-link, integrity and negative-case checks for real-label collection."""

from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.error import URLError

import pytest

pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from scripts import build_real_set as builder  # noqa: E402


@pytest.fixture
def bundle() -> bytes:
    """A synthetic SPL/archive fixture, never part of the real-label dataset."""
    xml = b"""<document xmlns="urn:hl7-org:v3">
      <code code="34390-5"/><setId root="fixture-set"/><versionNumber value="1"/>
      <effectiveTime value="20250101"/>
      <author><assignedEntity><representedOrganization><name>Fixture Labeler</name>
      </representedOrganization></assignedEntity></author>
      <component><structuredBody><component><section><subject><manufacturedProduct><manufacturedProduct>
      <code code="12345-100" codeSystem="2.16.840.1.113883.6.69"/><name>Fixture Medicine</name>
      <ingredient classCode="ACTIB"><quantity><numerator value="5" unit="mg"/>
      <denominator value="1" unit="1"/></quantity><ingredientSubstance><name>Fixture Ingredient</name>
      </ingredientSubstance></ingredient>
      <asContent><containerPackagedProduct><code code="12345-100-01" codeSystem="2.16.840.1.113883.6.69"/>
      </containerPackagedProduct></asContent>
      </manufacturedProduct></manufacturedProduct></subject></section></component>
      <component><section><id root="panel-1"/><code code="51945-4"/>
      <text><paragraph>Fixture Medicine 5 mg NDC 12345-100-01 Fixture Labeler</paragraph>
      <renderMultiMedia referencedObject="image-1"/></text>
      <component><observationMedia ID="image-1"><value><reference value="label.png"/></value>
      </observationMedia></component></section></component></structuredBody></component></document>"""
    png = BytesIO()
    Image.new("RGB", (200, 160), "white").save(png, format="PNG")
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("folder/label.xml", xml)
        archive.writestr("folder/label.png", png.getvalue())
    return output.getvalue()


def fetch_fixture(url: str, bundle: bytes) -> bytes:
    """Return an API response or ZIP fixture without any network activity."""
    if "spls.json" in url:
        return json.dumps({"data": [{"setid": "fixture-set", "spl_version": 1, "title": "Fixture"}]}).encode()
    if url.endswith(".xml"):
        return builder.unpack_bundle(bundle)[0]
    return bundle


def test_parse_fields_and_image_association(bundle: bytes) -> None:
    """Explicit media links and package NDC drive selection; labeler is not manufacturer."""
    xml, media = builder.unpack_bundle(bundle)
    parsed = builder.parse_spl(xml)
    assert parsed["product_name"] == "Fixture Medicine"
    assert parsed["labeler"] == "Fixture Labeler" and parsed["manufacturer"] == ""
    assert parsed["strengths"][0]["numerator_value"] == "5"
    assert parsed["panels"][0]["image_name"] in media
    assert parsed["panels"][0]["ndc"] == "12345-100-01"
    assert builder.normalize("FiXture 5 mg") == "fixture5mg"
    assert builder.text(None) == ""
    assert builder.image_details(media["label.png"])["width_px"] == 200


def test_selection_pins_version_and_never_uses_document_date_as_expiry(bundle: bytes) -> None:
    """Same-version evidence is preserved without inventing batch or expiry values."""
    candidate = {"setid": "fixture-set", "spl_version": 1}
    record, xml, image = builder.select_record(candidate, bundle, "2026-11-15")
    assert record["image_sha256"] == builder.digest(image)
    assert record["xml_sha256"] == builder.digest(xml)
    assert record["lot"] == record["expiry"] == ""
    assert record["visible_fields_verified"] is False
    assert record["field_evidence"]["ndc"] is True
    assert builder.truth_row(record)["manufacturer"] == ""
    with pytest.raises(builder.UnusableLabel, match="identity/version"):
        builder.select_record({**candidate, "spl_version": 2}, bundle, "date")


@pytest.mark.parametrize(
    "before,after",
    [
        (b'<code code="34390-5"', b'<code code="animal"'),
        (b'code="51945-4"', b'code="unrelated"'),
        (b'referencedObject="image-1"', b'referencedObject="missing-image"'),
        (b"NDC 12345-100-01", b"NDC 99999-999-99"),
    ],
)
def test_ambiguous_or_unmatched_sources_rejected(bundle: bytes, before: bytes, after: bytes) -> None:
    """Unrelated images, non-medicine documents and mismatched NDCs cannot become truth."""
    xml, _ = builder.unpack_bundle(bundle)
    with pytest.raises(builder.UnusableLabel):
        builder.parse_spl(xml.replace(before, after))


def test_discovery_is_seeded_and_deduplicated(bundle: bytes) -> None:
    """Repeated results across ingredient queries cannot duplicate a selected label."""
    first = builder.discover(lambda url: fetch_fixture(url, bundle), 42)
    assert first == builder.discover(lambda url: fetch_fixture(url, bundle), 42)
    assert len(first) == 1


def test_collect_validate_and_byte_identical_rebuild(bundle: bytes, tmp_path: Path) -> None:
    """One command creates agreeing manifest/CSV and can rebuild pinned source bytes."""
    fetch = lambda url: fetch_fixture(url, bundle)  # noqa: E731
    output = tmp_path / "dataset"
    manifest = builder.collect(output, 1, 42, fetch)
    assert manifest["complete"]
    assert b"\r\n" not in (output / "truth.csv").read_bytes()
    assert manifest["labels"][0]["fields_available"] == ["product_name", "ndc", "strength", "labeler"]
    summary = builder.validate_dataset(output)
    assert summary["labels"] == 1 and summary["ocr_run"] is False
    assert summary["source_field_counts"]["manufacturer"] == 0
    target = tmp_path / "rebuilt"
    assert builder.rebuild(output / "manifest.json", target, fetch)["labels"] == 1
    for name in ("truth.csv", manifest["labels"][0]["image_path"], manifest["labels"][0]["xml_path"]):
        assert (target / name).read_bytes() == (output / name).read_bytes()
    with pytest.raises(FileExistsError):
        builder.collect(output, 1, 42, fetch)
    with pytest.raises(FileExistsError):
        builder.rebuild(output / "manifest.json", target, fetch)


def test_corrupt_image_and_changed_truth_are_detected(bundle: bytes, tmp_path: Path) -> None:
    """Validation checks source bytes and exact CSV fields, not just file existence."""
    manifest = builder.collect(tmp_path, 1, 42, lambda url: fetch_fixture(url, bundle))
    truth = tmp_path / "truth.csv"
    original = truth.read_text()
    truth.write_text(original.replace("Fixture Medicine", "Incorrect Medicine"))
    with pytest.raises(ValueError, match="CSV"):
        builder.validate_dataset(tmp_path)
    truth.write_text(original)
    image = tmp_path / manifest["labels"][0]["image_path"]
    image.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="Changed image"):
        builder.validate_dataset(tmp_path)


def test_short_collection_is_marked_incomplete(bundle: bytes, tmp_path: Path) -> None:
    """A short dataset is never silently reported as meeting the requested count."""
    with pytest.raises(builder.UnusableLabel, match="1/2"):
        builder.collect(tmp_path, 2, 42, lambda url: fetch_fixture(url, bundle))
    assert not json.loads((tmp_path / "manifest.json").read_text())["complete"]
    with pytest.raises(ValueError, match="Incomplete"):
        builder.validate_dataset(tmp_path)


def test_download_stops_on_network_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retries are bounded and no alternate host is used to bypass blocked downloads."""

    def fail(*args: object, **kwargs: object) -> None:
        """Simulate unreachable network for the downloader."""
        raise URLError("offline")

    monkeypatch.setattr(builder, "urlopen", fail)
    monkeypatch.setattr(builder.time, "sleep", lambda _: None)
    with pytest.raises(builder.DownloadError, match="Network failure"):
        builder.download(builder.BASE + "fixture")
    with pytest.raises(builder.DownloadError, match="Only documented"):
        builder.download("https://example.org/other")


def test_main_offline_validation_and_failure(bundle: bytes, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """CLI returns explicit success or failure for offline dataset checks."""
    builder.collect(tmp_path, 1, 42, lambda url: fetch_fixture(url, bundle))
    assert builder.main(["--output", str(tmp_path), "--validate"]) == 0
    assert '"labels": 1' in capsys.readouterr().out
    assert builder.main(["--output", str(tmp_path / "absent"), "--validate"]) == 1
    assert "STOPPED:" in capsys.readouterr().err


def test_committed_real_dataset_integrity() -> None:
    """Every committed image opens and every truth row agrees with its pinned XML."""
    output = Path("data/real")
    if not (output / "manifest.json").exists():
        pytest.skip("Live dataset has not yet been collected")
    summary = builder.validate_dataset(output)
    assert summary["labels"] == 60
    assert summary["bytes"] < 200_000_000
    assert summary["labelers"] >= 20
    assert summary["source_field_counts"]["product_name"] == 60
    assert summary["source_field_counts"]["ndc"] == 60
    assert summary["source_field_counts"]["strength"] == 60


def test_resume_uses_frozen_candidates_and_preserves_existing_sources(bundle: bytes, tmp_path: Path) -> None:
    """An interrupted build can finish without reselecting or replacing its first image."""
    with pytest.raises(builder.UnusableLabel):
        builder.collect(tmp_path, 2, 42, lambda url: fetch_fixture(url, bundle))
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    first_hash = manifest["labels"][0]["image_sha256"]
    candidates = json.loads((tmp_path / "candidates.json").read_text())
    candidates.append({"setid": "fixture-second", "spl_version": 1})
    (tmp_path / "candidates.json").write_text(json.dumps(candidates))
    xml, _ = builder.unpack_bundle(bundle)
    png = BytesIO()
    Image.new("RGB", (200, 160), "black").save(png, format="PNG")
    second = BytesIO()
    with zipfile.ZipFile(second, "w") as archive:
        archive.writestr("label.xml", xml.replace(b'root="fixture-set"', b'root="fixture-second"'))
        archive.writestr("label.png", png.getvalue())

    def frozen_fetch(url: str) -> bytes:
        """Supply the second pinned source; fail if discovery restarts."""
        assert "spls.json" not in url
        source = second.getvalue() if "fixture-second" in url else bundle
        return builder.unpack_bundle(source)[0] if url.endswith(".xml") else source

    result = builder.collect(tmp_path, 2, 42, frozen_fetch, resume=True)
    assert result["complete"] and result["labels"][0]["image_sha256"] == first_hash
    assert builder.validate_dataset(tmp_path)["labels"] == 2


def test_blocked_download_saves_incomplete_status(bundle: bytes, tmp_path: Path) -> None:
    """A network block stops the build and leaves an honest, resumable status."""

    def blocked(url: str) -> bytes:
        """Allow discovery but simulate a network block on actual source access."""
        if "spls.json" in url:
            return fetch_fixture(url, bundle)
        raise builder.DownloadError("HTTP 403: fixture")

    with pytest.raises(builder.DownloadError, match="403"):
        builder.collect(tmp_path, 1, 42, blocked)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["complete"] is False and manifest["labels"] == []


def test_unverified_fields_cannot_be_marked_as_pixel_truth(bundle: bytes, tmp_path: Path) -> None:
    """A metadata edit cannot silently turn source data into verified image transcription."""
    manifest = builder.collect(tmp_path, 1, 42, lambda url: fetch_fixture(url, bundle))
    manifest["labels"][0]["visible_fields_verified"] = True
    builder.write_snapshot(tmp_path, manifest)
    with pytest.raises(ValueError, match="pixel-verification"):
        builder.validate_dataset(tmp_path)


def test_git_windows_line_endings_preserve_source_bytes(tmp_path: Path) -> None:
    """Simulate Git autocrlf=true without claiming execution on a Windows host."""
    import shutil
    import subprocess

    executable = shutil.which("git")
    if executable is None:
        pytest.skip("Git is needed for the checkout line-ending simulation")
    repo = tmp_path / "repo"
    repo.mkdir()
    subtree = repo / "data" / "real"
    source = subtree / "source" / "fixture.xml"
    source.parent.mkdir(parents=True)
    original = b"<original>  \r\n  source bytes \n</original>\r\n"
    source.write_bytes(original)
    attributes = Path("data/real/.gitattributes").read_bytes()
    assert attributes == builder.GIT_ATTRIBUTES.encode("utf-8")
    (subtree / ".gitattributes").write_bytes(attributes)
    subprocess.run([executable, "init", "-q", str(repo)], check=True, capture_output=True)
    subprocess.run(
        [executable, "-C", str(repo), "-c", "core.autocrlf=true", "add", "."], check=True, capture_output=True
    )
    stored = subprocess.run(
        [executable, "-C", str(repo), "show", ":data/real/source/fixture.xml"], check=True, capture_output=True
    ).stdout
    assert stored == original
    checkout = tmp_path / "checkout"
    subprocess.run(
        [executable, "-C", str(repo), "-c", "core.autocrlf=true", "checkout-index", "--all", f"--prefix={checkout}/"],
        check=True,
        capture_output=True,
    )
    assert (checkout / "data/real/source/fixture.xml").read_bytes() == original
