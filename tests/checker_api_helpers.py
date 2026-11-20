"""Shared setup for the checker API tests: a stub extractor, image files on disk and bm25 retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from src.api.seed import LABEL_ID, PRODUCT_ID
from src.checker.settings import CheckerSettings, RetrievalSettings
from src.checker.synthetic import extraction_from_truth
from src.common.schemas import LabelExtraction

EDITOR, REVIEWER = "usr_demo_editor", "usr_demo_reviewer"
L2, L3 = "lbv_exampledevice_carton_l2", "lbv_exampledevice_carton_l3"


class StubExtractor:
    """Replaces the CV extractor: returns a prepared extraction and counts calls (no cv2, zxingcpp or rapidocr)."""

    def __init__(self, record: dict[str, Any]) -> None:
        self.calls = 0
        self.record = record
        self.fields = {
            "product_name": record["name"], "manufacturer": record["manufacturer"],
            "manufacturer_address": record["manufacturer_address"], "model": f"REF: {record['model']}",
            "lot": f"LOT: {record['extra']['lot']}", "expiry": f"EXP: {record['extra']['expiry']}",
        }
        self.error: Exception | None = None

    def ais(self) -> dict[str, str]:
        """GS1 values that agree with the product record (the seed's UDI-DI is the all-zero test placeholder)."""
        return {"01": self.record["udi_di"], "17": "280331", "10": self.record["extra"]["lot"],
                "21": self.record["extra"]["serial"]}

    def __call__(self, path: Path) -> tuple[LabelExtraction, str]:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return extraction_from_truth(path.stem, self.fields, self.ais()), "stub"


def h(user: str = EDITOR) -> dict[str, str]:
    """Headers naming the calling user."""
    return {"X-User-Id": user}


def install(client: TestClient, files: Path, monkeypatch: Any) -> StubExtractor:
    """Point the app at a stub extractor, bm25 retrieval and a folder holding empty images for L2 and L3."""
    (files / "files").mkdir(parents=True, exist_ok=True)
    for name in (L2, L3):
        (files / "files" / f"{name}.png").write_bytes(b"")
    monkeypatch.setenv("LABELLENS_FILES_DIR", str(files))
    record = client.get(f"/products/{PRODUCT_ID}", headers=h()).json()["record"]
    stub = StubExtractor(record)
    client.app.state.extractor = stub
    client.app.state.checker_settings = CheckerSettings(retrieval=RetrievalSettings(method="bm25"))
    return stub


__all__ = ["EDITOR", "L2", "L3", "LABEL_ID", "REVIEWER", "StubExtractor", "h", "install"]
