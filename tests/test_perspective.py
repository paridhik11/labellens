"""Image-only detection, aspect-ratio correction and honest scoring tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

cv2 = pytest.importorskip("cv2")
np = pytest.importorskip("numpy")
pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from src.cv import perspective  # noqa: E402
from src.gen.augment import augment_label  # noqa: E402


def label() -> Image.Image:
    """Create a test-only label with visible border and coloured orientation marks."""
    pixels = np.full((300, 500, 3), 255, dtype=np.uint8)
    cv2.rectangle(pixels, (3, 3), (496, 296), (0, 0, 0), 2)
    cv2.rectangle(pixels, (50, 50), (180, 120), (240, 20, 20), -1)
    cv2.rectangle(pixels, (320, 180), (440, 250), (20, 20, 240), -1)
    cv2.putText(pixels, "TEST DATA", (100, 170), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    return Image.fromarray(pixels)


@pytest.mark.parametrize("condition", ["clean", "moderate", "hard"])
def test_correction_coordinates(condition: str) -> None:
    """Detect synthetic rotated/perspective boundaries and map all four corners."""
    photo, _, truth = augment_label(label(), condition, 7001)
    pixels = np.asarray(photo)
    before = pixels.copy()
    result = perspective.correct_perspective(pixels, 5 / 3, output_width=500)
    assert result is not None
    assert np.array_equal(pixels, before)
    assert result.image.shape == (300, 500, 3)
    assert np.linalg.norm(result.corners - np.array(truth), axis=1).max() <= 10
    projected = cv2.perspectiveTransform(result.corners[None].astype(np.float32), result.homography)[0]
    assert np.allclose(projected, [[0, 0], [499, 0], [499, 299], [0, 299]], atol=0.001)
    again = perspective.correct_perspective(pixels, 5 / 3, output_width=500)
    assert np.array_equal(again.image, result.image)
    assert result.image[75, 100, 0] > result.image[75, 100, 2] + 100
    assert result.image[210, 380, 2] > result.image[210, 380, 0] + 100


@pytest.mark.parametrize("ratio,width", [(0, 500), (-1, 500), (float('nan'), 500),
                                           (True, 500), (1, 1), (1, True), (0.001, 500)])
def test_invalid_geometry(ratio: float, width: int) -> None:
    """Reject invalid aspect ratios, dimensions and unsafe raster sizes."""
    with pytest.raises(ValueError):
        perspective.correct_perspective(np.asarray(label()), ratio, output_width=width)


def test_absent_boundary_and_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return None on blank input and exercise fallback without extractor changes."""
    assert perspective.correct_perspective(np.full((200, 300, 3), 255, dtype=np.uint8), 1.5) is None
    monkeypatch.setattr(perspective, "find_label_corners", lambda _: None)
    corners = np.array([[10, 10], [290, 10], [290, 190], [10, 190]], dtype=np.float32)
    monkeypatch.setattr(perspective, "find_label_corners_fallback", lambda _: corners)
    result = perspective.correct_perspective(np.asarray(label()), 2, output_width=400)
    assert result.detector == "boundary_fallback" and result.image.shape == (200, 400, 3)


def test_evaluation_counts_misses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Count detection failure in the denominator and test the CLI on saved images."""
    label().save(tmp_path / "photo.png")
    (tmp_path / "truth.json").write_text(json.dumps({"condition": "hard", "label_quad_px": [[0, 0]] * 4}))
    (tmp_path / "manifest.json").write_text(json.dumps({"files": [
        {"image": "photo.png", "ground_truth": "truth.json"}]}))
    monkeypatch.setattr(perspective, "correct_perspective", lambda *args: None)
    result = perspective.evaluate_dataset(tmp_path, 5 / 3)
    assert result["hard"]["images"] == 1 and result["hard"]["success_rate"] == 0
    assert result["clean"]["success_rate"] is None
    assert perspective.main(["--dataset", str(tmp_path), "--aspect-ratio", "1.6667"]) == 0


def test_benchmark_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check seeded aggregation and persisted reporting without a long generation job."""
    from scripts.cv_experiments import eval_perspective

    metrics = {name: {"images": 10, "detected": 9, "within_10px": 8}
               for name in ("clean", "moderate", "hard")}
    monkeypatch.setattr(eval_perspective, "generate_dataset", lambda *args, **kwargs: {})
    monkeypatch.setattr(eval_perspective, "evaluate_dataset", lambda *args: metrics)
    assert eval_perspective.main(["--output", str(tmp_path), "--seeds", "7001", "7002"]) == 0
    report = json.loads((tmp_path / "evaluation.json").read_text())
    assert report["totals"]["hard"] == {"images": 20, "detected": 18, "within_10px": 16}
    with pytest.raises(SystemExit):
        eval_perspective.main(["--seeds", "1", "1"])
