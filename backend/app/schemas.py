import re
import uuid
from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.config import JsonDict

PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")
PHONE_SEPARATORS = re.compile(r"[\s\-.()]")
PHONE_RULE = "Phone must contain 7–15 digits, optionally prefixed with +"

EXAMPLE_LEAD: JsonDict = {
    "id": "3f1c2a9e-8b7d-4c1e-9f0a-2b6d5e4c3a21",
    "name": "Jane Cooper",
    "email": "jane@acme.com",
    "phone": "+919876543210",
    "status": "new",
    "created_at": "2026-09-24T10:15:30.123456+00:00",
}


class LeadStatus(StrEnum):
    """Pipeline stage of a lead."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    LOST = "lost"


class LeadCreate(BaseModel):
    """Request body for creating a lead. Unknown fields are rejected."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "Jane Cooper",
                    "email": "Jane@Acme.com",
                    "phone": "+91 98765-43210",
                    "status": "new",
                }
            ]
        },
    )

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Full name of the lead. Leading and trailing whitespace is trimmed.",
        examples=["Jane Cooper"],
    )
    email: EmailStr = Field(
        max_length=254,
        description="Email address. Stored lowercase and unique across all leads.",
        examples=["jane@acme.com"],
    )
    phone: str = Field(
        description=(
            "Phone number. Spaces, dashes, dots and parentheses are removed; the result must "
            "be 7–15 digits, optionally prefixed with `+`. The normalized value is stored."
        ),
        examples=["+91 98765-43210"],
    )
    status: LeadStatus = Field(
        default=LeadStatus.NEW,
        description="Initial pipeline stage. Defaults to `new`.",
        examples=["new"],
    )

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        normalized = PHONE_SEPARATORS.sub("", value)
        if not PHONE_PATTERN.fullmatch(normalized):
            raise ValueError(PHONE_RULE)
        return normalized


class LeadStatusUpdate(BaseModel):
    """Request body for changing a lead's status. Unknown fields are rejected."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"examples": [{"status": "qualified"}]}
    )

    status: LeadStatus = Field(description="The new pipeline stage.", examples=["qualified"])


class LeadRead(BaseModel):
    """A lead as returned by the API."""

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"examples": [EXAMPLE_LEAD]})

    id: uuid.UUID = Field(
        description="Server-generated unique identifier.", examples=[EXAMPLE_LEAD["id"]]
    )
    name: str = Field(description="Full name of the lead.", examples=["Jane Cooper"])
    email: str = Field(description="Lowercase email address.", examples=["jane@acme.com"])
    phone: str = Field(
        description="Normalized phone number (optional `+`, then 7–15 digits).",
        examples=["+919876543210"],
    )
    status: LeadStatus = Field(description="Current pipeline stage.", examples=["new"])
    created_at: AwareDatetime = Field(
        description="When the lead was created (ISO 8601 with UTC offset).",
        examples=[EXAMPLE_LEAD["created_at"]],
    )


class LeadPage(BaseModel):
    """One page of leads, newest first, with the total count matching the filters."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"items": [EXAMPLE_LEAD], "total": 57, "limit": 20, "offset": 0}]
        }
    )

    items: list[LeadRead] = Field(
        description="Leads on this page, ordered by `created_at` descending."
    )
    total: int = Field(
        description="Number of leads matching the filters, ignoring pagination.", examples=[57]
    )
    limit: int = Field(description="Page size that was applied.", examples=[20])
    offset: int = Field(description="Number of matching leads skipped.", examples=[0])


class HealthResponse(BaseModel):
    """Service health, including database connectivity."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "ok", "database": "ok"}]})

    status: Literal["ok"] = Field(description="Overall API status.", examples=["ok"])
    database: Literal["ok"] = Field(description="Database connectivity status.", examples=["ok"])
