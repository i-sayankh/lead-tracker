from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LeadStatus(StrEnum):
    """Pipeline stage of a lead."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    LOST = "lost"


class HealthResponse(BaseModel):
    """Service health, including database connectivity."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"status": "ok", "database": "ok"}]})

    status: Literal["ok"] = Field(description="Overall API status.", examples=["ok"])
    database: Literal["ok"] = Field(description="Database connectivity status.", examples=["ok"])
