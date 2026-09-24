from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.db import get_db
from app.main import create_app


def test_health_check_reports_ok_when_database_is_reachable(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_check_returns_503_envelope_when_database_is_unreachable(
    client: TestClient,
) -> None:
    from sqlalchemy.exc import OperationalError

    class BrokenSession:
        def execute(self, *_: object) -> None:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    client.app.dependency_overrides[get_db] = lambda: BrokenSession()  # type: ignore[attr-defined]

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "Database is unreachable.",
            "details": None,
        }
    }


@pytest.fixture
def exploding_client() -> Iterator[TestClient]:
    """A client whose database session raises an unexpected (non-SQLAlchemy) error."""

    class ExplodingSession:
        def execute(self, *_: object) -> None:
            raise RuntimeError("secret connection string")

    app = create_app()
    app.dependency_overrides[get_db] = lambda: ExplodingSession()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_unhandled_error_returns_500_envelope_without_leaking_exception_text(
    exploding_client: TestClient,
) -> None:
    response = exploding_client.get("/api/v1/health")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
            "details": None,
        }
    }
    assert "secret" not in response.text


def test_unhandled_error_response_still_carries_cors_headers(exploding_client: TestClient) -> None:
    # Without them the browser hides the 500 envelope and reports a network error.
    response = exploding_client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
