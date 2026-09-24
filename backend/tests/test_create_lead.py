import uuid
from datetime import datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/leads"
VALID = {"name": "Jane Cooper", "email": "jane@acme.com", "phone": "+919876543210"}


def assert_validation_error(response: Any, field: str) -> None:
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Request validation failed."
    fields = [d["field"] for d in body["error"]["details"]]
    assert field in fields, fields


def test_create_lead_returns_201_with_all_fields(client: TestClient) -> None:
    response = client.post(URL, json=VALID)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "name", "email", "phone", "status", "created_at"}
    assert uuid.UUID(body["id"])
    assert body["name"] == "Jane Cooper"
    assert body["status"] == "new"
    assert datetime.fromisoformat(body["created_at"]).tzinfo is not None


def test_create_lead_lowercases_email_and_normalizes_phone(client: TestClient) -> None:
    response = client.post(
        URL, json={**VALID, "email": "Jane@Acme.COM", "phone": "+91 98765-43210"}
    )

    assert response.status_code == 201
    assert response.json()["email"] == "jane@acme.com"
    assert response.json()["phone"] == "+919876543210"


def test_create_lead_honors_explicit_status(client: TestClient) -> None:
    response = client.post(URL, json={**VALID, "status": "contacted"})

    assert response.status_code == 201
    assert response.json()["status"] == "contacted"


def test_create_lead_rejects_duplicate_email_with_different_casing(client: TestClient) -> None:
    assert client.post(URL, json={**VALID, "email": "jane@acme.com"}).status_code == 201

    response = client.post(URL, json={**VALID, "email": "Jane@Acme.com"})

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "LEAD_EMAIL_CONFLICT"
    assert error["message"] == "A lead with email 'jane@acme.com' already exists."
    assert error["details"][0]["field"] == "body.email"


def test_create_lead_rejects_missing_name(client: TestClient) -> None:
    payload = {k: v for k, v in VALID.items() if k != "name"}
    assert_validation_error(client.post(URL, json=payload), "body.name")


@pytest.mark.parametrize("name", ["", "   "])
def test_create_lead_rejects_empty_or_whitespace_name(client: TestClient, name: str) -> None:
    assert_validation_error(client.post(URL, json={**VALID, "name": name}), "body.name")


def test_create_lead_rejects_name_longer_than_100_chars(client: TestClient) -> None:
    assert_validation_error(client.post(URL, json={**VALID, "name": "a" * 101}), "body.name")


def test_create_lead_rejects_invalid_email(client: TestClient) -> None:
    assert_validation_error(client.post(URL, json={**VALID, "email": "not-an-email"}), "body.email")


def test_create_lead_rejects_phone_that_is_too_short(client: TestClient) -> None:
    response = client.post(URL, json={**VALID, "phone": "12345"})

    assert_validation_error(response, "body.phone")
    assert response.json()["error"]["details"][0]["message"] == (
        "Phone must contain 7–15 digits, optionally prefixed with +"
    )


def test_create_lead_rejects_phone_with_letters(client: TestClient) -> None:
    assert_validation_error(client.post(URL, json={**VALID, "phone": "555-CALL-NOW"}), "body.phone")


def test_create_lead_rejects_unknown_extra_field(client: TestClient) -> None:
    assert_validation_error(client.post(URL, json={**VALID, "company": "Acme"}), "body.company")


def test_create_lead_rejects_invalid_status(client: TestClient) -> None:
    assert_validation_error(client.post(URL, json={**VALID, "status": "won"}), "body.status")


def test_create_lead_rejects_malformed_json_body(client: TestClient) -> None:
    response = client.post(
        URL, content=b'{"name": "Jane",', headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    detail = response.json()["error"]["details"][0]
    assert detail["field"].startswith("body")
    assert detail["type"] == "json_invalid"
