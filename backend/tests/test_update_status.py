import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/leads"


@pytest.fixture
def lead(client: TestClient) -> dict[str, Any]:
    response = client.post(
        URL, json={"name": "Jane Cooper", "email": "jane@acme.com", "phone": "+919876543210"}
    )
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


def status_url(lead_id: object) -> str:
    return f"{URL}/{lead_id}/status"


def test_update_status_changes_and_persists_status(
    client: TestClient, lead: dict[str, Any]
) -> None:
    response = client.patch(status_url(lead["id"]), json={"status": "qualified"})

    assert response.status_code == 200
    assert response.json() == {**lead, "status": "qualified"}
    listed = client.get(URL).json()["items"]
    assert [item["status"] for item in listed] == ["qualified"]


def test_update_status_to_same_status_is_idempotent(
    client: TestClient, lead: dict[str, Any]
) -> None:
    first = client.patch(status_url(lead["id"]), json={"status": "new"})
    second = client.patch(status_url(lead["id"]), json={"status": "new"})

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == lead


def test_update_status_returns_404_for_unknown_lead(client: TestClient) -> None:
    missing = uuid.uuid4()

    response = client.patch(status_url(missing), json={"status": "lost"})

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "LEAD_NOT_FOUND",
            "message": f"Lead '{missing}' was not found.",
            "details": None,
        }
    }


@pytest.mark.parametrize(
    ("path_id", "body", "field"),
    [
        ("not-a-uuid", {"status": "lost"}, "path.lead_id"),
        (None, {"status": "won"}, "body.status"),
        (None, {}, "body.status"),
        (None, {"status": "lost", "name": "x"}, "body.name"),
    ],
    ids=["malformed_uuid", "invalid_status", "missing_status", "extra_field"],
)
def test_update_status_rejects_invalid_input(
    client: TestClient,
    lead: dict[str, Any],
    path_id: str | None,
    body: dict[str, Any],
    field: str,
) -> None:
    response = client.patch(status_url(path_id or lead["id"]), json=body)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert [d["field"] for d in response.json()["error"]["details"]] == [field]
