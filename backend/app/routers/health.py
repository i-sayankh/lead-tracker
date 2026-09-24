from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db
from app.errors import ServiceUnavailableError, error_responses
from app.schemas import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API and database health",
    description=(
        "Runs `SELECT 1` against the database. Used as the deployment health check.\n\n"
        "**Errors**\n\n"
        "- `503 SERVICE_UNAVAILABLE`: the database cannot be reached."
    ),
    response_description="The API and its database are reachable.",
    responses=error_responses(503),
)
def health_check(db: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ServiceUnavailableError() from exc
    return HealthResponse(status="ok", database="ok")
