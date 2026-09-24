from typing import Any

import pytest
from fastapi.testclient import TestClient


def test_unknown_route_returns_route_not_found_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "ROUTE_NOT_FOUND", "message": "Route not found.", "details": None}
    }


def test_wrong_method_returns_method_not_allowed_envelope(client: TestClient) -> None:
    response = client.delete("/api/v1/health")

    assert response.status_code == 405
    assert response.json() == {
        "error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed.", "details": None}
    }


EXPECTED_OPERATIONS = {
    ("post", "/api/v1/leads"): ("create_lead", {"201", "409", "422", "500"}),
    ("get", "/api/v1/leads"): ("list_leads", {"200", "422", "500"}),
    ("patch", "/api/v1/leads/{lead_id}/status"): (
        "update_lead_status",
        {"200", "404", "422", "500"},
    ),
    ("get", "/api/v1/health"): ("health_check", {"200", "503"}),
}
ERROR_REF = "#/components/schemas/ErrorResponse"


@pytest.fixture
def spec(client: TestClient) -> dict[str, Any]:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def operations(spec: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (method, path): op for path, item in spec["paths"].items() for method, op in item.items()
    }


def test_spec_contains_exactly_the_expected_operations(spec: dict[str, Any]) -> None:
    assert set(operations(spec)) == set(EXPECTED_OPERATIONS)


@pytest.mark.parametrize("key", list(EXPECTED_OPERATIONS), ids=lambda k: f"{k[0]} {k[1]}")
def test_operation_is_fully_documented(spec: dict[str, Any], key: tuple[str, str]) -> None:
    op = operations(spec)[key]
    operation_id, statuses = EXPECTED_OPERATIONS[key]

    assert op["operationId"] == operation_id
    assert op.get("summary")
    assert op.get("description")
    assert set(op["responses"]) == statuses
    for status_code, response in op["responses"].items():
        assert response.get("description"), status_code
        if int(status_code) >= 400:
            content = response["content"]["application/json"]
            assert content["schema"] == {"$ref": ERROR_REF}, status_code
            assert content.get("examples"), f"{status_code} has no named examples"
    for param in op.get("parameters", []):
        assert param.get("description"), param["name"]
        assert "example" in param or "examples" in param, param["name"]


def test_default_validation_error_schemas_are_absent(spec: dict[str, Any]) -> None:
    schemas = spec["components"]["schemas"]

    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas


def test_error_code_is_documented_as_an_enum(spec: dict[str, Any]) -> None:
    assert set(spec["components"]["schemas"]["ErrorCode"]["enum"]) == {
        "VALIDATION_ERROR",
        "LEAD_NOT_FOUND",
        "LEAD_EMAIL_CONFLICT",
        "ROUTE_NOT_FOUND",
        "METHOD_NOT_ALLOWED",
        "SERVICE_UNAVAILABLE",
        "INTERNAL_ERROR",
    }


def test_every_schema_property_has_a_description(spec: dict[str, Any]) -> None:
    missing = [
        f"{name}.{prop}"
        for name, schema in spec["components"]["schemas"].items()
        for prop, definition in schema.get("properties", {}).items()
        if not definition.get("description")
    ]

    assert missing == []


def test_every_schema_has_a_description(spec: dict[str, Any]) -> None:
    missing = [n for n, s in spec["components"]["schemas"].items() if not s.get("description")]

    assert missing == []


def test_api_metadata_describes_the_error_envelope(spec: dict[str, Any]) -> None:
    info = spec["info"]

    assert info["title"] == "Lead Tracker API"
    assert info["version"] == "1.0.0"
    assert "ErrorResponse" in info["description"] or '"error"' in info["description"]
    assert {t["name"] for t in spec["tags"]} == {"leads", "health"}
