# ruff: noqa: E501
"""Step 22c: POST /changes assessment, confirmChange and the approval gate, on a synthetic product.

The identifier 12345678901231 is a made-up number with a valid GS1 check digit, not a real GTIN.
"""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from src.api.changes import latest_assessment
from src.api.main import create_app
from src.api.seed import CHANGE_ID, L3_SHA256
from src.api.store import add_check_result, add_label_version, create_change
from src.checker.settings import CheckerSettings, RetrievalSettings
from tests.openapi_helpers import conformance_errors

EDITOR, REVIEWER = "usr_demo_editor", "usr_demo_reviewer"
PRODUCT = {
    "name": "Test Pump", "model": "TP-1", "manufacturer": "Example Medical", "manufacturer_address": "1 Test Road",
    "udi_di": "12345678901231", "sterilization": "EO", "storage": "Store dry",
    "extra": {"lot": "LOT001", "expiry": "2028-12-31", "serial": "SN001"},
}
SLOTS = [
    {"id": "addr", "type": "text", "field": "manufacturer_address", "size_pt": 7, "bbox_mm": [5, 20, 50, 8]},
    {"id": "udi", "type": "barcode", "field": "udi", "symbology": "GS1_DataMatrix", "bbox_mm": [60, 30, 20, 20]},
]


def h(user: str = EDITOR) -> dict[str, str]:
    return {"X-User-Id": user}


@pytest.fixture()
def env():
    """Client, product id and the first label version (template with a text slot and a barcode slot)."""
    with TestClient(create_app("sqlite://", seed=True)) as client:
        client.app.state.checker_settings = CheckerSettings(retrieval=RetrievalSettings(method="bm25"))
        product = client.post("/products", headers=h(), json=PRODUCT).json()["product"]["product_id"]
        tpl = client.post(f"/products/{product}/templates", headers=h(), json={
            "size_mm": {"w": 100, "h": 60}, "background": None, "slots": SLOTS}).json()["template_id"]
        with client.app.state.session_factory() as session:
            label = add_label_version(session, EDITOR, product, "files/x.svg", template_id=tpl, template_version=1)
        yield client, product, label


def post(client, product, **body):
    return client.post("/changes", headers=h(), json={"product_id": product, **body})


def barcode_item(assessment: dict) -> dict:
    return next(i for i in assessment["affected"] if i["item_kind"] == "barcode")


def test_lot_change_assessment_and_confirmation(env) -> None:
    client, product, label = env
    response = post(client, product, edits=[{"field": "lot", "new_value": "LOT002"}])
    assert response.status_code == 201
    body = response.json()
    assert not conformance_errors("assessChange", 201, body)
    assert body["parser"] == "rules" and body["checklist_complete"] is False and body["change"]["parse_state"] == "proposed"
    item = barcode_item(body)
    assert item["label_id"] == label.label_id and item["version_id"] == label.version_id
    assert item["barcode_decision"]["decision"] == "NEEDS_INPUT"
    assert item["barcode_decision"]["required_identifier"] == "confirm_lot" and item["needs_human"] is True
    assert "NEEDS_HUMAN_REVIEW" in body["needs_human_review"]
    chunk_ids = {c["chunk_id"] for c in body["citations"]}
    assert set(item["evidence_chunk_ids"]) <= chunk_ids
    change_id = body["change"]["change_id"]

    affected = client.get(f"/changes/{change_id}/affected", headers=h()).json()
    assert not conformance_errors("listAffectedLabels", 200, affected)
    assert affected["items"][0]["impact_id"] == item["impact_id"]

    confirm = client.post(f"/changes/{change_id}/confirm", headers=h(), json={
        "parse_confirmed": True, "decisions": [{"impact_id": item["impact_id"], "user_decision": "confirmed"}]})
    assert confirm.status_code == 200
    done = confirm.json()
    assert not conformance_errors("confirmChange", 200, done)
    assert done["change"]["parse_state"] == "confirmed" and done["checklist_complete"] is True
    assert done["assessment_id"] != body["assessment_id"]
    after = barcode_item(done)
    assert after["impact_id"] == item["impact_id"] and after["user_decision"] == "confirmed"
    assert after["barcode_decision"]["decision"] == "REGENERATE" and "required_identifier" not in after["barcode_decision"]
    assert after["barcode_decision"]["new_payload"] == "(01)12345678901231(17)281231(10)LOT002(21)SN001"
    # a second confirmation appends a row but not another assessment
    again = client.post(f"/changes/{change_id}/confirm", headers=h(), json={
        "parse_confirmed": True, "decisions": [{"impact_id": item["impact_id"], "user_decision": "dismissed"}]}).json()
    assert again["assessment_id"] == done["assessment_id"] and barcode_item(again)["user_decision"] == "dismissed"


def test_text_edit_item_is_rule_decided_and_barcode_kept(env) -> None:
    client, product, _ = env
    body = post(client, product, edits=[{"field": "manufacturer address", "new_value": "2 New Road"}]).json()
    text_item = next(i for i in body["affected"] if i["item_kind"] == "text")
    assert text_item["slot_id"] == "addr" and text_item["suggestion"] == "edit_required" and text_item["rule_ids"] == ["I-TEXT"]
    assert barcode_item(body)["barcode_decision"]["decision"] == "KEEP"
    assert body["change"]["field"] == "manufacturer_address"


def test_plain_text_is_parsed_by_the_rules(env) -> None:
    client, product, _ = env
    body = post(client, product, raw_text="Change the expiry to 30 April 2029").json()
    assert body["parser"] == "rules" and body["change"]["field"] == "expiry"
    assert body["change"]["new_value"] == "2029-04-30" and body["change"]["raw_text"].startswith("Change the expiry")


def test_unparseable_text_is_422_parser_not_implemented(env) -> None:
    client, product, _ = env
    for text_in in ("Switch to gamma", "change the model and lot to X", ""):
        response = post(client, product, raw_text=text_in)
        assert response.status_code == 422, text_in
        assert response.json()["error"] == "parser_not_implemented"
    detail = post(client, product, raw_text="Switch to gamma").json()["details"]
    assert detail["status"] == "unknown" and detail["issues"]
    assert not conformance_errors("assessChange", 422, post(client, product, raw_text="x1").json())


def test_no_change_and_duplicate_are_refused(env) -> None:
    client, product, _ = env
    same = post(client, product, edits=[{"field": "udi_di", "old_value": PRODUCT["udi_di"], "new_value": PRODUCT["udi_di"]}])
    assert same.status_code == 422 and same.json()["error"] == "no_change" and "nothing to change" in same.json()["message"]
    twice = post(client, product, edits=[{"field": "lot", "new_value": "A"}, {"field": "batch", "new_value": "B"}])
    assert twice.status_code == 422 and twice.json()["error"] == "duplicate_field"


def test_unknown_field_only_keeps_not_implemented(env) -> None:
    client, product, _ = env
    body = post(client, product, edits=[{"field": "colour", "new_value": "red"}]).json()
    assert not conformance_errors("assessChange", 201, body)
    assert body["parser"] == "not_implemented" and body["affected"] == [] and body["checklist_complete"] is False
    assert body["unassessed_edits"][0]["reason"] == "unknown_field" and "not because nothing is affected" in body["needs_human_review"]
    change_id = body["change"]["change_id"]
    assert client.get(f"/changes/{change_id}/affected", headers=h()).json()["items"] == []
    nothing = client.post(f"/changes/{change_id}/confirm", headers=h(), json={"parse_confirmed": True, "decisions": []})
    assert nothing.status_code == 409 and nothing.json()["error"] == "nothing_to_confirm"


def test_mixed_valid_and_unknown_edits(env) -> None:
    client, product, _ = env
    body = post(client, product, edits=[{"field": "lot", "new_value": "LOT009"}, {"field": "colour", "new_value": "red"}]).json()
    assert body["parser"] == "rules" and [u["field"] for u in body["unassessed_edits"]] == ["colour"]
    assert "Not assessed: colour" in body["needs_human_review"]


def test_invalid_udi_blocks_barcode(env) -> None:
    client, product, _ = env
    body = post(client, product, edits=[{"field": "manufacturer_address", "new_value": "3 Road"},
                                        {"field": "udi_di", "new_value": "123"}]).json()
    decision = barcode_item(body)["barcode_decision"]
    assert decision["decision"] == "NEEDS_INPUT" and decision["required_identifier"] == "udi_di"
    assert body["unassessed_edits"][0]["reason"] == "invalid_value"


def test_confirm_rules(env) -> None:
    client, product, _ = env
    body = post(client, product, edits=[{"field": "lot", "new_value": "LOT002"}]).json()
    url = f"/changes/{body['change']['change_id']}/confirm"
    impact = barcode_item(body)["impact_id"]
    ok = [{"impact_id": impact, "user_decision": "confirmed"}]
    cases = [
        (h(), {"parse_confirmed": False, "decisions": ok}, 422, "parse_not_confirmed"),
        (h(), {"parse_confirmed": True, "edits": [{"field": "lot", "new_value": "Z"}], "decisions": ok}, 422,
         "edits_not_supported"),
        (h(), {"parse_confirmed": True, "decisions": [{"impact_id": "imp_nope", "user_decision": "confirmed"}]}, 422,
         "unknown_impact"),
        (h(REVIEWER), {"parse_confirmed": True, "decisions": ok}, 403, "role_forbidden"),
        (None, {"parse_confirmed": True, "decisions": ok}, 401, "unknown_user"),
    ]
    for headers, payload, status, code in cases:
        response = client.post(url, headers=headers or {}, json=payload)
        assert response.status_code == status and response.json()["error"] == code, (code, response.text)
    assert client.post("/changes/chg_missing/confirm", headers=h(), json={"parse_confirmed": True, "decisions": []}
                       ).status_code == 404
    still = client.get(url.replace("/confirm", ""), headers=h()).json()
    assert still["parse_state"] == "proposed"  # none of the refusals appended a confirmation


def test_approval_needs_a_confirmed_assessment_and_points_at_it(env) -> None:
    client, product, label = env
    body = post(client, product, edits=[{"field": "manufacturer_address", "new_value": "2 New Road"}]).json()
    change_id = body["change"]["change_id"]
    sha = "c" * 64
    with client.app.state.session_factory() as session:
        draft = add_label_version(session, EDITOR, product, "files/g.svg", kind="generated", label_id=label.label_id,
                                  artifact_sha256=sha, change_id=change_id, template_id=label.template_id,
                                  template_version=1)
        check = add_check_result(session, "self_check", [], version_id=draft.version_id, artifact_sha256=sha)
    approve = {"decision": "approve", "artifact_sha256": sha, "check_id": check.check_id}
    url = f"/label-versions/{draft.version_id}/reviews"
    early = client.post(url, headers=h(REVIEWER), json=approve)
    assert early.status_code == 409 and early.json()["error"] == "change_not_confirmed"
    items = [{"impact_id": i["impact_id"], "user_decision": "confirmed"} for i in body["affected"]]
    confirmed = client.post(f"/changes/{change_id}/confirm", headers=h(), json={"parse_confirmed": True, "decisions": items})
    approved = client.post(url, headers=h(REVIEWER), json=approve)
    assert approved.status_code == 201, approved.text
    assert not conformance_errors("reviewArtwork", 201, approved.json())
    assert approved.json()["assessment_id"] == confirmed.json()["assessment_id"]


def test_return_records_assessment_without_confirmation(env) -> None:
    client, product, label = env
    body = post(client, product, edits=[{"field": "storage", "new_value": "Keep cool"}]).json()
    sha = "d" * 64
    with client.app.state.session_factory() as session:
        draft = add_label_version(session, EDITOR, product, "files/g2.svg", kind="generated", label_id=label.label_id,
                                  artifact_sha256=sha, change_id=body["change"]["change_id"])
    returned = client.post(f"/label-versions/{draft.version_id}/reviews", headers=h(REVIEWER),
                           json={"decision": "return", "artifact_sha256": sha, "comment": "Fix."})
    assert returned.status_code == 201 and returned.json()["assessment_id"] == body["assessment_id"]


def test_assessment_tables_are_append_only(env) -> None:
    client, product, _ = env
    post(client, product, edits=[{"field": "lot", "new_value": "LOT002"}])
    with client.app.state.engine.begin() as conn, pytest.raises((DatabaseError, sqlite3.DatabaseError)):
        conn.execute(text("UPDATE change_assessments SET confirmed = 1"))
    with client.app.state.engine.begin() as conn, pytest.raises((DatabaseError, sqlite3.DatabaseError)):
        conn.execute(text("DELETE FROM change_assessments"))


class Provider:
    def propose_edits(self, raw_text: str, fields: tuple[str, ...]) -> list[dict[str, str]]:
        return [{"field": "batch", "new_value": "ABC123"}]


def test_llm_provider_is_off_by_default_and_marks_parser_llm(env) -> None:
    client, product, _ = env
    sentence = "please make the batch code ABC123 from now on"
    assert post(client, product, raw_text=sentence).status_code == 422
    client.app.state.edit_provider = Provider()
    body = post(client, product, raw_text=sentence).json()
    assert body["parser"] == "llm" and body["change"]["field"] == "lot" and body["change"]["parse_state"] == "proposed"


def test_changes_without_a_stored_assessment_keep_the_mock(env) -> None:
    client, product, _ = env
    with client.app.state.session_factory() as session:  # a change made before Step 22 has no assessment
        old = create_change(session, EDITOR, product, "storage", "Keep cool", "Store dry")
    affected = client.get(f"/changes/{old.change_id}/affected", headers=h())
    assert affected.status_code == 200 and affected.headers["X-Mock"] == "true"
    confirm = client.post(f"/changes/{old.change_id}/confirm", headers=h(), json={"parse_confirmed": True, "decisions": []})
    assert confirm.status_code == 200 and confirm.headers["X-Mock"] == "true"
    assert client.get("/changes/chg_missing/affected", headers=h()).status_code == 404


def test_product_without_labels_says_so() -> None:
    with TestClient(create_app("sqlite://", seed=True)) as client:
        client.app.state.checker_settings = CheckerSettings(retrieval=RetrievalSettings(method="bm25"))
        product = client.post("/products", headers=h(), json=PRODUCT).json()["product"]["product_id"]
        body = post(client, product, edits=[{"field": "lot", "new_value": "LOT002"}]).json()
        assert body["affected"] == [] and body["checklist_complete"] is False and "no label registered" in body["needs_human_review"]


def test_seeded_demo_change_can_be_approved_end_to_end() -> None:
    """The seed stores a confirmed assessment for chg_0002, so its draft L3 can be approved on the real server."""
    l3 = "lbv_exampledevice_carton_l3"
    with TestClient(create_app("sqlite://", seed=True)) as client:
        affected = client.get(f"/changes/{CHANGE_ID}/affected", headers=h())
        assert "X-Mock" not in affected.headers and affected.json()["items"]
        assert all(i["user_decision"] == "confirmed" for i in affected.json()["items"])
        change = client.get(f"/changes/{CHANGE_ID}", headers=h()).json()
        assert change["status"] == "checked" and change["parse_state"] == "confirmed"
        body = {"decision": "approve", "artifact_sha256": L3_SHA256, "check_id": "chk_0003"}
        approved = client.post(f"/label-versions/{l3}/reviews", headers=h(REVIEWER), json=body)
        assert approved.status_code == 201, approved.text
        assert not conformance_errors("reviewArtwork", 201, approved.json())
        with client.app.state.session_factory() as session:
            latest = latest_assessment(session, CHANGE_ID)
            assert latest.confirmed and latest.parent_assessment_id is not None
        assert approved.json()["assessment_id"] == latest.assessment_id
        assert client.get(f"/changes/{CHANGE_ID}", headers=h()).json()["status"] == "reviewed"
        listed = client.get(f"/label-versions/{l3}/reviews", headers=h()).json()["items"]
        assert [r["decision"] for r in listed] == ["approve"]
