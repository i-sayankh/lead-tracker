import logging
from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.errors")

# Shared by the handlers and the OpenAPI examples so the docs match what is sent.
VALIDATION_FAILED_MESSAGE = "Request validation failed."
INTERNAL_ERROR_MESSAGE = "An unexpected error occurred."
DATABASE_UNREACHABLE_MESSAGE = "Database is unreachable."


class ErrorCode(StrEnum):
    """Machine-readable error code. Clients should branch on this, not on `message`."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    LEAD_NOT_FOUND = "LEAD_NOT_FOUND"
    LEAD_EMAIL_CONFLICT = "LEAD_EMAIL_CONFLICT"
    ROUTE_NOT_FOUND = "ROUTE_NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorDetail(BaseModel):
    """A problem with one input field."""

    field: str = Field(
        description="Dotted location of the invalid input, e.g. `body.email` or `query.limit`.",
        examples=["body.email"],
    )
    message: str = Field(
        description="Human-readable explanation.",
        examples=["value is not a valid email address: An email address must have an @-sign."],
    )
    type: str = Field(
        description="Error type, e.g. `missing`, `value_error`, `conflict`.",
        examples=["value_error"],
    )


class ErrorBody(BaseModel):
    """Error payload."""

    code: ErrorCode = Field(description="Machine-readable error code.", examples=["LEAD_NOT_FOUND"])
    message: str = Field(
        description="Human-readable summary of the error.",
        examples=["Lead '3f1c2a9e-8b7d-4c1e-9f0a-2b6d5e4c3a21' was not found."],
    )
    details: list[ErrorDetail] | None = Field(
        default=None,
        description="Per-field problems for validation and conflict errors; otherwise `null`.",
    )


class ErrorResponse(BaseModel):
    """Envelope used by every non-2xx response."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "error": {
                        "code": "LEAD_NOT_FOUND",
                        "message": "Lead '3f1c2a9e-8b7d-4c1e-9f0a-2b6d5e4c3a21' was not found.",
                        "details": None,
                    }
                }
            ]
        }
    )

    error: ErrorBody = Field(description="The error that occurred.")


class AppError(Exception):
    """Base for domain errors that map to a documented status code and error code."""

    status_code: int = 500
    code: ErrorCode = ErrorCode.INTERNAL_ERROR

    def __init__(self, message: str, details: list[ErrorDetail] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class LeadNotFoundError(AppError):
    status_code = 404
    code = ErrorCode.LEAD_NOT_FOUND

    def __init__(self, lead_id: object) -> None:
        super().__init__(f"Lead '{lead_id}' was not found.")


class LeadEmailConflictError(AppError):
    status_code = 409
    code = ErrorCode.LEAD_EMAIL_CONFLICT

    def __init__(self, email: str) -> None:
        super().__init__(
            f"A lead with email '{email}' already exists.",
            [ErrorDetail(field="body.email", message="Email already exists", type="conflict")],
        )


class ServiceUnavailableError(AppError):
    status_code = 503
    code = ErrorCode.SERVICE_UNAVAILABLE

    def __init__(self) -> None:
        super().__init__(DATABASE_UNREACHABLE_MESSAGE)


def _envelope(
    status_code: int, code: ErrorCode, message: str, details: list[ErrorDetail] | None = None
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def _app_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    return _envelope(exc.status_code, exc.code, exc.message, exc.details)


async def _validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ErrorDetail(
            field=".".join(str(part) for part in err["loc"]),
            message=str(err["msg"]).removeprefix("Value error, "),
            type=str(err["type"]),
        )
        for err in exc.errors()
    ]
    return _envelope(422, ErrorCode.VALIDATION_ERROR, VALIDATION_FAILED_MESSAGE, details)


async def _http_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    if exc.status_code == 404:
        return _envelope(404, ErrorCode.ROUTE_NOT_FOUND, "Route not found.")
    if exc.status_code == 405:
        return _envelope(405, ErrorCode.METHOD_NOT_ALLOWED, "Method not allowed.")
    logger.error("Unexpected HTTP %s: %s", exc.status_code, exc.detail)
    return _envelope(500, ErrorCode.INTERNAL_ERROR, INTERNAL_ERROR_MESSAGE)


class CatchUnhandledErrors:
    """ASGI middleware turning any unhandled exception into the 500 envelope.

    A middleware rather than an `Exception` handler: Starlette runs `Exception` handlers
    outside every user middleware, so those 500s would miss the CORS headers and the browser
    would report a network error instead of showing the envelope. Add it *inside* CORS.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def track(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, track)
        except Exception:
            # Log the traceback server-side; never leak exception text to the client.
            logger.exception("Unhandled error on %s %s", scope["method"], scope["path"])
            if response_started:
                raise
            response = _envelope(500, ErrorCode.INTERNAL_ERROR, INTERNAL_ERROR_MESSAGE)
            await response(scope, receive, send)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, _http_error_handler)


# --- OpenAPI documentation helpers -------------------------------------------------------------

Example = dict[str, Any]


def error_example(
    summary: str,
    code: ErrorCode,
    message: str,
    details: list[tuple[str, str, str]] | None = None,
) -> Example:
    """Build a named OpenAPI example of an `ErrorResponse`. `details` is (field, message, type)."""
    return {
        "summary": summary,
        "value": {
            "error": {
                "code": code,
                "message": message,
                "details": (
                    [{"field": f, "message": m, "type": t} for f, m, t in details]
                    if details is not None
                    else None
                ),
            }
        },
    }


_DEFAULTS: dict[int, tuple[str, dict[str, Example]]] = {
    404: (
        "The lead does not exist.",
        {
            "lead_not_found": error_example(
                "Unknown lead id",
                ErrorCode.LEAD_NOT_FOUND,
                "Lead '3f1c2a9e-8b7d-4c1e-9f0a-2b6d5e4c3a21' was not found.",
            )
        },
    ),
    409: (
        "A lead with this email already exists (comparison is case-insensitive).",
        {
            "email_conflict": error_example(
                "Duplicate email",
                ErrorCode.LEAD_EMAIL_CONFLICT,
                "A lead with email 'jane@acme.com' already exists.",
                [("body.email", "Email already exists", "conflict")],
            )
        },
    ),
    422: ("The request failed validation. `details` lists every invalid field.", {}),
    500: (
        "Unexpected server error. The cause is logged server-side and never returned.",
        {
            "internal_error": error_example(
                "Unexpected error", ErrorCode.INTERNAL_ERROR, INTERNAL_ERROR_MESSAGE
            )
        },
    ),
    503: (
        "The database is unreachable.",
        {
            "database_unreachable": error_example(
                "Database down", ErrorCode.SERVICE_UNAVAILABLE, DATABASE_UNREACHABLE_MESSAGE
            )
        },
    ),
}


def error_responses(
    *status_codes: int, examples: dict[int, dict[str, Example]] | None = None
) -> dict[int | str, dict[str, Any]]:
    """`responses=` value documenting each status code with `ErrorResponse` and named examples.

    `examples` adds route-specific examples (e.g. the 422 cases a route can produce).
    """
    responses: dict[int | str, dict[str, Any]] = {}
    for status_code in status_codes:
        description, defaults = _DEFAULTS[status_code]
        named = {**defaults, **(examples or {}).get(status_code, {})}
        responses[status_code] = {
            "model": ErrorResponse,
            "description": description,
            "content": {"application/json": {"examples": named}},
        }
    return responses
