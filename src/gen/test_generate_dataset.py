"""Integration checks for seeded label sets and photo-space ground truth."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import zxingcpp
from PIL import Image

from src.gen.generate_dataset import _save_condition, generate_dataset, main
from src.gen.smoke_label import build_label


@pytest.fixture(scope="module")
def dataset(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    """Generate a small shared set with two different labels per condition."""
    output = tmp_path_factory.mktemp("dataset")
    return output, generate_dataset(output, seed=42, labels_per_condition=2)


def test_paired_conditions(dataset: tuple[Path, dict[str, Any]]) -> None:
    """Every image has truth, matching variants, and measured barcode checks."""
    output, manifest = dataset
    assert manifest["total_images"] == 6
    assert len(list(output.rglob("*.png"))) == 6
    assert len(list(output.rglob("*.json"))) == 7  # Six truths and one manifest.
    variants: dict[str, list[dict[str, Any]]] = {}
    measured = {condition: 0 for condition in ("clean", "moderate", "hard")}
    for entry in manifest["files"]:
        truth = json.loads((output / entry["ground_truth"]).read_text(encoding="utf-8"))
        variants.setdefault(truth["base_label_id"], []).append(truth)
        assert truth["test_data"] is True
        assert truth["status"] == "DRAFT"
        assert truth["label_id"].startswith("test_")
        assert truth["barcode_ais"]["01"] == "00000000000000"
        assert truth["fields"]["lot"] == f"LOT: {truth['barcode_ais']['10']}"
        assert truth["change_log"][-1]["seed"] == truth["augmentation_seed"]
        check = truth["self_check"]
        assert check["ocr"] == check["symbol_detection"] == "NOT_RUN"
        assert check["barcode_recovery_method"] in {
            "original_image", "rectified_image", "thresholded_template_slot", "label_boundary_not_found"
        }
        with Image.open(output / entry["image"]) as image:
            assert list(image.size) == truth["image_size_px"]
        decoded = check["decoded_barcodes"]
        matches = len(decoded) == 1 and decoded[0]["parsed"] == truth["barcode_ais"]
        assert check["barcode_matches"] == matches
        expected_status = "PASS" if matches and check["geometry_in_bounds"] else "NEEDS_HUMAN_REVIEW"
        assert check["status"] == expected_status
        measured[truth["condition"]] += int(matches)
    assert len(variants) == 2
    for truths in variants.values():
        assert {truth["condition"] for truth in truths} == {"clean", "moderate", "hard"}
        assert all(truth["fields"] == truths[0]["fields"] for truth in truths)
        assert all(truth["barcode_payload"] == truths[0]["barcode_payload"] for truth in truths)
    first, second = [truths[0] for truths in variants.values()]
    for field in ("product_name", "manufacturer", "manufacturer_address", "model", "lot", "expiry"):
        assert first["fields"][field] != second["fields"][field]
    for condition, counts in manifest["conditions"].items():
        assert counts["images"] == counts["geometry_passes"] == 2
        assert counts["barcode_passes"] == measured[condition]
    assert measured["clean"] == 2


def test_transformed_positions(dataset: tuple[Path, dict[str, Any]], tmp_path: Path) -> None:
    """Check every field and symbol with independent homogeneous-coordinate math."""
    output, manifest = dataset
    for entry in manifest["files"]:
        truth = json.loads((output / entry["ground_truth"]).read_text(encoding="utf-8"))
        matrix = np.asarray(truth["homography"])
        width, height = truth["image_size_px"]
        for field, (x, y, w, h) in truth["source_slot_boxes_px_xywh"].items():
            source = np.array([[x, y, 1], [x + w, y, 1], [x + w, y + h, 1], [x, y + h, 1]])
            projected = source @ matrix.T
            expected = projected[:, :2] / projected[:, 2:]
            actual = np.asarray(truth["slot_quads_px"][field])
            assert np.allclose(actual, expected, atol=0.001, rtol=0)
            assert ((0 <= actual[:, 0]) & (actual[:, 0] < width)).all()
            assert ((0 <= actual[:, 1]) & (actual[:, 1] < height)).all()
        for symbol in truth["symbols"]:
            field = f"{symbol['name']}_symbol"
            assert symbol["source_bbox_px_xywh"] == truth["source_slot_boxes_px_xywh"][field]
            assert symbol["quad_px"] == truth["slot_quads_px"][field]
        source_width, source_height = truth["source_image_size_px"]
        corners = np.array([
            [0, 0, 1], [source_width - 1, 0, 1],
            [source_width - 1, source_height - 1, 1], [0, source_height - 1, 1],
        ]) @ matrix.T
        assert np.allclose(truth["label_quad_px"], corners[:, :2] / corners[:, 2:], atol=0.001, rtol=0)
        if truth["condition"] == "clean":
            assert np.array_equal(matrix, np.eye(3))
            source_paths = build_label(
                tmp_path, label_id=truth["base_label_id"],
                field_values=truth["fields"], barcode_ais=truth["barcode_ais"],
            )
            assert (output / entry["image"]).read_bytes() == Path(source_paths["image"]).read_bytes()


def test_reproducible_dataset(dataset: tuple[Path, dict[str, Any]], tmp_path: Path) -> None:
    """The same seed reproduces every byte, including a repeat in the same folder."""
    output, manifest = dataset
    before = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}
    assert generate_dataset(tmp_path, seed=42, labels_per_condition=2) == manifest
    assert generate_dataset(output, seed=42, labels_per_condition=2) == manifest
    for relative, expected in before.items():
        assert (tmp_path / relative).read_bytes() == expected
        assert (output / relative).read_bytes() == expected


def test_different_seed(dataset: tuple[Path, dict[str, Any]], tmp_path: Path) -> None:
    """Changing the seed changes photo pixels and their recorded transformation."""
    output, _ = dataset
    generate_dataset(tmp_path, seed=43, labels_per_condition=2)
    relative = Path("hard/test_label_001_hard")
    first = json.loads((output / relative.with_suffix(".json")).read_text(encoding="utf-8"))
    second = json.loads((tmp_path / relative.with_suffix(".json")).read_text(encoding="utf-8"))
    assert first["homography"] != second["homography"]
    first_pixels = (output / relative.with_suffix(".png")).read_bytes()
    second_pixels = (tmp_path / relative.with_suffix(".png")).read_bytes()
    assert first_pixels != second_pixels


def test_failed_barcode_is_retained(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Retain image and truth when the photo barcode cannot be decoded."""
    paths = build_label(tmp_path / "source")
    source_truth = json.loads(Path(paths["ground_truth"]).read_text(encoding="utf-8"))
    monkeypatch.setattr(zxingcpp, "read_barcodes", lambda image, **kwargs: [])
    output = tmp_path / "photos"
    with Image.open(paths["image"]) as source:
        truth = _save_condition(source, source_truth, output, "hard", seed=42)
    assert truth["self_check"]["status"] == "NEEDS_HUMAN_REVIEW"
    assert truth["self_check"]["barcode_matches"] is False
    assert truth["self_check"]["decoded_barcodes"] == []
    assert (output / "hard/test_label_001_hard.png").is_file()
    assert (output / "hard/test_label_001_hard.json").is_file()


@pytest.mark.parametrize("seed, count", [(-1, 1), (True, 1), (42, 0), (42, 1000), (42, 1.5)])
def test_invalid_configuration(tmp_path: Path, seed: int, count: int) -> None:
    """Reject invalid seeds and counts before creating an output folder."""
    output = tmp_path / "dataset"
    with pytest.raises(ValueError):
        generate_dataset(output, seed=seed, labels_per_condition=count)
    assert not output.exists()


def test_unrelated_output_is_preserved(tmp_path: Path) -> None:
    """Never overwrite an unrelated folder while generating a dataset."""
    existing = tmp_path / "notes.txt"
    existing.write_text("keep this", encoding="utf-8")
    with pytest.raises(ValueError, match="no dataset manifest"):
        generate_dataset(tmp_path, labels_per_condition=1)
    assert existing.read_text(encoding="utf-8") == "keep this"
    assert list(tmp_path.iterdir()) == [existing]


def test_mixed_settings_are_rejected(dataset: tuple[Path, dict[str, Any]]) -> None:
    """Require a different directory when seed or label count changes."""
    output, _ = dataset
    for seed, count in ((43, 2), (42, 1)):
        with pytest.raises(ValueError, match="different settings"):
            generate_dataset(output, seed=seed, labels_per_condition=count)


def test_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exercise the CLI options and verify that its measured counts are printed."""
    assert main(["--output-dir", str(tmp_path), "--seed", "42", "--labels-per-condition", "1"]) == 0
    output = capsys.readouterr().out
    assert "Generated 3 image/JSON pairs (seed=42)" in output
    for condition in ("clean", "moderate", "hard"):
        assert f"{condition}: images=1" in output
    assert "OCR and symbol detection NOT_RUN" in output
    assert (tmp_path / "manifest.json").is_file()


def test_cli_invalid_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Show a useful command-line error for an invalid count."""
    with pytest.raises(SystemExit) as error:
        main(["--output-dir", str(tmp_path), "--labels-per-condition", "0"])
    assert error.value.code == 2
    assert "labels_per_condition" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())
