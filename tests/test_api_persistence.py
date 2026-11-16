"""Step 20a: persistence layer, append-only triggers, derived status and review rules."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import DBAPIError

from src.api import models
from src.api.db import init_db, make_engine, make_session_factory
from src.api.errors import ApiError
from src.api.models import AuditEvent, ProductVersion, PublishedPage, Review
from src.api.reviews import record_review
from src.api.seed import (
    CHANGE_ID,
    L3_SHA256,
    LABEL_ID,
    PRODUCT_ID,
    TEMPLATE_ID,
    seed_demo,
)
from src.api.status import (
    change_latest_review_id,
    change_status,
    draft_watermark,
    is_closed,
    label_version_status,
)
from src.api.store import (
    add_check_result,
    add_label_version,
    add_product_version,
    create_change,
    register_template,
)

EDITOR, REVIEWER, ADMIN = "usr_demo_editor", "usr_demo_reviewer", "usr_demo_admin"
L1, L2, L3 = "lbv_exampledevice_carton_l1", "lbv_exampledevice_carton_l2", "lbv_exampledevice_carton_l3"


@pytest.fixture()
def session():
    """A fresh in-memory database with the demo seed."""
    engine = make_engine("sqlite://")
    init_db(engine)
    with make_session_factory(engine)() as s:
        seed_demo(s)
        yield s


def code_of(excinfo: pytest.ExceptionInfo[ApiError]) -> tuple[int, str]:
    """Return (status, code) of a raised ApiError."""
    return excinfo.value.status, excinfo.value.code


def approve_l3(session, user_id=REVIEWER, **overrides):
    """Approve L3 as `user_id` (default: the reviewer) with the seeded passed check; `overrides` change any argument."""
    args = {"version_id": L3, "decision": "approve", "artifact_sha256": L3_SHA256, "check_id": "chk_0003"}
    args.update(overrides)
    return record_review(session, user_id, **args)


# ---------------------------------------------------------------- seed


def test_seed_is_idempotent_and_has_expected_state(session):
    assert seed_demo(session) is False
    assert label_version_status(session, L1) == "draft"
    assert label_version_status(session, L2) == "checked"
    assert label_version_status(session, L3) == "checked"
    assert change_status(session, CHANGE_ID) == "checked"
    assert change_latest_review_id(session, CHANGE_ID) is None
    assert draft_watermark(session, L3) is True


# ---------------------------------------------------------------- append-only


def test_every_immutable_table_rejects_update_and_delete(session):
    approve_l3(session)
    session.add(
        PublishedPage(
            page_id="pub_1",
            label_id=LABEL_ID,
            version_id=L3,
            review_id=session.scalars(select(Review)).first().review_id,
            url="/p/pub_1",
            qr_payload="x",
            published_at="2026-11-12T16:00:00Z",
        )
    )
    session.add(models.Extraction(
        extraction_id="ext_1", version_id=L3, label_id=LABEL_ID, mode="stub", payload={},
        created_at="2026-11-12T16:00:00Z",
    ))
    session.add(models.Job(
        job_id="job_00000001", kind="inspect", state="queued", created_by="usr_demo_editor",
        created_at="2026-11-12T16:00:00Z",
    ))
    session.add(models.AskResult(job_id="job_00000002", payload={"answer": {}, "model": "m", "model_used": False},
                                 created_at="2026-11-12T16:00:00Z"))
    session.add(models.ChangeAssessment(
        assessment_id="asm_00000001", change_id=CHANGE_ID, confirmed=False, payload={"parser": "rules", "items": []},
        created_by="usr_demo_editor", created_at="2026-11-12T16:00:00Z",
    ))
    session.add(models.ChangeConfirmation(
        confirmation_id="cfm_00000001", change_id=CHANGE_ID, assessment_id="asm_00000001", decisions=[],
        created_by="usr_demo_editor", created_at="2026-11-12T16:00:00Z",
    ))
    session.commit()
    for table in models.IMMUTABLE_TABLES:
        first_col = inspect(session.get_bind()).get_columns(table)[0]["name"]
        assert session.execute(text(f"SELECT count(*) FROM {table}")).scalar() > 0, table
        with pytest.raises(DBAPIError, match="append-only"):
            session.execute(text(f"UPDATE {table} SET {first_col} = {first_col}"))
        session.rollback()
        with pytest.raises(DBAPIError, match="append-only"):
            session.execute(text(f"DELETE FROM {table}"))
        session.rollback()


def test_editing_an_orm_object_is_rejected_by_the_database(session):
    version = session.scalars(select(ProductVersion).where(ProductVersion.version == 1)).one()
    version.name = "Renamed"
    with pytest.raises(DBAPIError, match="append-only"):
        session.commit()
    session.rollback()
    assert session.scalars(select(ProductVersion).where(ProductVersion.version == 1)).one().name == "ExampleDevice"


def test_product_edit_appends_a_version_and_leaves_the_old_one(session):
    v3 = add_product_version(
        session, EDITOR, PRODUCT_ID, {"sterilization": "Gamma irradiation"}, source_change_id=CHANGE_ID
    )
    rows = session.scalars(select(ProductVersion).where(ProductVersion.product_id == PRODUCT_ID)).all()
    assert sorted(r.version for r in rows) == [1, 2, 3]
    assert v3.supersedes_version == 2 and v3.source_change_id == CHANGE_ID
    assert v3.storage == "Store dry, 5 to 25 C"  # carried over from v2
    assert {r.version: r.sterilization for r in rows} == {
        1: "Ethylene oxide (EO)",
        2: "Ethylene oxide (EO)",
        3: "Gamma irradiation",
    }


def test_template_versions_count_per_template_inside_one_product(session):
    slots = [{"id": "name", "type": "text", "field": "name", "bbox_mm": [5, 10, 50, 6], "size_pt": 10}]
    size = {"w": 100, "h": 60}
    t2 = register_template(session, ADMIN, PRODUCT_ID, size, slots, template_id=TEMPLATE_ID)
    assert (t2.template_id, t2.version) == (TEMPLATE_ID, 2)
    other = register_template(session, ADMIN, PRODUCT_ID, size, slots)  # new template_id
    assert other.version == 1 and other.template_id != TEMPLATE_ID
    again = register_template(session, ADMIN, PRODUCT_ID, size, slots, template_id=other.template_id)
    assert again.version == 2


def test_template_id_cannot_move_to_another_product(session):
    from src.api.store import create_product

    create_product(session, EDITOR, {"name": "Other"}, product_id="prd_other")
    with pytest.raises(ApiError) as e:
        register_template(session, ADMIN, "prd_other", {"w": 50, "h": 30}, [], template_id=TEMPLATE_ID)
    assert code_of(e) == (409, "template_product_mismatch")


def test_label_versions_are_gapless_and_record_their_inputs(session):
    l4 = add_label_version(
        session,
        EDITOR,
        PRODUCT_ID,
        "files/l4.svg",
        label_id=LABEL_ID,
        kind="generated",
        artifact_sha256="a" * 64,
        template_id=TEMPLATE_ID,
        change_id=CHANGE_ID,
    )
    assert l4.artwork_version == 4 and l4.parent_version_id == L3
    assert (l4.product_version, l4.template_version) == (2, 1)
    new_family = add_label_version(session, EDITOR, PRODUCT_ID, "files/x.svg")
    assert new_family.artwork_version == 1 and new_family.label_id != LABEL_ID


def test_generated_artwork_needs_a_hash(session):
    with pytest.raises(ApiError) as e:
        add_label_version(session, EDITOR, PRODUCT_ID, "files/x.svg", kind="generated")
    assert code_of(e) == (422, "artifact_hash_required")


# ---------------------------------------------------------------- derived status


def test_status_table_rows(session):
    failed = add_check_result(
        session,
        "self_check",
        [{"flag_id": "f", "kind": "clipping", "severity": "critical", "message": "m"}],
        version_id=L1,
        artifact_sha256="b" * 64,
    )
    assert failed.passed is False and failed.critical_count == 1
    assert label_version_status(session, L1) == "draft"  # latest check failed
    add_check_result(session, "inspection", [], version_id=L1)
    assert label_version_status(session, L1) == "checked"  # latest check passed, no review
    assert label_version_status(session, L3) == "checked"


def test_approve_makes_it_reviewed_and_removes_the_watermark(session):
    review = approve_l3(session)
    assert review.reviewer_role == "reviewer" and review.check_id == "chk_0003"
    assert label_version_status(session, L3) == "reviewed"
    assert change_status(session, CHANGE_ID) == "reviewed"
    assert change_latest_review_id(session, CHANGE_ID) == review.review_id
    assert draft_watermark(session, L3) is False


def test_return_shows_draft_and_is_not_terminal(session):
    review = record_review(session, REVIEWER, L3, "return", L3_SHA256, comment="Fix the symbol.")
    assert change_status(session, CHANGE_ID) == "draft"
    assert change_latest_review_id(session, CHANGE_ID) == review.review_id
    assert is_closed(session, CHANGE_ID) is False
    # the editor can regenerate and the new version is reviewable
    l4 = add_label_version(
        session,
        EDITOR,
        PRODUCT_ID,
        "files/l4.svg",
        label_id=LABEL_ID,
        kind="generated",
        artifact_sha256="c" * 64,
        change_id=CHANGE_ID,
    )
    assert change_status(session, CHANGE_ID) == "draft"  # new version: no review, no passed check yet
    add_check_result(session, "self_check", [], version_id=l4.version_id, artifact_sha256="c" * 64, check_id="chk_l4")
    assert change_status(session, CHANGE_ID) == "checked"


def test_a_published_page_makes_the_version_published(session):
    review = approve_l3(session)
    session.add(
        PublishedPage(
            page_id="pub_1",
            label_id=LABEL_ID,
            version_id=L3,
            review_id=review.review_id,
            url="/p/pub_1",
            qr_payload="x",
            published_at="2026-11-12T16:00:00Z",
        )
    )
    session.commit()
    assert label_version_status(session, L3) == "published"
    assert change_status(session, CHANGE_ID) == "published"


def test_new_version_after_approval_voids_the_approval(session):
    approve_l3(session)
    assert change_status(session, CHANGE_ID) == "reviewed"
    l4 = add_label_version(
        session,
        EDITOR,
        PRODUCT_ID,
        "files/l4.svg",
        label_id=LABEL_ID,
        kind="generated",
        artifact_sha256="d" * 64,
        change_id=CHANGE_ID,
    )
    assert change_status(session, CHANGE_ID) == "draft"  # approval of L3 no longer counts
    assert label_version_status(session, L3) == "reviewed"  # the old version stays readable as approved
    with pytest.raises(ApiError) as e:
        approve_l3(session, user_id=ADMIN)
    assert code_of(e) == (409, "version_superseded")
    add_check_result(session, "self_check", [], version_id=l4.version_id, artifact_sha256="d" * 64, check_id="chk_l4")
    assert change_status(session, CHANGE_ID) == "checked"


# ---------------------------------------------------------------- review rules


def test_only_reviewer_or_admin_may_review(session):
    with pytest.raises(ApiError) as e:
        approve_l3(session, user_id=EDITOR)
    assert code_of(e) == (403, "role_forbidden")
    assert approve_l3(session, user_id=ADMIN).reviewer_role == "admin"


def test_unknown_user_and_unknown_version(session):
    with pytest.raises(ApiError) as e:
        approve_l3(session, user_id="usr_nobody")
    assert code_of(e) == (401, "unknown_user")
    with pytest.raises(ApiError) as e:
        record_review(session, REVIEWER, "lbv_missing", "return", "x", comment="c")
    assert code_of(e) == (404, "not_found")


def test_submitter_cannot_approve_but_can_return_or_reject(session):
    change = create_change(session, ADMIN, PRODUCT_ID, "storage", "Store cool", "Store dry", change_id="chg_admin")
    version = add_label_version(
        session,
        EDITOR,
        PRODUCT_ID,
        "files/a.svg",
        kind="generated",
        artifact_sha256="e" * 64,
        change_id=change.change_id,
    )
    check = add_check_result(session, "self_check", [], version_id=version.version_id, artifact_sha256="e" * 64)
    with pytest.raises(ApiError) as e:
        record_review(session, ADMIN, version.version_id, "approve", "e" * 64, check_id=check.check_id)
    assert code_of(e) == (403, "self_approval_forbidden")
    assert (
        record_review(session, ADMIN, version.version_id, "return", "e" * 64, comment="self return").decision
        == "return"
    )
    assert record_review(session, REVIEWER, version.version_id, "approve", "e" * 64, check_id=check.check_id)


def test_approve_needs_a_matching_hash_and_a_passed_check(session):
    with pytest.raises(ApiError) as e:
        approve_l3(session, check_id=None)
    assert code_of(e) == (422, "check_required")
    with pytest.raises(ApiError) as e:
        approve_l3(session, artifact_sha256="0" * 64)
    assert code_of(e) == (409, "hash_mismatch")
    with pytest.raises(ApiError) as e:
        approve_l3(session, check_id="chk_missing")
    assert code_of(e) == (409, "check_not_passed")
    # a passed check of another version
    with pytest.raises(ApiError) as e:
        approve_l3(session, check_id="chk_0001")
    assert code_of(e) == (409, "check_not_passed")
    # a failed check of this version and hash
    add_check_result(
        session,
        "self_check",
        [{"flag_id": "f", "kind": "overlap", "severity": "critical", "message": "m"}],
        version_id=L3,
        artifact_sha256=L3_SHA256,
        check_id="chk_bad",
    )
    with pytest.raises(ApiError) as e:
        approve_l3(session, check_id="chk_bad")
    assert code_of(e) == (409, "check_not_passed")
    # a passed check of this version but for a different artifact hash
    add_check_result(session, "self_check", [], version_id=L3, artifact_sha256="f" * 64, check_id="chk_otherhash")
    with pytest.raises(ApiError) as e:
        approve_l3(session, check_id="chk_otherhash")
    assert code_of(e) == (409, "check_not_passed")
    assert session.scalars(select(Review)).first() is None  # nothing was written by the failures


def test_return_and_reject_need_a_comment(session):
    for decision in ("return", "reject"):
        with pytest.raises(ApiError) as e:
            record_review(session, REVIEWER, L3, decision, L3_SHA256, comment="  ")
        assert code_of(e) == (422, "comment_required")
    with pytest.raises(ApiError) as e:
        record_review(session, REVIEWER, L3, "maybe", L3_SHA256)
    assert code_of(e) == (422, "validation_error")


def test_reject_is_terminal(session):
    record_review(session, REVIEWER, L3, "reject", L3_SHA256, comment="Wrong approach.")
    assert is_closed(session, CHANGE_ID) is True
    assert change_status(session, CHANGE_ID) == "draft"
    for decision in ("approve", "return", "reject"):
        with pytest.raises(ApiError) as e:
            record_review(session, ADMIN, L3, decision, L3_SHA256, comment="again", check_id="chk_0003")
        assert code_of(e) == (409, "change_closed")


def test_reviews_write_audit_events_and_are_append_only(session):
    before = len(session.scalars(select(AuditEvent)).all())
    review = record_review(session, REVIEWER, L3, "return", L3_SHA256, comment="Fix it.")
    events = session.scalars(select(AuditEvent).order_by(AuditEvent.seq)).all()
    assert len(events) == before + 1
    last = events[-1]
    assert (last.action, last.user_id, last.entity_id) == ("review.returned", REVIEWER, L3)
    assert last.details["review_id"] == review.review_id
