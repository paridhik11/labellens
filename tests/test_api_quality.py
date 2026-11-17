"""Step 24a: the photo-quality gate. `judge` is pure; `measure` and `assess_photo` need OpenCV (skipped without it)."""

from __future__ import annotations

import pytest

from src.api.extractor import ExtractorUnavailable
from src.api.quality import DEFAULT, MESSAGES, Thresholds, judge

GOOD = {"sharpness": 900.0, "contrast": 100.0, "glare_blob": 0.0, "glare_edge": 255.0}


def test_judge_accepts_good_numbers_and_names_every_failed_reason() -> None:
    assert judge(GOOD).ok
    assert judge({**GOOD, "sharpness": 50.0}).reasons == ("blur",)
    assert judge({**GOOD, "contrast": 10.0}).reasons == ("low_contrast",)
    assert judge({**GOOD, "glare_blob": 0.05, "glare_edge": 30.0}).reasons == ("glare",)
    both = judge({**GOOD, "sharpness": 50.0, "glare_blob": 0.05, "glare_edge": 30.0})
    assert both.reasons == ("blur", "glare") and not both.ok


def test_glare_needs_both_a_big_enough_blob_and_a_soft_edge() -> None:
    assert judge({**GOOD, "glare_blob": 0.30, "glare_edge": 110.0}).ok  # a large white label with a hard edge
    assert judge({**GOOD, "glare_blob": 0.005, "glare_edge": 10.0}).ok  # a tiny highlight
    assert judge({**GOOD, "glare_blob": 0.02, "glare_edge": 59.9}).reasons == ("glare",)  # exactly at the cut-offs


def test_cut_offs_are_exclusive_at_the_boundary() -> None:
    assert judge({**GOOD, "sharpness": DEFAULT.min_sharpness}).ok
    assert judge({**GOOD, "contrast": DEFAULT.min_contrast}).ok
    assert not judge({**GOOD, "sharpness": DEFAULT.min_sharpness - 0.1}).ok


def test_error_body_follows_the_contract_error_shape() -> None:
    body = judge({**GOOD, "sharpness": 50.0}).error_body()
    assert set(body) == {"error", "message", "details"} and body["error"] == "retake_photo"
    assert MESSAGES["blur"] in body["message"]
    assert body["details"]["reasons"] == ["blur"] and body["details"]["thresholds"]["min_sharpness"] == 200.0
    assert body["details"]["metrics"]["sharpness"] == 50.0


def test_custom_thresholds_change_the_verdict() -> None:
    assert judge({**GOOD, "sharpness": 150.0}, Thresholds(min_sharpness=100.0)).ok
    assert not judge({**GOOD, "sharpness": 150.0}, Thresholds(min_sharpness=300.0)).ok


# ---------------------------------------------------------------- images (need OpenCV)


@pytest.fixture()
def cv():
    """cv2 and numpy, or skip the test when the CV libraries are not installed."""
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    return cv2, np


def label_photo(cv, size: int = 800):
    """A grey backdrop with a white label (hard edges) carrying black text-like bars."""
    cv2, np = cv
    img = np.full((size, size), 90, np.uint8)
    cv2.rectangle(img, (60, 60), (560, 560), 255, -1)
    for row in range(10):
        y = 90 + row * 45
        for col in range(8):
            x = 85 + col * 58
            cv2.rectangle(img, (x, y), (x + 40, y + 16), 0, -1)
    return img


def test_sharp_label_passes(cv) -> None:
    from src.api.quality import measure

    assert judge(measure(label_photo(cv))).ok


def test_heavy_blur_is_rejected(cv) -> None:
    from src.api.quality import measure

    cv2, _ = cv
    blurred = cv2.GaussianBlur(label_photo(cv), (0, 0), 8)
    report = judge(measure(blurred))
    assert "blur" in report.reasons and report.metrics["sharpness"] < 200


def test_flat_picture_is_rejected_for_contrast(cv) -> None:
    from src.api.quality import measure

    _, np = cv
    flat = np.full((600, 800), 128, np.uint8)
    assert "low_contrast" in judge(measure(flat)).reasons


def test_soft_glare_spot_is_rejected_but_a_white_label_is_not(cv) -> None:
    from src.api.quality import measure

    cv2, np = cv
    base = label_photo(cv).astype(np.float32)
    yy, xx = np.mgrid[0:800, 0:800]
    spot = 600.0 * np.exp(-(((xx - 680) ** 2 + (yy - 680) ** 2) / (2 * 60.0**2)))  # soft, saturating in the middle
    glared = np.clip(base + spot, 0, 255).astype(np.uint8)
    assert "glare" in judge(measure(glared)).reasons
    assert "glare" not in judge(measure(label_photo(cv))).reasons


def test_flat_white_render_is_not_glare(cv) -> None:
    from src.api.quality import measure

    cv2, np = cv
    page = np.full((800, 800), 255, np.uint8)
    cv2.rectangle(page, (100, 100), (700, 700), 200, 3)
    for y in range(150, 650, 60):
        cv2.rectangle(page, (150, y), (650, y + 20), 0, -1)
    assert "glare" not in judge(measure(page)).reasons


def test_resolution_does_not_change_the_verdict(cv) -> None:
    from src.api.quality import measure

    cv2, _ = cv
    big = cv2.resize(label_photo(cv), (2400, 2400), interpolation=cv2.INTER_NEAREST)
    assert judge(measure(big)).ok


def test_assess_photo_reads_a_file_and_rejects_an_undecodable_one(cv, tmp_path) -> None:
    from src.api.quality import assess_photo

    cv2, _ = cv
    good = tmp_path / "good.png"
    cv2.imwrite(str(good), label_photo(cv))
    assert assess_photo(good).ok
    broken = tmp_path / "broken.png"
    broken.write_bytes(b"not an image")
    with pytest.raises(ValueError):
        assess_photo(broken)


def test_assess_photo_without_opencv_raises_extractor_unavailable(tmp_path, monkeypatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "cv2":
            raise ImportError("no cv2")
        return real_import(name, *args, **kwargs)

    from src.api.quality import assess_photo

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ExtractorUnavailable):
        assess_photo(tmp_path / "x.png")
