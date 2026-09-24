import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app import services
from app.db import get_db
from app.errors import VALIDATION_FAILED_MESSAGE, ErrorCode, error_example, error_responses
from app.models import Lead
from app.schemas import PHONE_RULE, LeadCreate, LeadPage, LeadRead, LeadStatus, LeadStatusUpdate

router = APIRouter(prefix="/leads", tags=["leads"])

DbSession = Annotated[Session, Depends(get_db)]

# Keeps offsets far below Postgres' bigint limit (larger values would be a 500, not a 422).
MAX_OFFSET = 1_000_000

VALIDATION = ErrorCode.VALIDATION_ERROR
FAILED = VALIDATION_FAILED_MESSAGE


@router.post(
    "",
    response_model=LeadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a lead",
    description=(
        "Creates a lead with status `new` unless another status is given.\n\n"
        "- `email` is lowercased and must be unique (case-insensitive).\n"
        "- `phone` is normalized by removing spaces, dashes, dots and parentheses; the result "
        "must be 7–15 digits, optionally prefixed with `+`.\n"
        "- Unknown fields are rejected.\n\n"
        "**Errors**\n\n"
        "- `409 LEAD_EMAIL_CONFLICT`: a lead with this email already exists.\n"
        "- `422 VALIDATION_ERROR`: a field is missing or invalid, the body is not valid JSON, "
        "or it contains an unknown field. `details` names each field.\n"
        "- `500 INTERNAL_ERROR`: unexpected server error."
    ),
    response_description="The created lead.",
    responses=error_responses(
        409,
        422,
        500,
        examples={
            422: {
                "invalid_email": error_example(
                    "Invalid email",
                    VALIDATION,
                    FAILED,
                    [
                        (
                            "body.email",
                            "value is not a valid email address: "
                            "An email address must have an @-sign.",
                            "value_error",
                        )
                    ],
                ),
                "bad_phone": error_example(
                    "Invalid phone", VALIDATION, FAILED, [("body.phone", PHONE_RULE, "value_error")]
                ),
                "missing_name": error_example(
                    "Missing name", VALIDATION, FAILED, [("body.name", "Field required", "missing")]
                ),
                "extra_field": error_example(
                    "Unknown field",
                    VALIDATION,
                    FAILED,
                    [("body.company", "Extra inputs are not permitted", "extra_forbidden")],
                ),
            }
        },
    ),
)
def create_lead(body: LeadCreate, db: DbSession) -> Lead:
    return services.create_lead(db, body)


@router.get(
    "",
    response_model=LeadPage,
    summary="List and search leads",
    description=(
        "Returns one page of leads ordered newest first (`created_at` descending, then `id`).\n\n"
        "- `q` does a case-insensitive substring match on name, email **or** phone. "
        "`%` and `_` are matched literally. An empty or whitespace-only `q` means no filter.\n"
        "- `status` keeps only leads in that stage. It combines with `q`.\n"
        "- `total` is the number of leads matching the filters, ignoring `limit`/`offset`.\n\n"
        "**Errors**\n\n"
        "- `422 VALIDATION_ERROR`: a query parameter is out of bounds or not an allowed value.\n"
        "- `500 INTERNAL_ERROR`: unexpected server error."
    ),
    response_description="A page of leads and the total number matching the filters.",
    responses=error_responses(
        422,
        500,
        examples={
            422: {
                "limit_too_small": error_example(
                    "limit=0",
                    VALIDATION,
                    FAILED,
                    [
                        (
                            "query.limit",
                            "Input should be greater than or equal to 1",
                            "greater_than_equal",
                        )
                    ],
                ),
                "unknown_status": error_example(
                    "status=unknown",
                    VALIDATION,
                    FAILED,
                    [
                        (
                            "query.status",
                            "Input should be 'new', 'contacted', 'qualified' or 'lost'",
                            "enum",
                        )
                    ],
                ),
            }
        },
    ),
)
def list_leads(
    db: DbSession,
    q: Annotated[
        str | None,
        Query(
            max_length=100,
            description=(
                "Case-insensitive substring to match against name, email or phone. "
                "Trimmed; empty means no filter."
            ),
            openapi_examples={"name": {"summary": "Match a name", "value": "jane"}},
        ),
    ] = None,
    status: Annotated[
        LeadStatus | None,
        Query(
            description="Only return leads in this stage.",
            openapi_examples={"contacted": {"summary": "Contacted", "value": "contacted"}},
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Page size (1–100).",
            openapi_examples={"default": {"summary": "Default", "value": 20}},
        ),
    ] = 20,
    offset: Annotated[
        int,
        Query(
            ge=0,
            le=MAX_OFFSET,
            description=f"Number of matching leads to skip (0–{MAX_OFFSET:,}).",
            openapi_examples={"first_page": {"summary": "First page", "value": 0}},
        ),
    ] = 0,
) -> LeadPage:
    items, total = services.list_leads(
        db, q=(q or "").strip() or None, status=status, limit=limit, offset=offset
    )
    return LeadPage(
        items=[LeadRead.model_validate(lead) for lead in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/{lead_id}/status",
    response_model=LeadRead,
    summary="Update a lead's status",
    description=(
        "Sets the pipeline stage of one lead and returns the updated lead.\n\n"
        "- Any status may follow any other (there is no enforced transition order).\n"
        "- Setting the status a lead already has is an idempotent success (`200`).\n\n"
        "**Errors**\n\n"
        "- `404 LEAD_NOT_FOUND`: no lead has this id.\n"
        "- `422 VALIDATION_ERROR`: `lead_id` is not a UUID, the body is missing, `status` is "
        "missing or not an allowed value, or the body has an unknown field.\n"
        "- `500 INTERNAL_ERROR`: unexpected server error."
    ),
    response_description="The lead with its updated status.",
    responses=error_responses(
        404,
        422,
        500,
        examples={
            422: {
                "invalid_status": error_example(
                    "Invalid status",
                    VALIDATION,
                    FAILED,
                    [
                        (
                            "body.status",
                            "Input should be 'new', 'contacted', 'qualified' or 'lost'",
                            "enum",
                        )
                    ],
                ),
                "malformed_uuid": error_example(
                    "Malformed lead id",
                    VALIDATION,
                    FAILED,
                    [
                        (
                            "path.lead_id",
                            "Input should be a valid UUID, invalid character: found `n` at 1",
                            "uuid_parsing",
                        )
                    ],
                ),
                "missing_body": error_example(
                    "Missing body", VALIDATION, FAILED, [("body", "Field required", "missing")]
                ),
            }
        },
    ),
)
def update_lead_status(
    lead_id: Annotated[
        uuid.UUID,
        Path(
            description="Id of the lead to update.",
            openapi_examples={
                "lead_id": {"summary": "A lead id", "value": "3f1c2a9e-8b7d-4c1e-9f0a-2b6d5e4c3a21"}
            },
        ),
    ],
    body: LeadStatusUpdate,
    db: DbSession,
) -> Lead:
    return services.update_lead_status(db, lead_id, body.status)
