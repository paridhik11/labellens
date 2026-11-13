"""Checks for raw-text CER, explicit failures and reproducible evaluation reports."""

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from src.common.schemas import BarcodeResult, LabelExtraction, SymbolDetection
from src.cv import eval_extract
from src.gen.generate_dataset import generate_dataset


@pytest.mark.parametrize(
    "reference, observed, expected",
    [
        ("", "", 0),
        ("ABC", "ABC", 0),
        ("ABC", "", 3),
        ("", "ABC", 3),
        ("kitten", "sitting", 3),
        ("ABC", "abc", 3),
        ("A B", "AB", 1),
        ("LOT: X", "LOT:X", 1),
        ("A", "AAAA", 3),
        ("é", "e", 1),
    ],
)
def test_edit_distance(reference: str, observed: str, expected: int) -> None:
    """Count known edits without normalizing spaces, case, punctuation or accents."""
    assert eval_extract.edit_distance(reference, observed) == expected
    assert eval_extract.edit_distance(observed, reference) == expected


def test_box_iou() -> None:
    """Measure matching boxes and reject invalid extents."""
    assert eval_extract._box_iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1.0
    assert eval_extract._box_iou((0, 0, 10, 10), (10, 0, 10, 10)) == 0.0
    with pytest.raises(ValueError, match="positive"):
        eval_extract._box_iou((0, 0, 0, 10), (0, 0, 10, 10))


@pytest.fixture(scope="module")
def dataset(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a small real synthetic set with one label per condition."""
    root = tmp_path_factory.mktemp("evaluation")
    generate_dataset(root, seed=42, labels_per_condition=1)
    return root


@pytest.fixture
def perfect_engine(dataset: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, dict[str, Any]]:
    """Isolate scoring with explicit perfect predictions, not real recognition claims."""
    truths = {}
    for condition in eval_extract.CONDITIONS:
        path = dataset / condition / f"test_label_001_{condition}.json"
        truths[condition] = json.loads(path.read_text(encoding="utf-8"))

    def predict(path: Path) -> LabelExtraction:
        """Supply known predictions to exercise metric accounting only."""
        if not path.exists():
            raise FileNotFoundError("test missing image")
        truth = truths[path.parent.name]
        symbols = []
        for item in truth["symbols"]:
            quad = np.asarray(item["quad_px"], dtype=float)
            left, top = quad.min(axis=0)
            right, bottom = quad.max(axis=0)
            symbols.append(SymbolDetection(
                name=item["name"], bbox=(left, top, right - left, bottom - top), conf=1.0
            ))
        return LabelExtraction(
            label_id=path.stem,
            fields=dict(truth["fields"]),
            barcodes=[BarcodeResult(type="Data Matrix", raw="unit-test prediction", parsed=truth["barcode_ais"])],
            symbols=symbols,
            warnings=["LOW_OCR_CONFIDENCE: first", "LOW_OCR_CONFIDENCE: second"],
        )

    monkeypatch.setattr(eval_extract, "extract_label", predict)
    return truths


def test_perfect_scores(dataset: Path, perfect_engine: dict[str, dict[str, Any]]) -> None:
    """Keep all denominators and count repeated warning codes once per image."""
    evaluation = eval_extract.evaluate_dataset(dataset)
    assert evaluation["provenance"]["total_images"] == 3
    for condition, counts in evaluation["conditions"].items():
        assert counts["images"] == counts["decoded"] == counts["gs1_exact"] == 1
        assert counts["detected"] == counts["corrected_within_10px"] == 1
        assert counts["expected_symbols"] == counts["matched_symbols"] == 2
        assert counts["exact_symbol_sets"] == 1 and counts["symbol_false_positives"] == 0
        assert counts["extraction_failures"] == counts["geometry_failures"] == 0
        assert counts["gs1_per_ai"] == {ai: 1 for ai in eval_extract.AIS}
        assert counts["warning_images"]["LOW_OCR_CONFIDENCE"] == 1
        for field, score in counts["ocr"].items():
            assert score == {
                "edits": 0,
                "reference_characters": len(perfect_engine[condition]["fields"][field]),
                "observed": 1,
            }


def test_insertions_and_missing_fields(
    dataset: Path, perfect_engine: dict[str, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An insertion costs one while a missing field deletes every reference character."""

    def predict(path: Path) -> LabelExtraction:
        """Create controlled field errors for a scorer unit test."""
        fields = dict(perfect_engine[path.parent.name]["fields"])
        fields["manufacturer"] = "X" + fields["manufacturer"]
        del fields["lot"]
        return LabelExtraction(label_id=path.stem, fields=fields)

    monkeypatch.setattr(eval_extract, "extract_label", predict)
    evaluation = eval_extract.evaluate_dataset(dataset)
    for condition, counts in evaluation["conditions"].items():
        assert counts["images"] == 1 and counts["decoded"] == 0
        assert counts["ocr"]["manufacturer"]["edits"] == 1
        lot = counts["ocr"]["lot"]
        assert lot["edits"] == lot["reference_characters"] == len(perfect_engine[condition]["fields"]["lot"])
        assert lot["observed"] == 0
    assert "0/0 (N/A)" in eval_extract.render_report(evaluation)


def test_extraction_exception_is_not_excluded(
    dataset: Path, perfect_engine: dict[str, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failed extraction remains in image counts and receives full deletion errors."""
    previous = eval_extract.extract_label

    def predict(path: Path) -> LabelExtraction:
        """Fail one condition while retaining controlled predictions for the others."""
        if path.parent.name == "hard":
            raise RuntimeError("controlled extraction failure")
        return previous(path)

    monkeypatch.setattr(eval_extract, "extract_label", predict)
    evaluation = eval_extract.evaluate_dataset(dataset)
    hard = evaluation["conditions"]["hard"]
    assert hard["images"] == hard["extraction_failures"] == 1
    assert hard["decoded"] == hard["gs1_exact"] == 0
    for score in hard["ocr"].values():
        assert score["edits"] == score["reference_characters"] and score["observed"] == 0
    assert evaluation["conditions"]["clean"]["gs1_exact"] == 1
    assert "controlled extraction failure" in eval_extract.render_report(evaluation)


@pytest.mark.parametrize("multiple", [False, True])
def test_partial_and_ambiguous_gs1(
    dataset: Path, perfect_engine: dict[str, dict[str, Any]], monkeypatch: pytest.MonkeyPatch, multiple: bool
) -> None:
    """Separate decoding from exact parsing, without selecting among multiple symbols."""

    def predict(path: Path) -> LabelExtraction:
        """Supply a wrong lot or two symbols to test strict match denominators."""
        parsed = dict(perfect_engine[path.parent.name]["barcode_ais"])
        if not multiple:
            parsed["10"] = "WRONG"
        result = BarcodeResult(type="Data Matrix", raw="unit-test prediction", parsed=parsed)
        return LabelExtraction(label_id=path.stem, barcodes=[result, result] if multiple else [result])

    monkeypatch.setattr(eval_extract, "extract_label", predict)
    for counts in eval_extract.evaluate_dataset(dataset)["conditions"].values():
        assert counts["images"] == counts["decoded"] == 1
        assert counts["gs1_exact"] == counts["gs1_per_ai"]["10"] == 0
        for ai in ("01", "17", "21"):
            assert counts["gs1_per_ai"][ai] == (0 if multiple else 1)


def test_geometry_probe(dataset: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Distinguish a detected outline from a correction within the fixed tolerance."""
    image = dataset / "hard/test_label_001_hard.png"
    truth = json.loads(image.with_suffix(".json").read_text(encoding="utf-8"))
    expected = truth["label_quad_px"]
    assert eval_extract._probe_geometry(image, expected) == (True, True, None)
    monkeypatch.setattr(eval_extract, "find_label_corners", lambda image: np.asarray(expected, dtype=np.float32) + 20)
    assert eval_extract._probe_geometry(image, expected) == (True, False, None)
    monkeypatch.setattr(eval_extract, "find_label_corners", lambda image: None)
    assert eval_extract._probe_geometry(image, expected) == (False, False, None)
    found, corrected, failure = eval_extract._probe_geometry(image.parent / "missing.png", expected)
    assert found is corrected is False
    assert "FileNotFoundError" in failure


def test_geometry_failure_count(
    dataset: Path, perfect_engine: dict[str, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Geometry-probe exceptions stay separate from extraction and OCR results."""
    monkeypatch.setattr(
        eval_extract, "_probe_geometry", lambda path, expected: (False, False, "controlled geometry failure")
    )
    evaluation = eval_extract.evaluate_dataset(dataset)
    for counts in evaluation["conditions"].values():
        assert counts["images"] == counts["geometry_failures"] == 1
        assert counts["detected"] == counts["corrected_within_10px"] == 0
        assert counts["extraction_failures"] == 0
    assert "controlled geometry failure" in eval_extract.render_report(evaluation)


@pytest.mark.parametrize(
    "problem",
    [
        "duplicate",
        "escape",
        "missing_truth",
        "missing_field",
        "empty_reference",
        "unknown_condition",
        "not_test_data",
        "corners",
        "ais",
        "symbols",
        "counts",
    ],
)
def test_invalid_dataset(dataset: Path, tmp_path: Path, problem: str) -> None:
    """Reject unscoreable truth or inconsistent manifests before computing results."""
    root = tmp_path / "broken"
    shutil.copytree(dataset, root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    truth_path = root / manifest["files"][0]["ground_truth"]
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    if problem == "duplicate":
        manifest["files"].append(manifest["files"][0])
        manifest["total_images"] += 1
    elif problem == "escape":
        manifest["files"][0]["image"] = "../outside.png"
    elif problem == "missing_truth":
        truth_path.unlink()
    elif problem == "missing_field":
        del truth["fields"]["lot"]
    elif problem == "empty_reference":
        truth["fields"]["lot"] = ""
    elif problem == "unknown_condition":
        truth["condition"] = "unknown"
    elif problem == "not_test_data":
        truth["test_data"] = False
    elif problem == "corners":
        truth["label_quad_px"] = [[0, 0]]
    elif problem == "ais":
        del truth["barcode_ais"]["21"]
    elif problem == "symbols":
        del truth["symbols"]
    else:
        manifest["conditions"]["clean"]["images"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    if problem != "missing_truth":
        truth_path.write_text(json.dumps(truth), encoding="utf-8")
    with pytest.raises((ValueError, OSError)):
        eval_extract._load_dataset(root)


def test_provenance_fingerprints(dataset: Path, tmp_path: Path) -> None:
    """Fingerprint actual input bytes, source and models without absolute output paths."""
    root = tmp_path / "copy"
    shutil.copytree(dataset, root)
    manifest, _ = eval_extract._load_dataset(root)
    first = eval_extract._provenance(root, manifest)
    assert first["dataset_sha256"] == eval_extract._provenance(dataset, manifest)["dataset_sha256"]
    assert first["settings"] == {"min_confidence": 0.8, "blur_threshold": 100.0}
    assert len(first["model_sha256"]) == 3
    assert all(len(value) == 64 for value in first["model_sha256"].values())
    image = root / manifest["files"][0]["image"]
    image.write_bytes(image.read_bytes() + b"test fingerprint change")
    assert first["dataset_sha256"] != eval_extract._provenance(root, manifest)["dataset_sha256"]


def test_report_and_read_only_inputs(dataset: Path, perfect_engine: dict[str, dict[str, Any]]) -> None:
    """Reports are deterministic and include denominators without changing inputs."""
    before = {path.relative_to(dataset): path.read_bytes() for path in dataset.rglob("*") if path.is_file()}
    first = eval_extract.render_report(eval_extract.evaluate_dataset(dataset))
    second = eval_extract.render_report(eval_extract.evaluate_dataset(dataset))
    assert first == second
    assert "1/1 (100.00%)" in first
    assert "0/1 (0.00%)" in first
    assert "Edits / reference characters" in first
    assert "All four exact given decode" in first
    assert "Symbols IoU >= 0.50" in first
    assert "No extraction or geometry-probe exceptions occurred" in first
    assert "src/cv/extract.py" in first
    after = {path.relative_to(dataset): path.read_bytes() for path in dataset.rglob("*") if path.is_file()}
    assert before == after


def test_formatting_helpers() -> None:
    """Keep zero denominators, whitespace and Markdown-sensitive observations explicit."""
    assert eval_extract._fraction(0, 0) == "0/0 (N/A)"
    assert eval_extract._fraction(3, 4) == "3/4 (75.00%)"
    cell = eval_extract._cell(" A|B\n`")
    assert "\\|" in cell and "\\n" in cell and "&#96;" in cell
    assert cell.startswith('" ')


def test_cli(
    dataset: Path, perfect_engine: dict[str, dict[str, Any]], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Write the computed Markdown report and print actual per-condition summaries."""
    report = tmp_path / "reports/cv_extract.md"
    assert eval_extract.main(["--dataset", str(dataset), "--output", str(report)]) == 0
    assert report.read_text(encoding="utf-8") == eval_extract.render_report(eval_extract.evaluate_dataset(dataset))
    output = capsys.readouterr().out
    assert "Evaluated 3 images; OCR and blur warning thresholds unchanged" in output
    for condition in eval_extract.CONDITIONS:
        assert f"{condition}: decoded=1/1, all_ais_match=1/1" in output


def test_cli_invalid_input(dataset: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Refuse invalid datasets and any report path inside the read-only input set."""
    report = tmp_path / "report.md"
    with pytest.raises(SystemExit) as missing:
        eval_extract.main(["--dataset", str(tmp_path / "missing"), "--output", str(report)])
    assert missing.value.code == 2 and not report.exists()
    assert "No such file" in capsys.readouterr().err
    with pytest.raises(SystemExit) as inside:
        eval_extract.main(["--dataset", str(dataset), "--output", str(dataset / "report.md")])
    assert inside.value.code == 2
    assert "read-only dataset" in capsys.readouterr().err
    assert not (dataset / "report.md").exists()


def test_real_evaluation(dataset: Path) -> None:
    """Exercise actual extraction for every condition without asserting invented accuracy."""
    evaluation = eval_extract.evaluate_dataset(dataset)
    assert evaluation["provenance"]["total_images"] == 3
    for counts in evaluation["conditions"].values():
        assert counts["images"] == 1 and counts["extraction_failures"] == 0
        assert counts["corrected_within_10px"] == 1
        assert counts["expected_symbols"] == 2
        assert 0 <= counts["matched_symbols"] <= 2
        assert 0 <= counts["gs1_exact"] <= counts["decoded"] <= 1
        for score in counts["ocr"].values():
            assert score["reference_characters"] > 0 and score["edits"] >= 0
