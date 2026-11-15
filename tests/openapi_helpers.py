"""Small helpers to validate a live API response against its schema in docs/contracts/openapi.yaml."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

SPEC_PATH = Path(__file__).resolve().parents[1] / "docs" / "contracts" / "openapi.yaml"
SPEC: dict[str, Any] = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
REGISTRY = Registry().with_resource("urn:oas", Resource.from_contents(SPEC, default_specification=DRAFT202012))


def find_operation(operation_id: str) -> dict[str, Any]:
    """Return the OpenAPI operation object with this operationId."""
    for item in SPEC["paths"].values():
        for op in item.values():
            if isinstance(op, dict) and op.get("operationId") == operation_id:
                return op
    raise KeyError(operation_id)


def documented_statuses(operation_id: str) -> set[int]:
    """Every status code the spec documents for an operation."""
    return {int(code) for code in find_operation(operation_id)["responses"]}


def response_schema(operation_id: str, status: int) -> dict[str, Any]:
    """The JSON schema of one documented response. Raises AssertionError if the status is not documented."""
    responses = find_operation(operation_id)["responses"]
    assert str(status) in responses, f"{operation_id}: status {status} is not documented in openapi.yaml"
    response = responses[str(status)]
    if "$ref" in response:
        response = SPEC["components"]["responses"][response["$ref"].split("/")[-1]]
    return response["content"]["application/json"]["schema"]


def validator_for(schema: dict[str, Any]) -> Draft202012Validator:
    """A 2020-12 validator whose $refs resolve inside openapi.yaml."""
    rewritten = json.loads(json.dumps(schema).replace('"#/components/', '"urn:oas#/components/'))
    return Draft202012Validator(rewritten, registry=REGISTRY)


def conformance_errors(operation_id: str, status: int, body: Any) -> list[str]:
    """Schema violations of `body` against the documented response of (operation_id, status)."""
    validator = validator_for(response_schema(operation_id, status))
    return [f"{list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(body)]
