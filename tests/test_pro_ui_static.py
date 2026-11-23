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


ROOT = Path(__file__).resolve().parents[1]


def test_lab_evaluation_numbers_match_the_results_file() -> None:
    """Every number in the Retrieval lab table is in results/step18_final.md (no number is typed from memory)."""
    final = (ROOT / "results" / "step18_final.md").read_text(encoding="utf-8")
    block = re.search(r"const LAB_EVAL = \[(.*?)\];", JS, re.S)
    assert block, "LAB_EVAL not found"
    rows = re.findall(r"\['([^']+)', '([0-9.]+)', '([0-9.]+)'\]", block.group(1))
    assert len(rows) == 3
    for _name, ndcg, recall in rows:
        assert f"| {ndcg} | {recall} |" in final or f"**{ndcg}** | **{recall}**" in final, (ndcg, recall)
    assert "LLM grades" in JS


def test_required_elements_and_lab_systems_exist() -> None:
    """The five required elements and the five lab systems are all there, and every system is a real search method."""
    required = JS[JS.index("const REQUIRED = ["):JS.index("const REQ_WORD")]
    for key in ("manufacturer", "udi", "lot", "expiry", "barcode"):
        assert f"['{key}'," in required
    systems = re.findall(r"\['(bm25|tfidf|dense|hybrid_rrf|e5b)', '", JS)
    assert sorted(systems) == ["bm25", "dense", "e5b", "hybrid_rrf", "tfidf"]


def test_new_page_files_are_wired_and_have_no_em_dash() -> None:
    """index.html loads readhints.js before pro.js, and the new file has no em dash."""
    html = (ROOT / "ui" / "pro" / "index.html").read_text(encoding="utf-8")
    assert html.index("readhints.js") < html.index("pro.js")
    assert "—" not in (ROOT / "ui" / "pro" / "readhints.js").read_text(encoding="utf-8")
    assert "—" not in (ROOT / "ui" / "pro" / "pro-api.js").read_text(encoding="utf-8")
