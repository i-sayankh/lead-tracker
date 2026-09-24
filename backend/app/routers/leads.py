from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import services
from app.db import get_db
from app.errors import ErrorCode, error_example, error_responses
from app.models import Lead
from app.schemas import PHONE_RULE, LeadCreate, LeadRead

router = APIRouter(prefix="/leads", tags=["leads"])

DbSession = Annotated[Session, Depends(get_db)]

VALIDATION = ErrorCode.VALIDATION_ERROR
FAILED = "Request validation failed."


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
