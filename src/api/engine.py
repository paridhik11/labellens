"""The label renderer behind a small interface (Step 24b).

`RealEngine` calls Parth's revision engine and renderers (`src.gen.revise`, `src.export`). Their libraries
(zxing-cpp, reportlab) are imported inside the methods, never at import time, so `src.api` stays importable and
testable on a machine without them (CI). Tests that cannot have the libraries put a fake engine on
`app.state.artwork_engine`.

This module only translates. It never edits the renderer, never creates an approval and never fills in an
identifier: a missing one raises `IdentifierRequired`, as the renderer does.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from src.common.schemas import ProductRecord

# Messages the renderer uses for layout failures (src/export/label_model.py, src/export/template.py).
LAYOUT_MESSAGE = re.compile(
    r"^(clipping or watermark_overlap|text_overflow|overlap|Barcode cannot fit|Font size|Slot is below|"
    r"Use a standard PDF font|Text must contain|Unsupported symbol|Barcode quiet zone|Invalid physical bounds)"
)


class RendererUnavailable(RuntimeError):
    """The rendering libraries are not installed in this environment."""


class LayoutFailure(ValueError):
    """The filled template does not fit (clipping, overlap, text overflow ...). `kind` is the renderer's own word."""

    def __init__(self, kind: str, message: str, slot: str = "") -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.slot = slot


@dataclass(frozen=True)
class Revision:
    """What revising a template for one confirmed edit produced. `label` is opaque to the API."""

    action: str  # KEEP, REGENERATE or NEEDS_INPUT
    reason: str
    required_identifier: str | None
    template: dict[str, Any]  # the new template version (slots, size, version number)
    record: ProductRecord  # the new product record
    change_log: tuple[dict[str, Any], ...]
    label: Any
    self_check: dict[str, str]


@dataclass(frozen=True)
class Rendered:
    """The bytes of one rendered draft."""

    pdf: bytes
    svg: bytes
    qr_png: bytes
    qr_svg: bytes
    visible_markings: tuple[str, ...]
    reference_sha256: str
    size_mm: tuple[float, float]


class ArtworkEngine(Protocol):
    """What `generateArtwork` needs from a renderer."""

    def revise(
        self, template: dict[str, Any], record: ProductRecord, change: dict[str, str], *, version_id: str,
        previous_version_id: str, actor: str, reason: str, test_data: bool, confirmed: dict[str, bool],
        requires_new_identifier: bool, allocated_identifier: str | None,
    ) -> Revision:
        """Revise the template and record for one edit (raises LayoutFailure, IdentifierRequired or ValueError)."""
        ...

    def render(self, revision: Revision, out_dir: Path, qr_payload: str) -> Rendered:
        """Render the draft PDF, SVG and QR of a revision that has artwork (raises LayoutFailure)."""
        ...


def _layout_or_raise(error: ValueError) -> None:
    """Re-raise a renderer ValueError as LayoutFailure when it is a layout message, otherwise unchanged."""
    message = str(error)
    if LAYOUT_MESSAGE.match(message):
        kind, _, rest = message.partition(":")
        raise LayoutFailure(kind.strip(), message, rest.strip()) from error
    raise error


class RealEngine:
    """Parth's renderer, called as GEN_HANDOFF.md describes."""

    def revise(
        self, template: dict[str, Any], record: ProductRecord, change: dict[str, str], *, version_id: str,
        previous_version_id: str, actor: str, reason: str, test_data: bool, confirmed: dict[str, bool],
        requires_new_identifier: bool, allocated_identifier: str | None,
    ) -> Revision:
        """Build the source snapshot from the current record, then revise it with `revise_template`."""
        try:
            from src.common.schemas import ChangeRequest as ChangeSchema
            from src.export.template import from_product
            from src.gen.revise import revise_template
        except ImportError as error:
            raise RendererUnavailable(f"The label renderer libraries are not installed: {error}") from error
        try:
            previous = from_product(
                template, record, version_id=previous_version_id, actor=actor,
                reason="source snapshot of the current product record", test_data=test_data,
            )
            result = revise_template(
                template, record, ChangeSchema(**change), previous_label=previous, version_id=version_id,
                actor=actor, reason=reason, confirmed=confirmed, requires_new_identifier=requires_new_identifier,
                allocated_identifier=allocated_identifier,
            )
        except KeyError as error:
            raise ValueError(f"product_incomplete: the product record has no extra value {error}") from error
        except ValueError as error:
            _layout_or_raise(error)
            raise
        return Revision(
            action=str(result.barcode_decision.action), reason=result.barcode_decision.reason,
            required_identifier=result.required_identifier, template=result.template, record=result.record,
            change_log=result.change_log, label=result.label, self_check=dict(result.self_check),
        )

    def render(self, revision: Revision, out_dir: Path, qr_payload: str) -> Rendered:
        """Write the PDF and SVG into `out_dir`, read the bytes back, and make the QR (the files are temporary)."""
        try:
            from src.export.label_model import reference_sha256
            from src.export.pdf import render_pdf
            from src.export.qr import make_qr
            from src.export.svg import render_svg
        except ImportError as error:
            raise RendererUnavailable(f"The label renderer libraries are not installed: {error}") from error
        label = revision.label
        try:
            pdf = render_pdf(label, out_dir / "label.pdf")
            svg = render_svg(label, out_dir / "label.svg")
        except ValueError as error:
            _layout_or_raise(error)
            raise
        sidecar = json.loads(Path(str(pdf) + ".json").read_text(encoding="utf-8"))
        qr = make_qr(qr_payload)
        return Rendered(
            pdf=pdf.read_bytes(), svg=svg.read_bytes(), qr_png=qr.png, qr_svg=qr.svg.encode("utf-8"),
            visible_markings=tuple(sidecar["visible_markings"]), reference_sha256=reference_sha256(label),
            size_mm=(label.width_mm, label.height_mm),
        )
