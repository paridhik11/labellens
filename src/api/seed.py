"""Seed fake demo data, taken from the mock JSON so the UI sees the same names and ids.

All names are fake and the identifier is the GS1 test placeholder (see src/api/mock/index.json).
The seed leaves one change (chg_0002) at status `checked`: its generated draft L3 has a passed
self-check and no review yet, so a reviewer can approve it. Run it with `python -m src.api.seed`.
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from src.api.db import init_db, make_engine, make_session_factory
from src.api.models import User
from src.api.store import (
    add_check_result,
    add_label_version,
    add_product_version,
    create_change,
    create_product,
    register_template,
)

MOCK = Path(__file__).parent / "mock" / "professional"
USERS = (
    ("usr_demo_editor", "Demo Editor", "editor"),
    ("usr_demo_reviewer", "Demo Reviewer", "reviewer"),
    ("usr_demo_admin", "Demo Admin", "admin"),
)
PRODUCT_ID = "prd_exampledevice"
LABEL_ID = "lbl_exampledevice_carton"
TEMPLATE_ID = "tpl_exampledevice_carton"
CHANGE_ID = "chg_0002"
L3_SHA256 = "23f81fcd260e85a1086f09eaf733427f7cbb09becdf887a081ee857dcad90b74"  # sha256 of a mock tag, not a file


def _mock(relative: str) -> dict:
    """Load one mock JSON file."""
    return json.loads((MOCK / relative).read_text(encoding="utf-8"))


def _assess_and_confirm_demo_change(session: Session, change: dict) -> None:
    """Store the real assessment of the demo change (rules, no retrieval) and its confirmation.

    The demo change is a returned, confirmed one, so a reviewer can approve its draft L3 on the real server.
    No retriever is used at seed time, so the stored items carry no citations (sterilization has no cited
    requirement in the corpus anyway).
    """
    from src.api import changes
    from src.api.models import ChangeRequest
    from src.api.requests import ChangeConfirmCreate, ImpactDecision
    from src.api.store import current_product_version
    from src.change.fields import record_values
    from src.change.models import Edit

    row = session.get(ChangeRequest, CHANGE_ID)
    current = record_values(changes._record(current_product_version(session, PRODUCT_ID)))
    edits = [Edit(change["field"], change["old_value"], change["new_value"])]
    stored = changes.assess_and_store(session, row, edits, current, "rules", [], [], None, {}, 10, "usr_demo_editor")
    decisions = [ImpactDecision(impact_id=i["impact_id"], user_decision="confirmed") for i in stored.payload["items"]]
    changes.confirm_change(
        session, "usr_demo_editor", CHANGE_ID, ChangeConfirmCreate(parse_confirmed=True, decisions=decisions)
    )


def seed_demo(session: Session) -> bool:
    """Insert the demo users and data once. Returns False (and does nothing) if users already exist."""
    if session.query(User).first() is not None:
        return False
    session.add_all(User(user_id=i, name=n, role=r) for i, n, r in USERS)
    session.commit()

    detail = _mock("product_detail/success.json")
    record = detail["record"]
    fields = ("name", "model", "manufacturer", "manufacturer_address", "udi_di", "sterilization", "extra")
    v1 = {f: record[f] for f in fields}
    v1["storage"] = "Store dry"
    create_product(
        session, "usr_demo_editor", v1, detail["product"]["intended_market"], PRODUCT_ID, at="2026-11-01T09:00:00Z"
    )
    add_product_version(
        session, "usr_demo_editor", PRODUCT_ID, {"storage": record["storage"]}, at="2026-11-10T09:00:00Z"
    )

    template = _mock("template_setup/success.json")
    register_template(
        session,
        "usr_demo_admin",
        PRODUCT_ID,
        template["size_mm"],
        template["slots"],
        template["background"],
        template["min_font_pt"],
        TEMPLATE_ID,
        at="2026-11-01T10:00:00Z",
    )

    common = {"label_id": LABEL_ID, "template_id": TEMPLATE_ID, "template_version": 1}
    add_label_version(
        session,
        "usr_demo_editor",
        PRODUCT_ID,
        "files/lbv_exampledevice_carton_l1.svg",
        product_version=1,
        version_id="lbv_exampledevice_carton_l1",
        at="2026-11-02T09:00:00Z",
        **common,
    )
    add_label_version(
        session,
        "usr_demo_editor",
        PRODUCT_ID,
        "files/lbv_exampledevice_carton_l2.svg",
        product_version=2,
        version_id="lbv_exampledevice_carton_l2",
        at="2026-11-03T09:00:00Z",
        **common,
    )
    inspect = _mock("inspect/success.json")
    add_check_result(
        session,
        "inspection",
        inspect["findings"],
        version_id="lbv_exampledevice_carton_l2",
        check_id="chk_0001",
        at="2026-11-10T10:00:00Z",
        coverage=inspect["coverage"],
    )

    change = _mock("changes/change_returned.json")
    create_change(
        session,
        "usr_demo_editor",
        PRODUCT_ID,
        change["field"],
        change["new_value"],
        change["old_value"],
        change["raw_text"],
        "confirmed",
        CHANGE_ID,
        at=change["created_at"],
    )
    _assess_and_confirm_demo_change(session, change)
    add_label_version(
        session,
        "usr_demo_editor",
        PRODUCT_ID,
        "files/lbv_exampledevice_carton_l3.svg",
        kind="generated",
        product_version=2,
        pdf_file="files/lbv_exampledevice_carton_l3.pdf",
        change_id=CHANGE_ID,
        artifact_sha256=L3_SHA256,
        version_id="lbv_exampledevice_carton_l3",
        at="2026-11-11T09:00:00Z",
        **common,
    )
    add_check_result(
        session,
        "self_check",
        [],
        version_id="lbv_exampledevice_carton_l3",
        artifact_sha256=L3_SHA256,
        check_id="chk_0003",
        at="2026-11-11T09:05:00Z",
        coverage=_mock("review/recheck_success.json")["coverage"],
    )
    return True


def main() -> None:
    """Create the tables in the configured database and seed it."""
    engine = make_engine()
    init_db(engine)
    with make_session_factory(engine)() as session:
        print("seeded" if seed_demo(session) else "already seeded, nothing changed")


if __name__ == "__main__":
    main()
