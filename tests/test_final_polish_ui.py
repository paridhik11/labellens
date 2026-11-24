"""final_polish: static and node checks on the public and professional pages (no browser, no server)."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parents[1] / "ui"
P2 = (UI / "js" / "render-p2.js").read_text(encoding="utf-8")
P3 = (UI / "js" / "render-p3.js").read_text(encoding="utf-8")
SCAN = (UI / "js" / "public-scan.js").read_text(encoding="utf-8")
LIVE = (UI / "js" / "live-dailymed.js").read_text(encoding="utf-8")
PRO = (UI / "pro" / "pro.js").read_text(encoding="utf-8")
node = pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")


def _run(script: str) -> None:
    done = subprocess.run(["node", str(UI / "tools" / script)], capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stdout + done.stderr


@node
def test_name_guess_checks_pass() -> None:
    _run("check_name_guess.cjs")


@node
def test_ask_panel_checks_pass() -> None:
    _run("check_ask_panel.cjs")


def test_no_percent_or_select_on_unsure_candidates() -> None:
    review = P2[P2.index("if (state === 'needs_review')"):P2.index("// 3. Success State")]
    assert "match_confidence * 100" not in review and ">\n                      Select\n" not in review
    assert "This is my pack" in review and "Not certain" in review
    assert ">Select</button>" not in LIVE and "Use this label" in LIVE


def test_authenticity_banner_shown_once_on_public_pages() -> None:
    page = (UI / "public" / "index.html").read_text(encoding="utf-8")
    assert page.count('<div class="notice-title">Authenticity not verified</div>') == 1
    assert "const authenticityBannerHtml = staticBanner ? ''" in P2


def test_label_citations_read_label_section() -> None:
    assert "'Label section: '" in P2 and "21 CFR ${escapeHtml(s.section" not in P2


def test_public_ask_pick_a_medicine_and_ai_wait() -> None:
    assert "Pick a medicine first" in P3 and "No label loaded for this name" not in P3
    assert "autoSearch" in P3 and "autoSearch" in LIVE
    assert "Model is loading, first run can take about a minute." in P3


def test_photo_lookup_never_auto_confirms() -> None:
    propose = SCAN[SCAN.index("function proposeLive"):SCAN.index("function lookupFromPhoto")]
    assert "Is this" in propose and 'data-testid="live-confirm"' in propose and 'data-testid="live-reject"' in propose
    assert "We couldn't identify this pack" in propose
    # fetching happens only in the Confirm click handler
    assert propose.count("fetchCandidate(") == 1 and "live-confirm\"]').addEventListener('click'" in propose


def test_pro_finding_cards_replace_field_buttons() -> None:
    assert "Evidence for this field" not in PRO and "'field-evidence'" not in PRO
    assert "findingCardsHtml(v, false)" in PRO and "findingCardsHtml(v, true)" in PRO
    assert "'download-report'" in PRO and "function findingsReport" in PRO
    assert re.search(r"raw retrieval, unfiltered", PRO)
    assert "A.ask(q, productId())" in PRO


def test_no_em_dash_in_changed_ui_files() -> None:
    for text in (P2, P3, SCAN, LIVE, PRO):
        assert "—" not in text
