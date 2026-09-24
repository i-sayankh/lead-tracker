from typing import Any

import pytest
from fastapi.testclient import TestClient

URL = "/api/v1/leads"


def create(
    client: TestClient, name: str, email: str, phone: str = "+15550000000", **extra: Any
) -> dict[str, Any]:
    response = client.post(URL, json={"name": name, "email": email, "phone": phone, **extra})
    assert response.status_code == 201, response.text
    body: dict[str, Any] = response.json()
    return body


def names(response: Any) -> list[str]:
    assert response.status_code == 200, response.text
    return [item["name"] for item in response.json()["items"]]


def test_list_leads_on_empty_database_returns_empty_page(client: TestClient) -> None:
    response = client.get(URL)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}


def test_list_leads_orders_newest_first(client: TestClient) -> None:
    for i in range(3):
        create(client, f"Lead {i}", f"lead{i}@example.com")

    assert names(client.get(URL)) == ["Lead 2", "Lead 1", "Lead 0"]


def test_list_leads_paginates_with_limit_and_offset_and_total_ignores_pagination(
    client: TestClient,
) -> None:
    for i in range(5):
        create(client, f"Lead {i}", f"lead{i}@example.com")

    response = client.get(URL, params={"limit": 2, "offset": 1})

    assert names(response) == ["Lead 3", "Lead 2"]
    assert response.json()["total"] == 5
    assert response.json()["limit"] == 2
    assert response.json()["offset"] == 1


@pytest.fixture
def people(client: TestClient) -> None:
    create(client, "Jane Cooper", "jane@acme.com", "+919876543210")
    create(client, "Robert Fox", "robert@globex.io", "+14155550123", status="contacted")
    create(client, "Janet Lee", "janet@initech.com", "+447700900123", status="qualified")


@pytest.mark.usefixtures("people")
def test_search_matches_partial_name_case_insensitively(client: TestClient) -> None:
    assert names(client.get(URL, params={"q": "JAN"})) == ["Janet Lee", "Jane Cooper"]


@pytest.mark.usefixtures("people")
def test_search_matches_partial_email(client: TestClient) -> None:
    assert names(client.get(URL, params={"q": "globex"})) == ["Robert Fox"]


@pytest.mark.usefixtures("people")
def test_search_matches_partial_phone_digits(client: TestClient) -> None:
    assert names(client.get(URL, params={"q": "98765"})) == ["Jane Cooper"]


@pytest.mark.usefixtures("people")
def test_search_trims_whitespace_and_treats_empty_as_no_filter(client: TestClient) -> None:
    assert names(client.get(URL, params={"q": "  fox  "})) == ["Robert Fox"]
    assert client.get(URL, params={"q": "   "}).json()["total"] == 3


def test_search_treats_percent_and_underscore_literally(client: TestClient) -> None:
    create(client, "100% Growth", "growth@example.com")
    create(client, "snake_case", "snake@example.com")
    create(client, "Plain Name", "plain@example.com")

    assert names(client.get(URL, params={"q": "%"})) == ["100% Growth"]
    assert names(client.get(URL, params={"q": "_"})) == ["snake_case"]


@pytest.mark.usefixtures("people")
def test_status_filter_returns_only_matching_status(client: TestClient) -> None:
    response = client.get(URL, params={"status": "contacted"})

    assert names(response) == ["Robert Fox"]
    assert response.json()["total"] == 1


@pytest.mark.usefixtures("people")
def test_status_filter_combines_with_search(client: TestClient) -> None:
    assert names(client.get(URL, params={"q": "jan", "status": "qualified"})) == ["Janet Lee"]


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"limit": 0}, "query.limit"),
        ({"limit": 101}, "query.limit"),
        ({"offset": -1}, "query.offset"),
        ({"status": "bogus"}, "query.status"),
        ({"q": "x" * 101}, "query.q"),
    ],
)
def test_list_leads_rejects_invalid_query_parameters(
    client: TestClient, params: dict[str, Any], field: str
) -> None:
    response = client.get(URL, params=params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["field"] == field
