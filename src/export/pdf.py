"""Physical-size vector PDF export with extractable text."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from src.export.label_model import (
    MM_TO_PT,
    ApprovalRecord,
    Label,
    PassedCheck,
    primitives,
    validate_approval,
    validate_label,
    write_artifact,
)


def render_pdf(
    label: Label,
    path: Path,
    *,
    min_module_mm: float = 0.25,
    approval: ApprovalRecord | None = None,
    check: PassedCheck | None = None,
    authorized_reviewers: frozenset[str] = frozenset(),
) -> Path:
    """Write a one-page PDF at the exact label size, plus an audit sidecar.

    PDF points = mm * 72 / 25.4. Review highlights are never printed. A valid
    externally issued approval and passed check are needed to remove DRAFT.
    """
    validate_label(label, min_module_mm)
    approved = validate_approval(label, approval, check, authorized_reviewers)
    buffer = BytesIO()
    page = Canvas(buffer, pagesize=(label.width_mm * MM_TO_PT, label.height_mm * MM_TO_PT), invariant=1)
    page.setTitle(f"LabelLens {label.version_id}")
    if not approved or label.test_data:
        heading = (
            "TEST DATA | DRAFT" if not approved and label.test_data else "TEST DATA" if label.test_data else "DRAFT"
        )
        page.setFont("Helvetica", 9)
        page.drawString(2 * MM_TO_PT, (label.height_mm - 6) * MM_TO_PT, heading)
    for element in label.elements:
        for item in primitives(element):
            x, y = item.x * MM_TO_PT, (label.height_mm - item.y) * MM_TO_PT
            if item.kind in {"rect", "outline"}:
                page.setLineWidth(0.2 * MM_TO_PT)
                page.rect(
                    x,
                    y - item.h * MM_TO_PT,
                    item.w * MM_TO_PT,
                    item.h * MM_TO_PT,
                    stroke=int(item.kind == "outline"),
                    fill=int(item.kind == "rect"),
                )
            elif item.kind == "line":
                page.setLineWidth(0.3 * MM_TO_PT)
                page.line(x, y, x + item.w * MM_TO_PT, y - item.h * MM_TO_PT)
            elif item.kind == "text":
                page.setFont(item.font, item.size_pt)
                page.drawString(x, y, item.text)
            else:
                page.drawImage(
                    ImageReader(BytesIO(item.png)),
                    x,
                    y - item.h * MM_TO_PT,
                    width=item.w * MM_TO_PT,
                    height=item.h * MM_TO_PT,
                    mask="auto",
                )
    page.showPage()
    page.save()
    return write_artifact(path, buffer.getvalue(), label, approved, approval.check_id if approved else "")
