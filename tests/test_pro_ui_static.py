"""Static checks on ui/pro/pro.js: the per-field Evidence tables cover every record field and name real rules.

The page itself is exercised by ui/tools/pro_e2e.cjs against a running server; these checks need no server.
"""
from __future__ import annotations

import re
from pathlib import Path

from src.checker.citations import CITATION_SPECS, NO_CITATION_RULES

JS = (Path(__file__).resolve().parents[1] / "ui" / "pro" / "pro.js").read_text(encoding="utf-8")
FIELDS = ("name", "model", "manufacturer", "manufacturer_address", "udi_di", "sterilization", "storage", "lot",
          "expiry", "serial")


def _block(name: str) -> str:
    match = re.search(rf"const {name} = \{{(.*?)\n  \}};", JS, re.S)
    assert match, f"{name} not found in pro.js"
    return match.group(1)


def test_every_record_field_has_a_question_and_a_rule_list() -> None:
    """Each of the ten fields has one fixed regulation question and an entry in the rule map."""
    questions, rules = _block("FIELD_QUESTION"), _block("FIELD_RULES")
    for field in FIELDS:
        assert re.search(rf"\b{field}: '", questions), f"no question for {field}"
        assert re.search(rf"\b{field}: \[", rules), f"no rule list for {field}"


def test_rule_ids_in_the_field_map_exist_in_the_checker() -> None:
    """The rule ids the page looks up in the check result are real checker rules."""
    known = set(CITATION_SPECS) | set(NO_CITATION_RULES) | {"R-NAMEPLACE", "D-FMT"}
    used = set(re.findall(r"'([A-Z]-[A-Z0-9]+)'", _block("FIELD_RULES")))
    assert used and used <= known, sorted(used - known)


def test_no_sample_data_or_em_dash_in_the_page_code() -> None:
    """The evidence code has no canned answers, and the file has no em dash."""
    assert "—" not in JS
    assert "sample answer" not in JS.lower()
    assert "/ui/pro/sample/" in JS  # only the Add page loads the sample label file, nothing in Evidence
    evidence = JS[JS.index("function renderEvidence"):JS.index("function renderCheck")]
    assert "sample" not in evidence.lower()


def test_evidence_uses_the_existing_ask_gate_not_a_new_threshold() -> None:
    """The page sends the question to askProfessional (scope rule and score gate) and sets no threshold itself."""
    assert "A.ask(" in JS
    assert "threshold =" not in JS and "THRESHOLD" not in JS
