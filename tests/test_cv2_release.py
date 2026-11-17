"""The committed fresh-set verdict controls the public extractor default."""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from src.cv.extract import DEFAULT_PHOTO_PROFILE, extract_label, extract_label_modes


def test_frozen_release_default_matches_gate() -> None:
    """A successful frozen gate promotes CV2 while keeping public profile defaults aligned."""
    release = json.loads(Path("scripts/cv_experiments/config/cv2_release.json").read_text())
    expected = "cv2" if release["gate_passed"] else "baseline"
    assert release["profile"] == DEFAULT_PHOTO_PROFILE == expected
    for function in [extract_label, extract_label_modes]:
        assert inspect.signature(function).parameters["photo_profile"].default == expected
