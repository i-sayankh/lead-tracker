import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.parametrize(
    "url",
    ["postgres://u:p@host:5432/db", "postgresql://u:p@host:5432/db"],
)
def test_database_url_uses_the_psycopg_driver(url: str) -> None:
    settings = Settings(database_url=url)

    assert settings.database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_cors_origins_are_parsed_from_a_comma_separated_list() -> None:
    settings = Settings(
        database_url="postgresql://x", CORS_ORIGINS=" https://a.app , http://localhost:5173 ,"
    )

    assert settings.cors_origins == ["https://a.app", "http://localhost:5173"]


def test_wildcard_cors_origin_is_rejected() -> None:
    with pytest.raises(ValidationError, match="explicit origins"):
        Settings(database_url="postgresql://x", CORS_ORIGINS="https://a.app,*")
