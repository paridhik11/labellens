"""The default label extractor for the API (Step 21c).

The CV libraries (cv2, zxingcpp, rapidocr) are imported inside the function, never at module import,
so `src.api` stays importable and testable on a machine without them (CI). Tests replace the extractor
on `app.state.extractor` with a stub that returns a prepared extraction.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from src.common.schemas import LabelExtraction

# An extractor reads one image file and returns the extraction plus the name of the mode that produced it.
Extractor = Callable[[Path], tuple[LabelExtraction, str]]
DEFAULT_MODE = "blind"  # uploaded labels have no known template, so no layout knowledge is assumed


class ExtractorUnavailable(RuntimeError):
    """The CV libraries are not installed in this environment."""


def extract_with_cv(path: Path) -> tuple[LabelExtraction, str]:
    """Run the unchanged CV extractor in blind mode. Raises ExtractorUnavailable when the CV libraries are missing."""
    try:
        from src.cv.extract import extract_label
    except ImportError as error:
        raise ExtractorUnavailable(f"CV libraries are not installed: {error}") from error
    return extract_label(path, mode=DEFAULT_MODE), DEFAULT_MODE
