"""Step 22b: change assessment rules (fields, parser, barcode decision, impact, citations, needs_human).

Synthetic products and label versions only. The test GTIN 00000000000000 is the GS1 test placeholder and
12345678901231 is a made-up number with a valid check digit; neither is a real identifier.
"""
from __future__ import annotations

import pytest

from src.change.assess import assess, item_json
from src.change.barcode import PayloadUnbuildable, build_payload, decide_barcode
from src.change.fields import normalise_value, record_values, resolve_field
from src.change.models import ChangeError, Edit, LabelContext
from src.change.parser import parse_request, parse_rules, validate_edits
from src.common.schemas import Chunk, Hit, ProductRecord

OLD = {
    "name": "Test Pump", "model": "TP-1", "manufacturer": "Example Medical", "manufacturer_address": "1 Test Road",
    "udi_di": "00000000000000", "sterilization": "Ethylene oxide (EO)", "storage": "Store dry",
    "lot": "LOT001", "expiry": "2028-12-31", "serial": "SN001", "ref": "R1", "rx_only": "",
}
NEW_DI = "12345678901231"
SLOTS = [
    {"id": "name", "type": "text", "field": "product_name", "size_pt": 10, "bbox_mm": [5, 12, 50, 6]},
    {"id": "addr", "type": "text", "field": "manufacturer_address", "size_pt": 7, "bbox_mm": [5, 20, 50, 8]},
    {"id": "ster", "type": "text", "field": "sterilization", "size_pt": 7, "bbox_mm": [5, 30, 50, 6]},
    {"id": "mfr_sym", "type": "symbol", "field": "manufacturer", "symbol_name": "manufacturer",
     "bbox_mm": [60, 12, 8, 8]},
    {"id": "exp_sym", "type": "symbol", "field": "expiry", "symbol_name": "expiry", "bbox_mm": [60, 22, 8, 8]},
    {"id": "udi", "type": "barcode", "field": "udi", "symbology": "GS1_DataMatrix", "bbox_mm": [60, 30, 20, 20]},
]


def ctx(label_id: str = "lbl_a", template: bool | list = True, **kw) -> LabelContext:
    tpl = None if template is False else {"template_id": "tpl_a", "version": 1,
                                          "slots": SLOTS if template is True else template}
    return LabelContext(label_id=label_id, version_id=f"lbv_{label_id}", old_values=dict(OLD), template=tpl, **kw)


def edits_of(**changes: str) -> tuple[list[Edit], dict[str, str]]:
    new = {**OLD, **changes}
    return [Edit(f, OLD[f], v) for f, v in changes.items()], new


# ---------------------------------------------------------------- fields


def test_aliases_and_values() -> None:
    assert resolve_field("Product_Name") == "name"
    assert resolve_field("GTIN") == "udi_di"
    assert resolve_field("Expiration date") == "expiry"
    assert resolve_field("colour") is None
    assert normalise_value("expiry", "30 April 2028") == "2028-04-30"
    assert normalise_value("expiry", "April 30, 2028") == "2028-04-30"
    assert normalise_value("rx_only", "Yes") == "true"
    assert normalise_value("storage", "  Keep   dry ") == "Keep dry"


@pytest.mark.parametrize("field,value,code", [
    ("expiry", "03/04/2028", "ambiguous_date"), ("expiry", "2028-02-30", "invalid_value"),
    ("expiry", "soon", "invalid_value"), ("udi_di", "1234567890123", "invalid_value"),
    ("udi_di", "12345678901234", "invalid_value"), ("lot", "X" * 21, "invalid_value"),
    ("lot", "bad lot~", "invalid_value"), ("rx_only", "maybe", "invalid_value"), ("name", "   ", "invalid_value"),
])
def test_invalid_values(field: str, value: str, code: str) -> None:
    from src.change.fields import InvalidValue

    with pytest.raises(InvalidValue) as error:
        normalise_value(field, value)
    assert error.value.code == code


def test_record_values_reads_extra() -> None:
    record = ProductRecord(product_id="p", name="N", extra={"lot": "L1", "rx_only": "true"})
    values = record_values(record)
    assert values["lot"] == "L1" and values["rx_only"] == "true" and values["expiry"] == ""


# ---------------------------------------------------------------- validate_edits (structured)


def test_validate_edits_fills_old_value_and_normalises() -> None:
    result = validate_edits([{"field": "expiry date", "new_value": "30 April 2028"}], OLD)
    assert result.edits == [Edit("expiry", "2028-12-31", "2028-04-30")]
    assert not result.unassessed and not result.warnings


def test_validate_edits_unknown_field_is_unassessed() -> None:
    result = validate_edits([{"field": "colour", "new_value": "red"}, {"field": "lot", "new_value": "LOT002"}], OLD)
    assert [e.field for e in result.edits] == ["lot"]
    assert result.unassessed[0].reason == "unknown_field" and "Supported fields" in result.unassessed[0].message


def test_validate_edits_invalid_value_is_unassessed() -> None:
    result = validate_edits([{"field": "udi_di", "new_value": "123"}], OLD)
    assert not result.edits and result.unassessed[0].reason == "invalid_value"


def test_validate_edits_old_value_mismatch_warns_and_record_wins() -> None:
    result = validate_edits([{"field": "lot", "old_value": "LOT999", "new_value": "LOT002"}], OLD)
    assert result.edits[0].old_value == "LOT001" and "old_value_mismatch" in result.warnings[0]


def test_validate_edits_no_change_and_duplicate_are_refused() -> None:
    with pytest.raises(ChangeError) as error:
        validate_edits([{"field": "udi_di", "old_value": "00000000000000", "new_value": "00000000000000"}], OLD)
    assert error.value.code == "no_change" and "nothing to change" in error.value.message
    with pytest.raises(ChangeError) as error:
        validate_edits([{"field": "lot", "new_value": "A"}, {"field": "batch", "new_value": "B"}], OLD)
    assert error.value.code == "duplicate_field"


# ---------------------------------------------------------------- text parser


@pytest.mark.parametrize("text,expected", [
    ("Update the sterilization method from ethylene oxide (EO) to gamma irradiation.",
     {"field": "sterilization", "new_value": "gamma irradiation", "old_value": "ethylene oxide (EO)"}),
    ("Change the lot to LOT002", {"field": "lot", "new_value": "LOT002"}),
    ("set the expiry to 30 April 2028", {"field": "expiry", "new_value": "30 April 2028"}),
    ("lot: LOT002", {"field": "lot", "new_value": "LOT002"}),
    ("The new lot is LOT002.", {"field": "lot", "new_value": "LOT002"}),
    ("storage -> Keep cool", {"field": "storage", "new_value": "Keep cool"}),
    ('replace address with "9 New Street" ', None),  # no supported pattern, must not guess
])
def test_parser_patterns(text: str, expected: dict | None) -> None:
    result = parse_rules(text)
    if expected is None:
        assert result.status != "parsed"
    else:
        assert result.status == "parsed" and result.edits == [expected]


def test_parser_two_clauses() -> None:
    result = parse_rules("change the lot to LOT002 and the expiry to 2029-01-31")
    assert [e["field"] for e in result.edits] == ["lot", "expiry"]


@pytest.mark.parametrize("text,status", [
    ("", "empty"), ("Switch to gamma", "unknown"), ("change the model and lot to X", "ambiguous"),
    ("do not change the lot to LOT002", "ambiguous"), ("change the sterilization", "ambiguous"),
    ("set expiry to 03/04/2028", "ambiguous"), ("set the udi to 123", "ambiguous"),
])
def test_parser_refuses(text: str, status: str) -> None:
    result = parse_rules(text)
    assert result.status == status and not result.edits and result.issues


def test_one_bad_clause_refuses_the_whole_request() -> None:
    result = parse_rules("change the lot to LOT002; change the colour to red")
    assert result.status in ("ambiguous", "unknown") and not result.edits


class FakeProvider:
    def __init__(self, proposals=None, error: Exception | None = None) -> None:
        self.proposals, self.error, self.calls = proposals or [], error, 0

    def propose_edits(self, raw_text: str, fields: tuple[str, ...]) -> list[dict[str, str]]:
        self.calls += 1
        if self.error:
            raise self.error
        return self.proposals


def test_provider_not_called_when_rules_parse_or_off() -> None:
    provider = FakeProvider([{"field": "lot", "new_value": "ZZZ"}])
    assert parse_request("change the lot to LOT002", provider).source == "rules" and provider.calls == 0
    assert parse_request("Switch to gamma", None).status == "unknown"


def test_provider_valid_proposal_is_used_and_marked_llm() -> None:
    text = "please make the batch code ABC123 from now on"
    result = parse_request(text, FakeProvider([{"field": "batch", "new_value": "ABC123"}]))
    assert result.status == "parsed" and result.source == "llm"
    assert result.edits == [{"field": "lot", "new_value": "ABC123"}]


@pytest.mark.parametrize("proposal", [
    {"field": "lot", "new_value": "INVENTED9"},  # value not in the typed text
    {"field": "colour", "new_value": "ABC123"},  # unknown field
    {"field": "udi_di", "new_value": "ABC123"},  # fails the value rule
])
def test_provider_bad_proposals_are_dropped(proposal: dict) -> None:
    result = parse_request("please make the batch code ABC123 from now on", FakeProvider([proposal]))
    assert result.status != "parsed" and result.source == "rules"


def test_provider_error_falls_back_to_rules() -> None:
    result = parse_request("Switch to gamma", FakeProvider(error=RuntimeError("down")))
    assert result.status == "unknown" and result.source == "rules"


# ---------------------------------------------------------------- barcode


def test_build_payload() -> None:
    assert build_payload(OLD) == "(01)00000000000000(17)281231(10)LOT001(21)SN001"
    for field, code in [("udi_di", ""), ("expiry", ""), ("lot", ""), ("serial", ""), ("udi_di", "123"),
                        ("expiry", "31/12/2028"), ("lot", "x" * 21)]:
        with pytest.raises(PayloadUnbuildable) as error:
            build_payload({**OLD, field: code})
        assert error.value.field == field


def test_payload_matches_renderer_when_available() -> None:
    render = pytest.importorskip("src.gen.render")
    record = ProductRecord(product_id="p", name="N", udi_di=NEW_DI,
                           extra={"expiry": "2028-12-31", "lot": "LOT001", "serial": "SN001"})
    _, ais = render.record_content(record, test_data=False)
    from src.change.barcode import build_ais

    assert build_ais({**OLD, "udi_di": NEW_DI}) == ais


def decide(confirmed: bool = False, symbology: str = "GS1_DataMatrix", invalid=(), **changes: str):
    edited = list(changes)
    return decide_barcode(OLD, {**OLD, **changes}, edited, symbology=symbology, confirmed=confirmed,
                          invalid_encoded=invalid)


def test_barcode_keep_when_encoded_fields_untouched() -> None:
    for changes in ({"manufacturer_address": "2 New Road"}, {"sterilization": "Gamma"}, {"storage": "Cool"}):
        outcome = decide(**changes)
        assert outcome.decision == "KEEP" and outcome.old_payload == outcome.new_payload
    assert "placeholder" in decide(storage="Cool").reason


def test_barcode_keep_with_unbuildable_old_record() -> None:
    outcome = decide_barcode({**OLD, "lot": ""}, {**OLD, "lot": "", "storage": "Cool"}, ["storage"],
                             symbology="GS1_DataMatrix", confirmed=False)
    assert outcome.decision == "KEEP" and outcome.old_payload == ""


def test_barcode_unconfirmed_lot_needs_confirmation_and_confirmed_regenerates() -> None:
    outcome = decide(lot="LOT002")
    assert outcome.decision == "NEEDS_INPUT" and outcome.required_identifier == "confirm_lot"
    assert outcome.new_payload.endswith("(10)LOT002(21)SN001")
    done = decide(confirmed=True, lot="LOT002")
    assert done.decision == "REGENERATE" and done.required_identifier is None and "LOT002" in done.new_payload


def test_barcode_expiry_change() -> None:
    assert decide(expiry="2029-12-31").required_identifier == "confirm_expiry"
    assert decide(confirmed=True, expiry="2029-12-31").decision == "REGENERATE"


def test_barcode_new_udi_unconfirmed_and_confirmed() -> None:
    assert decide(udi_di=NEW_DI).required_identifier == "confirm_udi_di"
    assert decide(confirmed=True, udi_di=NEW_DI).decision == "REGENERATE"


def test_barcode_model_change_needs_new_identifier() -> None:
    outcome = decide(confirmed=True, model="TP-2")
    assert outcome.decision == "NEEDS_INPUT" and outcome.required_identifier == "udi_di"
    assert outcome.rule_ids == ("BC-830-50",) and outcome.new_payload == ""
    assert decide(confirmed=True, model="TP-2", udi_di=NEW_DI).decision == "REGENERATE"


def test_barcode_needs_input_when_payload_cannot_be_built() -> None:
    outcome = decide_barcode({**OLD, "lot": ""}, {**OLD, "lot": "", "expiry": "2029-12-31"}, ["expiry"],
                             symbology="GS1_DataMatrix", confirmed=True)
    assert outcome.decision == "NEEDS_INPUT" and outcome.required_identifier == "lot" and outcome.new_payload == ""
    assert decide_barcode({**OLD, "udi_di": ""}, {**OLD, "udi_di": "", "lot": "L2"}, ["lot"],
                          symbology="GS1_DataMatrix", confirmed=True).required_identifier == "udi_di"


def test_barcode_placeholder_never_a_new_value() -> None:
    old = {**OLD, "udi_di": NEW_DI}
    outcome = decide_barcode(old, {**old, "udi_di": "00000000000000"}, ["udi_di"], symbology="GS1_DataMatrix",
                             confirmed=True)
    assert outcome.decision == "NEEDS_INPUT" and outcome.required_identifier == "udi_di"


def test_barcode_invalid_encoded_edit_blocks() -> None:
    outcome = decide(invalid=["udi_di"], storage="Cool")
    assert outcome.decision == "NEEDS_INPUT" and outcome.required_identifier == "udi_di"


def test_barcode_symbology_is_carried() -> None:
    assert decide(symbology="GS1-128", lot="LOT002").symbology == "GS1-128"


# ---------------------------------------------------------------- impact and assessment


class StubRetriever:
    """Returns the chunk ids it was told to return, whatever the query."""

    def __init__(self, ids: list[str]) -> None:
        self.ids = ids

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=i, score=1.0, rank=n) for n, i in enumerate(self.ids, 1)]


CHUNKS = {
    "c801_1": Chunk(chunk_id="c801_1", source="s", section="801.1", title="t",
                    text="The label shall state the name and place of business of the manufacturer."),
    "c801_40": Chunk(chunk_id="c801_40", source="s", section="801.40", title="t",
                     text="The UDI production identifier segment has the lot or batch number and expiration date."),
    "c801_18": Chunk(chunk_id="c801_18", source="s", section="801.18", title="t",
                     text="Dates use the format year, month, day with hyphens."),
    "c830_50": Chunk(chunk_id="c830_50", source="s", section="830.50", title="t",
                     text="Whenever a change results in a new version or model, assign a new device identifier."),
    "c801_20": Chunk(chunk_id="c801_20", source="s", section="801.20", title="t",
                     text="The label of every medical device shall bear a unique device identifier."),
}
FULL = StubRetriever(list(CHUNKS))


def run(changes: dict[str, str], contexts, *, confirmed=False, retriever=FULL, **kw):
    edits, new = edits_of(**changes)
    return assess(edits, new, contexts, confirmed=confirmed, retriever=retriever, chunks=CHUNKS, **kw)


def kinds(result) -> dict[str, list]:
    out: dict[str, list] = {}
    for item in result.items:
        out.setdefault(item.item_kind, []).append(item)
    return out


def test_text_edit_refills_slot_and_keeps_barcode() -> None:
    result = run({"manufacturer_address": "2 New Road"}, [ctx()])
    by = kinds(result)
    text, = by["text"]
    assert text.slot_id == "addr" and text.suggestion == "edit_required" and not text.needs_human
    assert text.evidence_chunk_ids == ["c801_1"] and result.citations[0]["chunk_id"] == "c801_1"
    symbol, = by["symbol"]
    assert symbol.slot_id == "mfr_sym" and symbol.needs_human and symbol.suggestion == "review_suggested"
    barcode, = by["barcode"]
    assert barcode.barcode.decision == "KEEP" and barcode.suggestion == "no_change" and not barcode.needs_human


def test_name_alias_slot_matches() -> None:
    result = run({"name": "Test Pump 2"}, [ctx()])
    text, = kinds(result)["text"]
    assert text.slot_id == "name" and not text.needs_human and not text.evidence_chunk_ids
    assert "none is cited" in text.description


def test_sterilization_text_without_citation_note() -> None:
    result = run({"sterilization": "Gamma irradiation"}, [ctx()])
    text, = kinds(result)["text"]
    assert not text.needs_human and "no sterilization symbol" in text.description
    assert "symbol" not in kinds(result)


def test_lot_change_barcode_item_is_needs_human_until_confirmed() -> None:
    result = run({"lot": "LOT002"}, [ctx()])
    assert "text" not in kinds(result)  # no lot text slot, the barcode covers it
    assert "linked_label" not in kinds(result)
    barcode, = kinds(result)["barcode"]
    assert barcode.barcode.required_identifier == "confirm_lot" and barcode.needs_human
    assert barcode.evidence_chunk_ids == ["c801_40"]
    confirmed, = kinds(run({"lot": "LOT002"}, [ctx()], confirmed=True))["barcode"]
    assert confirmed.barcode.decision == "REGENERATE" and not confirmed.needs_human
    assert confirmed.key == barcode.key


def test_expiry_touches_symbol_and_barcode_with_two_citations() -> None:
    result = run({"expiry": "2029-12-31"}, [ctx()], confirmed=True)
    by = kinds(result)
    assert by["symbol"][0].slot_id == "exp_sym"
    assert set(by["barcode"][0].evidence_chunk_ids) == {"c801_40", "c801_18"}


def test_no_matching_template_field_gives_linked_label_item() -> None:
    result = run({"storage": "Keep cool"}, [ctx()])
    item = next(i for i in result.items if i.item_kind == "linked_label")
    assert item.needs_human and item.rule_ids == ["I-NOSLOT"] and item.slot_id is None
    assert "fixed background" in item.description


def test_label_without_template_one_item_per_edit_and_no_barcode_decision() -> None:
    result = run({"storage": "Keep cool", "lot": "LOT002"}, [ctx(template=False)])
    assert [i.item_kind for i in result.items] == ["linked_label", "linked_label", "linked_label"]
    assert any(i.rule_ids == ["I-NOBARCODE"] for i in result.items)
    assert all(i.needs_human and i.barcode is None for i in result.items)


def test_two_labels_with_different_templates() -> None:
    carton = ctx("lbl_carton")
    pouch = ctx("lbl_pouch", template=[SLOTS[0]])  # only a name slot, no barcode
    result = run({"manufacturer_address": "2 New Road"}, [carton, pouch])
    assert {i.label_id for i in result.items} == {"lbl_carton", "lbl_pouch"}
    pouch_items = [i for i in result.items if i.label_id == "lbl_pouch"]
    assert [i.item_kind for i in pouch_items] == ["linked_label"]
    assert len({i.key for i in result.items}) == len(result.items)


def test_product_without_labels() -> None:
    result = run({"storage": "Cool"}, [])
    assert result.items == [] and "no label registered" in result.needs_human_review


def test_model_change_item_blocks_barcode() -> None:
    result = run({"model": "TP-2"}, [ctx()])
    barcode, = kinds(result)["barcode"]
    assert barcode.barcode.required_identifier == "udi_di" and barcode.evidence_chunk_ids == ["c830_50"]


def test_missing_citation_forces_needs_human() -> None:
    result = run({"manufacturer_address": "2 New Road"}, [ctx()], retriever=StubRetriever(["c801_40"]))
    text, = kinds(result)["text"]
    assert text.needs_human and "No supporting regulation passage" in text.description and not text.evidence_chunk_ids
    assert result.citations == []


def test_no_retriever_or_failing_retriever_never_raises() -> None:
    class Boom:
        def search(self, query: str, k: int = 10):
            raise RuntimeError("index down")

    for retriever in (None, Boom()):
        text, = kinds(run({"manufacturer_address": "x"}, [ctx()], retriever=retriever))["text"]
        assert text.needs_human


def test_unassessed_edits_are_reported_and_block_barcode() -> None:
    from src.change.models import Unassessed

    bad = Unassessed("udi_di", "invalid_value", "A UDI-DI must be exactly 14 digits.")
    result = run({"storage": "Cool"}, [ctx()], unassessed=[bad])
    barcode, = kinds(result)["barcode"]
    assert barcode.barcode.decision == "NEEDS_INPUT" and barcode.barcode.required_identifier == "udi_di"
    assert "Not assessed: udi_di" in result.needs_human_review


def test_printed_barcode_mismatch_needs_human() -> None:
    printed = {"01": "00000000000000", "17": "280331", "10": "LOT001", "21": "SN001"}  # expiry differs
    result = run({"manufacturer_address": "x"}, [ctx(printed_barcode=printed)])
    barcode, = kinds(result)["barcode"]
    assert barcode.needs_human and "printed_barcode_differs_from_record" in barcode.description
    same = {"01": "00000000000000", "17": "281231", "10": "LOT001", "21": "SN001"}
    barcode, = kinds(run({"manufacturer_address": "x"}, [ctx(printed_barcode=same)]))["barcode"]
    assert not barcode.needs_human


def test_only_rule_decided_items_are_not_needs_human() -> None:
    result = run({"manufacturer_address": "x", "lot": "LOT002", "storage": "Cool"}, [ctx()])
    for item in result.items:
        if not item.needs_human:
            assert item.rule_ids[0] in ("I-TEXT", "BC-KEEP", "BC-REGENERATE")
    assert any(i.item_kind in ("symbol", "linked_label") and i.needs_human for i in result.items)


def test_wording_never_claims_compliance() -> None:
    result = run({"manufacturer_address": "x", "lot": "LOT002", "expiry": "2029-12-31", "model": "T2"}, [ctx()])
    text = " ".join([i.description for i in result.items] + [result.needs_human_review or ""]).lower()
    assert "compliant" not in text.replace("not whether the result is compliant", "")
    assert "approved" not in text and "no further action" not in text


def test_item_json_matches_contract_fields() -> None:
    result = run({"lot": "LOT002"}, [ctx()])
    out = item_json(result.items[0], "chg_1", "imp_1")
    assert out["user_decision"] == "pending" and out["barcode_decision"]["decision"] == "NEEDS_INPUT"
    assert out["barcode_decision"]["required_identifier"] == "confirm_lot" and out["item_kind"] == "barcode"
