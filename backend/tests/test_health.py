from fastapi.testclient import TestClient


def test_health_check_reports_ok_when_database_is_reachable(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_check_returns_503_envelope_when_database_is_unreachable(
    client: TestClient,
) -> None:
    from sqlalchemy.exc import OperationalError

    from app.db import get_db

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


def test_unhandled_error_returns_500_envelope_without_leaking_exception_text() -> None:
    from app.db import get_db
    from app.main import create_app

    class ExplodingSession:
        def execute(self, *_: object) -> None:
            raise RuntimeError("secret connection string")

    app = create_app()
    app.dependency_overrides[get_db] = lambda: ExplodingSession()
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred.",
            "details": None,
        }
    }
    assert "secret" not in response.text
