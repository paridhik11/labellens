"""Contract tests for the Step 19 mock JSON in src/api/mock.

Every mock is validated against the response schema of its endpoint in docs/contracts/openapi.yaml,
and, where a class exists, the mapped part is also validated with the locked models in
src/common/schemas.py. Further checks keep the mocks honest: citations quote real chunks, modules
do not mix, no identifier is invented, and every required screen state is covered.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

import pytest
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from src.common.schemas import ChangeRequest, Flag, Hit, LabelExtraction, ProductRecord

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "docs" / "contracts" / "openapi.yaml"
MOCK_DIR = ROOT / "src" / "api" / "mock"
SCREENS_PATH = ROOT / "docs" / "contracts" / "SCREENS.md"
CORPUS_PATH = ROOT / "data" / "processed" / "regs.jsonl"
GS1_TEST_PLACEHOLDER = "00000000000000"
REQUIRED_STATES = {"empty", "loading", "success", "failed_check", "needs_review", "approved", "abstained"}
ABSTAIN_REASONS = {"no_evidence", "low_confidence", "out_of_scope", "needs_human_check"}
SPEC: dict[str, Any] = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
REGISTRY = Registry().with_resource("urn:oas", Resource.from_contents(SPEC, default_specification=DRAFT202012))
INDEX: dict[str, Any] = json.loads((MOCK_DIR / "index.json").read_text(encoding="utf-8"))
ENTRIES: list[dict[str, Any]] = INDEX["mocks"]


def load_mock(rel: str) -> Any:
    """Read one mock file by its path relative to src/api/mock."""
    return json.loads((MOCK_DIR / rel).read_text(encoding="utf-8"))


def find_operation(operation_id: str) -> dict[str, Any]:
    """Return the OpenAPI operation object with the given operationId."""
    for item in SPEC["paths"].values():
        for op in item.values():
            if isinstance(op, dict) and op.get("operationId") == operation_id:
                return op
    raise KeyError(operation_id)


def response_schema(operation_id: str, status: int) -> dict[str, Any]:
    """Return the JSON response schema for an operation and status code, following response $refs."""
    response = find_operation(operation_id)["responses"][str(status)]
    if "$ref" in response:
        response = SPEC["components"]["responses"][response["$ref"].split("/")[-1]]
    return response["content"]["application/json"]["schema"]


def validator_for(schema: dict[str, Any]) -> Draft202012Validator:
    """Build a 2020-12 validator whose $refs resolve inside openapi.yaml."""
    rewritten = json.loads(json.dumps(schema).replace('"#/components/', '"urn:oas#/components/'))
    return Draft202012Validator(rewritten, registry=REGISTRY)


def walk(node: Any) -> Iterator[Any]:
    """Yield every dict and list nested anywhere inside a JSON value, including the value itself."""
    yield node
    if isinstance(node, dict):
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def model_subset(model: type, data: dict[str, Any]) -> dict[str, Any]:
    """Keep only the keys a schemas.py model defines, so extended contract fields can be checked by the model."""
    return {k: v for k, v in data.items() if k in model.model_fields}


def load_corpus() -> dict[str, dict[str, Any]]:
    """Load the regulation chunks keyed by chunk_id."""
    chunks = {}
    for line in CORPUS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            chunks[row["chunk_id"]] = row
    return chunks


CORPUS = load_corpus()


# ---------------------------------------------------------------- the spec itself

def test_spec_is_openapi_31_with_valid_component_schemas() -> None:
    assert SPEC["openapi"].startswith("3.1")
    for schema in SPEC["components"]["schemas"].values():
        Draft202012Validator.check_schema(schema)


def test_spec_refs_resolve_and_operation_ids_unique() -> None:
    text = SPEC_PATH.read_text(encoding="utf-8")
    for ref in set(re.findall(r'\$ref: "#/([^"]+)"', text)):
        node: Any = SPEC
        for part in ref.split("/"):
            node = node[part]
    ops = [op["operationId"] for item in SPEC["paths"].values() for op in item.values() if isinstance(op, dict)]
    assert len(ops) == len(set(ops))


def test_spec_examples_validate() -> None:
    count = 0
    for item in SPEC["paths"].values():
        for op in item.values():
            blocks = list(op.get("requestBody", {}).get("content", {}).values())
            for response in op.get("responses", {}).values():
                blocks += list(response.get("content", {}).values())
            for block in blocks:
                for example in block.get("examples", {}).values():
                    errors = list(validator_for(block["schema"]).iter_errors(example["value"]))
                    assert not errors, [e.message for e in errors]
                    count += 1
    assert count >= 6


# ---------------------------------------------------------------- index completeness

def test_index_lists_every_mock_file_and_nothing_else() -> None:
    on_disk = {p.relative_to(MOCK_DIR).as_posix() for p in MOCK_DIR.rglob("*.json")} - {"index.json"}
    listed = [e["file"] for e in ENTRIES]
    assert len(listed) == len(set(listed))
    assert set(listed) == on_disk


def test_screens_doc_lists_the_same_mock_files() -> None:
    doc = SCREENS_PATH.read_text(encoding="utf-8")
    in_doc = set(re.findall(r"`((?:public|professional)/[a-z_/]+\.json)`", doc))
    assert in_doc == {e["file"] for e in ENTRIES}


# ---------------------------------------------------------------- every mock against its endpoint

@pytest.mark.parametrize("entry", ENTRIES, ids=[e["file"] for e in ENTRIES])
def test_mock_matches_endpoint_response_schema(entry: dict[str, Any]) -> None:
    data = load_mock(entry["file"])
    errors = list(validator_for(response_schema(entry["operationId"], entry["status"])).iter_errors(data))
    assert not errors, [f"{list(e.absolute_path)}: {e.message}" for e in errors]
    if not entry["schema"].startswith("inline:"):
        named = {"$ref": f"#/components/schemas/{entry['schema']}"}
        assert not list(validator_for(named).iter_errors(data))


def test_validation_is_not_vacuous() -> None:
    """Broken copies of real mocks must fail, so a passing run means something."""
    returned = load_mock("professional/review/returned.json")
    schema = validator_for(response_schema("reviewArtwork", 201))
    assert list(schema.iter_errors(dict(returned, resulting_status="reviewed")))
    assert list(schema.iter_errors(dict(returned, unexpected_key=1)))
    abstain = load_mock("public/ask/abstained_out_of_scope.json")
    assert list(validator_for(response_schema("askPublic", 200)).iter_errors(dict(abstain, reason="guess")))
    approve = {"decision": "approve", "artifact_sha256": "0" * 64}
    assert list(validator_for({"$ref": "#/components/schemas/ReviewCreate"}).iter_errors(approve))


@pytest.mark.parametrize("entry", [e for e in ENTRIES if e.get("schemas_py")], ids=lambda e: e["file"])
def test_mapped_parts_validate_with_schemas_py(entry: dict[str, Any]) -> None:
    data = load_mock(entry["file"])
    kind = entry["schemas_py"]
    if kind == "LabelExtraction":
        LabelExtraction(**model_subset(LabelExtraction, data))
    elif kind == "Flag":
        assert data["findings"] or data.get("coverage")  # a clean check has no findings but lists its coverage
        for finding in data["findings"]:
            Flag(**model_subset(Flag, finding))
    elif kind == "ChangeRequest":
        ChangeRequest(**model_subset(ChangeRequest, data.get("change", data)))
    elif kind == "Hit":
        assert data["hits"]
        for hit in data["hits"]:
            Hit(**hit)
    else:
        pytest.fail(f"unknown schemas_py mapping {kind}")


def test_every_product_record_validates_with_schemas_py() -> None:
    seen = 0
    for entry in ENTRIES:
        for node in walk(load_mock(entry["file"])):
            if isinstance(node, dict) and "record" in node:
                ProductRecord(**model_subset(ProductRecord, node["record"]))
                seen += 1
    assert seen >= 3


# ---------------------------------------------------------------- honesty checks

def test_citations_quote_real_chunks_of_the_right_module() -> None:
    checked = 0
    for entry in ENTRIES:
        module = "medicine" if entry["file"].startswith("public/") else "device"
        for node in walk(load_mock(entry["file"])):
            if isinstance(node, dict) and node.get("source_type") == "cfr":
                chunk = CORPUS[node["chunk_id"]]
                assert chunk["module"] == module, (entry["file"], node["chunk_id"])
                for key in ("source", "section", "title", "url"):
                    assert node[key] == chunk[key]
                assert node["quote"] and node["quote"] in chunk["text"]
                checked += 1
            if isinstance(node, dict) and "evidence_chunk_ids" in node:
                for chunk_id in node["evidence_chunk_ids"]:
                    assert CORPUS[chunk_id]["module"] == module, (entry["file"], chunk_id)
    assert checked >= 10


def test_no_label_section_citations_while_label_corpus_is_missing() -> None:
    for entry in ENTRIES:
        for node in walk(load_mock(entry["file"])):
            assert not (isinstance(node, dict) and node.get("source_type") == "label_section"), entry["file"]


def test_evidence_hits_are_real_device_chunks() -> None:
    data = load_mock("professional/evidence/success.json")
    for hit in data["hits"]:
        assert CORPUS[hit["doc_id"]]["module"] == "device"
        assert CORPUS[hit["doc_id"]]["text"].startswith(hit["text"])


def test_no_invented_identifiers() -> None:
    for entry in ENTRIES:
        text = (MOCK_DIR / entry["file"]).read_text(encoding="utf-8")
        for node in walk(json.loads(text)):
            if isinstance(node, dict) and "udi_di" in node:
                assert node["udi_di"] in ("", GS1_TEST_PLACEHOLDER), entry["file"]
            if isinstance(node, dict) and isinstance(node.get("parsed"), dict) and "01" in node["parsed"]:
                assert node["parsed"]["01"] == GS1_TEST_PLACEHOLDER, entry["file"]
        for gtin in re.findall(r"\(01\)(\d{14})", text):
            assert gtin == GS1_TEST_PLACEHOLDER, entry["file"]


def test_generated_drafts_are_marked_and_use_test_data_with_the_placeholder() -> None:
    art = load_mock("professional/changes/generated_success.json")
    assert art["draft_watermark"] is True
    assert art["disclaimer"] == "Draft generated for review. Not a compliance determination."
    if GS1_TEST_PLACEHOLDER in art["barcode_decision"]["new_payload"]:
        assert art["test_data"] is True
    needs = load_mock("professional/changes/generate_needs_input.json")
    assert needs["barcode_decision"]["new_payload"] == ""
    assert needs["task"]["title"] == "enter allocated identifier"


def test_names_are_clearly_fake() -> None:
    names = []
    for entry in ENTRIES:
        for node in walk(load_mock(entry["file"])):
            if isinstance(node, dict):
                names += [node[k] for k in ("name", "product_name", "manufacturer") if isinstance(node.get(k), str)]
    assert names
    for name in names:
        assert re.search(r"Example|Sample|Demo|^sterile_eo$|^manufacturer$", name), name


# ---------------------------------------------------------------- workflow rules

def test_returned_change_status_is_derived_from_its_latest_review() -> None:
    change = load_mock("professional/changes/change_returned.json")
    review = load_mock("professional/review/returned.json")
    assert change["latest_review_id"] == review["review_id"]
    assert review["decision"] == "return" and review["resulting_status"] == "draft"
    assert change["status"] == "draft" and change["closed"] is False


def test_rejected_change_is_closed() -> None:
    change = load_mock("professional/changes/change_rejected.json")
    assert change["closed"] is True and change["status"] == "draft"


def test_approval_is_bound_to_a_passed_check_and_not_self_approved() -> None:
    review = load_mock("professional/review/approved.json")
    check = load_mock("professional/review/recheck_success.json")
    art = load_mock("professional/changes/generated_success.json")
    change = load_mock("professional/changes/assess_success.json")["change"]
    assert review["check_id"] == check["check_id"] and check["passed"] is True
    assert review["version_id"] == check["version_id"] == art["version_id"]
    assert review["artifact_sha256"] == check["artifact_sha256"] == art["artifact_sha256"]
    assert review["user_id"] != change["created_by"]
    forbidden = load_mock("professional/review/self_approval_forbidden.json")
    assert forbidden["error"] == "self_approval_forbidden"


def test_published_export_is_pinned_to_its_version() -> None:
    export = load_mock("professional/export/approved.json")
    assert export["qr"]["version_id"] == export["version_id"] == export["report"]["version_id"]
    assert export["draft_watermark"] is False
    assert load_mock("professional/export/draft.json")["draft_watermark"] is True


def test_long_operations_return_job_envelopes() -> None:
    for operation_id in ("uploadScan", "generateArtwork", "verifyPrint", "publicScan"):
        schema = response_schema(operation_id, 202)
        assert schema == {"$ref": "#/components/schemas/Job"}, operation_id
    loading = [e for e in ENTRIES if e["state"] == "loading"]
    assert loading and all(e["schema"] == "Job" and e["status"] == 202 for e in loading)


# ---------------------------------------------------------------- coverage

def test_every_required_state_is_covered() -> None:
    assert REQUIRED_STATES <= {e["state"] for e in ENTRIES}


def test_all_four_abstain_reasons_are_mocked_without_answer_text() -> None:
    reasons = set()
    for entry in ENTRIES:
        if entry["state"] == "abstained":
            data = load_mock(entry["file"])
            assert data["abstained"] is True and "answer" not in data
            assert isinstance(data["score_name"], str) and data["score_name"]
            reasons.add(data["reason"])
    assert reasons == ABSTAIN_REASONS


def test_public_and_professional_mocks_stay_separate() -> None:
    for entry in ENTRIES:
        tags = find_operation(entry["operationId"]).get("tags", [])
        if entry["file"].startswith("public/"):
            assert "public" in tags or "common" in tags, entry["file"]
        else:
            assert "device" in tags or "common" in tags, entry["file"]


def test_contract_docs_have_no_em_dashes() -> None:
    for path in (ROOT / "docs" / "contracts").iterdir():
        assert "—" not in path.read_text(encoding="utf-8"), path.name


# ---------------------------------------------------------------- Step 21: checker coverage (CR-17)

def _check_results() -> Iterator[tuple[str, dict[str, Any]]]:
    for entry in ENTRIES:
        data = load_mock(entry["file"])
        if isinstance(data, dict) and data.get("kind") in ("inspection", "self_check"):
            yield entry["file"], data


def test_inspection_mocks_carry_coverage_and_needs_human_count() -> None:
    seen = 0
    for file, data in _check_results():
        ids = [o["rule_id"] for o in data["coverage"]]
        assert len(ids) == len(set(ids)), file
        assert data["needs_human_count"] == sum(o["outcome"] == "needs_human" for o in data["coverage"]), file
        assert data["critical_count"] == sum(f["severity"] == "critical" for f in data["findings"]), file
        assert data["passed"] == (data["critical_count"] == 0), file
        seen += 1
    assert seen >= 4


def test_findings_contain_only_problems() -> None:
    for file, data in _check_results():
        assert all(f["severity"] != "info" for f in data["findings"]), file


def test_a_fail_outcome_has_a_finding_with_the_same_rule() -> None:
    for file, data in _check_results():
        rules = {f.get("rule_id") for f in data["findings"]}
        for outcome in data["coverage"]:
            if outcome["outcome"] == "fail":
                assert outcome["rule_id"] in rules, (file, outcome["rule_id"])


def test_rx_only_is_documented_for_product_registration() -> None:
    extra = SPEC["components"]["schemas"]["ProductCreate"]["properties"]["extra"]
    assert "rx_only" in extra["description"]
    assert "rx_only" in (ROOT / "docs" / "contracts" / "DATA_MODEL.md").read_text(encoding="utf-8")
