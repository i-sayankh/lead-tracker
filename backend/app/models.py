import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.schemas import LeadStatus

EMAIL_UNIQUE_CONSTRAINT = "uq_leads_email"


class Lead(Base):
    __tablename__ = "leads"
    # Fetch server defaults (created_at, status) via INSERT ... RETURNING, not a second SELECT.
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint("email", name=EMAIL_UNIQUE_CONSTRAINT),
        Index("ix_leads_created_at", text("created_at DESC"), text("id DESC")),
        Index("ix_leads_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(100))
    # Always stored lowercase (normalized by the LeadCreate schema).
    email: Mapped[str] = mapped_column(String(254))
    # Stored normalized: optional leading "+" followed by 7-15 digits.
    phone: Mapped[str] = mapped_column(String(16))
    status: Mapped[LeadStatus] = mapped_column(
        Enum(
            LeadStatus,
            name="lead_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        server_default=LeadStatus.NEW.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
