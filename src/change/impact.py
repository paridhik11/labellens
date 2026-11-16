"""Impact rule: which labels, template slots and symbols a set of edits touches (docs/CHANGE_SPEC.md section 4).

Matching is by exact slot `field` after alias resolution, and the slot type must be right. A rule decides a text slot
refill and a barcode KEEP or REGENERATE. Everything else is left to a human (`needs_human` stays True here, and the
assessment adds the citation check).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.change.barcode import PayloadUnbuildable, build_ais, decide_barcode
from src.change.fields import ENCODED_FIELDS, resolve_field
from src.change.models import Edit, Item, LabelContext
from src.checker import gs1

SYMBOL_FOR_FIELD = {"manufacturer": "manufacturer", "manufacturer_address": "manufacturer", "expiry": "expiry"}
BARCODE_FIELDS = (*ENCODED_FIELDS, "model")
TEMPLATE_RULE = "no template field"
SUGGESTION = {"KEEP": "no_change", "REGENERATE": "edit_required", "NEEDS_INPUT": "review_suggested"}


def _slots(template: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    return list(template["slots"]) if template else []


def label_items(
    ctx: LabelContext, edits: Sequence[Edit], new_values: Mapping[str, str], *, confirmed: bool,
    invalid_encoded: Sequence[str] = (),
) -> list[Item]:
    """The affected items of one label."""
    items: list[Item] = []
    slots = _slots(ctx.template)
    base = dict(label_id=ctx.label_id, version_id=ctx.version_id)
    edited = [e.field for e in edits]
    barcode_slot = next((s for s in slots if s["type"] == "barcode"), None)
    symbol_items: dict[str, Item] = {}

    for edit in edits:
        text_slots = [s for s in slots if s["type"] == "text" and resolve_field(s["field"]) == edit.field]
        for slot in text_slots:
            note = ""
            if edit.field == "sterilization":
                note = " Templates have no sterilization symbol, so any symbol on the artwork cannot be assessed."
            items.append(Item(
                key=f"{ctx.label_id}|{slot['id']}|{edit.field}", item_kind="text", slot_id=slot["id"],
                title=f"{edit.field} text", suggestion="edit_required", rule_ids=["I-TEXT"], fields=[edit.field],
                description=(f"The slot {slot['id']} shows {edit.field}. It must be refilled with the new value "
                             f"(was {edit.old_value!r}, now {edit.new_value!r}). This says what to update, "
                             f"not whether the result is compliant." + note),
                needs_human=False, **base,
            ))
        symbol = SYMBOL_FOR_FIELD.get(edit.field)
        for slot in (s for s in slots if s["type"] == "symbol" and symbol and s.get("symbol_name") == symbol):
            item = symbol_items.get(slot["id"])
            if item is None:
                item = symbol_items[slot["id"]] = Item(
                    key=f"{ctx.label_id}|{slot['id']}|symbol", item_kind="symbol", slot_id=slot["id"],
                    title=f"{symbol} symbol", suggestion="review_suggested", rule_ids=["I-SYMBOL"], fields=[],
                    description=(f"The {symbol} symbol sits beside text that changes. The symbol image does not "
                                 f"depend on the value, so no rule says it must change. A person decides."),
                    needs_human=True, **base,
                )
                items.append(item)
            item.fields.append(edit.field)
        covered = bool(text_slots) or (edit.field in ENCODED_FIELDS and barcode_slot is not None)
        if not covered:
            reason = ("the label has no template" if ctx.template is None
                      else f"no slot of template {ctx.template.get('template_id')} shows {edit.field}")
            items.append(Item(
                key=f"{ctx.label_id}|none|{edit.field}", item_kind="linked_label",
                title=f"{edit.field}: {TEMPLATE_RULE}",
                suggestion="review_suggested", rule_ids=["I-NOSLOT"], fields=[edit.field],
                description=(f"Nothing can be refilled automatically: {reason}. If the text is part of the fixed "
                             f"background artwork, LabelLens cannot update it. A person must check this label."),
                needs_human=True, **base,
            ))

    if barcode_slot is not None:
        items.append(_barcode_item(ctx, edits, new_values, barcode_slot, edited, confirmed, invalid_encoded, base))
    elif any(f in edited for f in BARCODE_FIELDS):
        items.append(Item(
            key=f"{ctx.label_id}|none|barcode", item_kind="linked_label", title="Barcode: no barcode slot",
            suggestion="review_suggested", rule_ids=["I-NOBARCODE"], fields=[f for f in BARCODE_FIELDS if f in edited],
            description="A changed value is encoded in the barcode, but this label's template has no barcode slot. "
                        "A person must check the barcode.", needs_human=True, **base,
        ))
    return items


def _barcode_item(
    ctx: LabelContext, edits: Sequence[Edit], new_values: Mapping[str, str], slot: Mapping[str, Any],
    edited: Sequence[str], confirmed: bool, invalid_encoded: Sequence[str], base: Mapping[str, str],
) -> Item:
    """The barcode decision of one label as an item."""
    outcome = decide_barcode(ctx.old_values, new_values, edited, symbology=slot["symbology"], confirmed=confirmed,
                             invalid_encoded=invalid_encoded)
    suggestion = SUGGESTION[outcome.decision]
    needs_human = outcome.decision == "NEEDS_INPUT"
    description = outcome.reason
    rule_ids = list(outcome.rule_ids)
    if ctx.printed_barcode:
        try:
            matches = build_ais(ctx.old_values) == ctx.printed_barcode
        except (PayloadUnbuildable, ValueError):
            matches = False
        if not matches:
            needs_human = True
            rule_ids.append("I-PRINTED-DIFFERS")
            description += (" The barcode read from the label differs from the one built from the product record "
                            "(printed_barcode_differs_from_record). The printed one is the truth about the label.")
    fields = [f for f in BARCODE_FIELDS if f in edited]
    return Item(
        key=f"{ctx.label_id}|{slot['id']}|barcode", item_kind="barcode", slot_id=slot["id"],
        title=f"Barcode: {outcome.decision}", description=description, suggestion=suggestion, rule_ids=rule_ids,
        fields=fields, needs_human=needs_human, barcode=outcome, **base,
    )


def parse_ais_safe(raw: str) -> dict[str, str] | None:
    """AIs of a decoded raw payload, or None when it does not parse."""
    try:
        return gs1.parse_gs1(raw)
    except ValueError:
        return None
