import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.errors import CatchUnhandledErrors, register_error_handlers
from app.routers import health, leads

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

API_PREFIX = "/api/v1"

DESCRIPTION = """
A small CRM-style API for tracking sales leads: create a lead, list and search leads,
and move a lead through the pipeline by updating its status.

## Lead status

| Value | Meaning |
|---|---|
| `new` | Just created; nobody has reached out yet (default). |
| `contacted` | First contact has been made. |
| `qualified` | The lead is a real opportunity. |
| `lost` | The lead will not convert. |

Any status may follow any other.

## Pagination

`GET /api/v1/leads` takes `limit` (1–100, default 20) and `offset` (default 0) and returns
`total`, the number of leads matching the filters regardless of pagination. Results are
ordered newest first.

## Errors

Every non-2xx response uses the same `ErrorResponse` envelope. Branch on `error.code`;
`error.message` is for humans. `error.details` lists each invalid field for validation
and conflict errors and is `null` otherwise.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": [
      {
        "field": "body.email",
        "message": "value is not a valid email address: An email address must have an @-sign.",
        "type": "value_error"
      }
    ]
  }
}
```

| Status | `code` |
|---|---|
| 404 | `LEAD_NOT_FOUND`, `ROUTE_NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 409 | `LEAD_EMAIL_CONFLICT` |
| 422 | `VALIDATION_ERROR` |
| 500 | `INTERNAL_ERROR` |
| 503 | `SERVICE_UNAVAILABLE` |
"""


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Lead Tracker API",
        version="1.0.0",
        summary="Create, list, search and update the status of sales leads.",
        description=DESCRIPTION,
        contact={"name": "Sayan Khutia", "url": "https://github.com/i-sayankh/lead-tracker"},
        openapi_tags=[
            {"name": "leads", "description": "Create, list, search and update leads."},
            {"name": "health", "description": "Liveness and database connectivity."},
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        generate_unique_id_function=lambda route: route.name,
    )
    register_error_handlers(app)
    # Order matters: middleware added last is outermost, so CORS wraps the 500 catch-all
    # and even unexpected errors reach the browser with CORS headers.
    app.add_middleware(CatchUnhandledErrors)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )
    app.include_router(leads.router, prefix=API_PREFIX)
    app.include_router(health.router, prefix=API_PREFIX)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/docs")

    return app


app = create_app()
