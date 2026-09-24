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
