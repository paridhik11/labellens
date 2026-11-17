"""A fake renderer for the API tests (Step 24b): no zxing-cpp, reportlab or OpenCV, so CI can run them.

`FakeEngine` follows the same interface as `src.api.engine.RealEngine`. It decides KEEP, REGENERATE and
NEEDS_INPUT with the same rule the API uses (an encoded value changes and is confirmed), fails the layout when a
slot starts above the 9 mm DRAFT band, and returns small deterministic files whose bytes include the version id,
so every version has its own hash like the real PDF does.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from src.api.engine import LayoutFailure, Rendered, RendererUnavailable, Revision
from src.change.fields import ENCODED_FIELDS
from src.common.schemas import IdentifierRequired, ProductRecord

MARK = "DRAFT, not for production"


class FakeEngine:
    """Stands in for the real renderer."""

    def __init__(self) -> None:
        self.revise_calls: list[dict[str, Any]] = []
        self.render_calls = 0
        self.fail_render: Exception | None = None
        self.unavailable = False

    def revise(
        self, template: dict[str, Any], record: ProductRecord, change: dict[str, str], *, version_id: str,
        previous_version_id: str, actor: str, reason: str, test_data: bool, confirmed: dict[str, bool],
        requires_new_identifier: bool, allocated_identifier: str | None,
    ) -> Revision:
        """Apply one edit to a copy of the record and template, like `revise_template`."""
        if self.unavailable:
            raise RendererUnavailable("The label renderer libraries are not installed (fake)")
        self.revise_calls.append({**change, "confirmed": dict(confirmed), "test_data": test_data})
        for slot in template["slots"]:
            if slot["bbox_mm"][1] < 9:
                kind = "clipping or watermark_overlap"
                raise LayoutFailure(kind, f"{kind}: {slot['id']}", slot["id"])
        if record.udi_di == "00000000000000" and not test_data:
            raise IdentifierRequired("Test-only GTIN requires a visibly marked test label")
        data = record.model_dump()
        data["version"] += 1
        field = change["field"]
        if field in ("udi_di", "name", "model", "manufacturer", "manufacturer_address", "sterilization", "storage"):
            data[field] = change["new_value"]
        else:
            data["extra"][field] = change["new_value"]
        if allocated_identifier:
            data["udi_di"] = allocated_identifier
        new_template = copy.deepcopy(template)
        new_template["version"] += 1
        encoded = field in ENCODED_FIELDS or allocated_identifier is not None
        action = "REGENERATE" if encoded else "KEEP"
        log = ({"change_id": change["change_id"], "field": field, "before": change["old_value"],
                "after": change["new_value"], "actor": actor, "reason": reason, "version_id": version_id},)
        return Revision(
            action=action, reason="fake", required_identifier=None, template=new_template,
            record=ProductRecord.model_validate(data), change_log=log, label={"version_id": version_id,
            "values": data}, self_check={"status": "NEEDS_HUMAN_REVIEW", "scope": "fake renderer, nothing was checked"},
        )

    def render(self, revision: Revision, out_dir: Path, qr_payload: str) -> Rendered:
        """Return bytes that depend on the version id and the record values, plus the draft mark."""
        self.render_calls += 1
        if self.fail_render is not None:
            raise self.fail_render
        label = revision.label
        tag = f"{label['version_id']}|{sorted(label['values'].items())}".encode()
        return Rendered(
            pdf=b"%PDF-1.4 fake " + tag, svg=b"<svg xmlns='http://www.w3.org/2000/svg'><!-- " + tag + b" --></svg>",
            qr_png=b"\x89PNG fake " + qr_payload.encode(), qr_svg=b"<svg><!-- " + qr_payload.encode() + b" --></svg>",
            visible_markings=(MARK,), reference_sha256="f" * 64, size_mm=(100.0, 60.0),
        )
