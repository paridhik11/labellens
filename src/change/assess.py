"""Assessment: impact items, barcode decisions, citations and needs_human (docs/CHANGE_SPEC.md sections 4 to 7).

Rules decide, retrieval cites, a human confirms. This module never says a label is compliant.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.change.fields import ENCODED_FIELDS
from src.change.impact import label_items
from src.change.models import Assessment, Edit, Item, LabelContext, Unassessed
from src.checker import citations as C
from src.common.schemas import Chunk
from src.ir.base import Retriever

_Q_NEW_DI = "changes that require use of a new device identifier new version or model"


def _specs(*pairs: tuple[str, str]) -> list[C.CitationSpec]:
    return [C.CitationSpec(q, frozenset({section}), "direct") for q, section in pairs]


# Fixed queries and accepted sections, written before use (CHANGE_SPEC.md section 6). Fields not listed have no
# citation: name and ref are internal consistency, sterilization and storage have no section in the device corpus.
FIELD_CITATIONS: dict[str, list[C.CitationSpec]] = {
    "manufacturer": _specs((C._Q_MFR, "801.1")),
    "manufacturer_address": _specs((C._Q_MFR, "801.1")),
    "udi_di": _specs((C._Q_UDI, "801.20")),
    "model": _specs((_Q_NEW_DI, "830.50")),
    "lot": _specs((C._Q_PI, "801.40")),
    "serial": _specs((C._Q_PI, "801.40")),
    "expiry": _specs((C._Q_PI, "801.40"), (C._Q_DATE, "801.18")),
    "rx_only": _specs((C._Q_RX, "801.109")),
}
NO_CITATION_FIELDS = ("name", "ref", "sterilization", "storage")


def _lookup(
    spec: C.CitationSpec, retriever: Retriever | None, chunks: Mapping[str, Chunk], k: int
) -> C.Citation | None:
    """One citation, or None when there is no retriever, the retriever fails, or no accepted hit is in the top k."""
    if retriever is None:
        return None
    try:
        return C.find_citation(spec, retriever, dict(chunks), k)
    except Exception:  # a retrieval failure leaves the item without a citation, flagged for a human
        return None


def assess(
    edits: Sequence[Edit], new_values: Mapping[str, str], contexts: Sequence[LabelContext], *, confirmed: bool,
    unassessed: Sequence[Unassessed] = (), warnings: Sequence[str] = (), retriever: Retriever | None = None,
    chunks: Mapping[str, Chunk] | None = None, k: int = 10,
) -> Assessment:
    """Assess edits against every label family of the product.

    `confirmed` says whether the person confirmed the change (it decides REGENERATE versus NEEDS_INPUT for an
    encoded change). `retriever` and `chunks` find citations; without them every cited field is needs_human.
    """
    chunks = chunks or {}
    invalid_encoded = [u.field for u in unassessed if u.reason in ("invalid_value", "ambiguous_date")
                       and u.field in ENCODED_FIELDS]
    items: list[Item] = []
    for ctx in contexts:
        items.extend(label_items(ctx, edits, new_values, confirmed=confirmed, invalid_encoded=invalid_encoded))
    cache: dict[tuple[str, int], C.Citation | None] = {}
    found: dict[str, C.Citation] = {}
    for item in items:
        missing: list[str] = []
        for name in dict.fromkeys(item.fields):
            for index, spec in enumerate(FIELD_CITATIONS.get(name, [])):
                if (name, index) not in cache:
                    cache[(name, index)] = _lookup(spec, retriever, chunks, k)
                cite = cache[(name, index)]
                if cite is None:
                    missing.append(name)
                else:
                    found[cite.chunk_id] = cite
                    if cite.chunk_id not in item.evidence_chunk_ids:
                        item.evidence_chunk_ids.append(cite.chunk_id)
        if missing:
            item.needs_human = True
            names = ', '.join(dict.fromkeys(missing))
            item.description += f" No supporting regulation passage was retrieved for {names}."
        elif not item.evidence_chunk_ids and any(f in NO_CITATION_FIELDS for f in item.fields):
            item.description += " No regulation passage applies to this field in the corpus, so none is cited."
    warns = list(warnings)
    if not contexts:
        warns.append("This product has no label registered, so nothing could be assessed against a label.")
    for u in unassessed:
        warns.append(f"Not assessed: {u.field or '(no field)'} ({u.reason}): {u.message}")
    human = sum(1 for i in items if i.needs_human)
    review = None
    if warns or human or not items:
        parts = [f"{human} of {len(items)} items need a person to decide." if items else "No items were produced."]
        review = "NEEDS_HUMAN_REVIEW: " + " ".join(parts + warns)
    return Assessment(
        items=items, citations=[c.model_dump(mode="json", exclude={"rank"}) for c in found.values()],
        warnings=warns, unassessed=list(unassessed), needs_human_review=review,
    )


def item_json(item: Item, change_id: str, impact_id: str, user_decision: str = "pending") -> dict[str, Any]:
    """An item as a contract AffectedLabel (CR-18 optional fields included)."""
    out: dict[str, Any] = {
        "impact_id": impact_id, "change_id": change_id, "label_id": item.label_id, "version_id": item.version_id,
        "item_kind": item.item_kind, "title": item.title, "description": item.description,
        "suggestion": item.suggestion, "evidence_chunk_ids": list(item.evidence_chunk_ids),
        "user_decision": user_decision, "needs_human": item.needs_human, "reason": item.description,
        "rule_ids": list(item.rule_ids),
    }
    if item.slot_id:
        out["slot_id"] = item.slot_id
    if item.barcode:
        out["barcode_decision"] = item.barcode.to_json()
    return out
