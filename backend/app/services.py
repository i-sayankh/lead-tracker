import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import LeadEmailConflictError, LeadNotFoundError
from app.models import EMAIL_UNIQUE_CONSTRAINT, Lead
from app.schemas import PHONE_SEPARATORS, LeadCreate, LeadStatus


def create_lead(db: Session, data: LeadCreate) -> Lead:
    # Rely on the unique constraint rather than a SELECT first: two concurrent requests
    # would both pass a pre-check, but only one INSERT can win.
    lead = Lead(**data.model_dump())
    db.add(lead)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if EMAIL_UNIQUE_CONSTRAINT in str(exc.orig):
            raise LeadEmailConflictError(data.email) from exc
        raise
    return lead


def _escape_like(value: str) -> str:
    """Escape LIKE wildcards so user input matches literally (used with escape="\\")."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def list_leads(
    db: Session, *, q: str | None, status: LeadStatus | None, limit: int, offset: int
) -> tuple[list[Lead], int]:
    """Return one page of leads (newest first) and the total count matching the filters."""
    filters = []
    if q:
        pattern = f"%{_escape_like(q)}%"
        matches = [
            Lead.name.ilike(pattern, escape="\\"),
            Lead.email.ilike(pattern, escape="\\"),
        ]
        # Phones are stored normalized, so strip the same separators from the search
        # term: "98200 11223" must find "+919820011223".
        phone_q = PHONE_SEPARATORS.sub("", q)
        if phone_q:
            matches.append(Lead.phone.ilike(f"%{_escape_like(phone_q)}%", escape="\\"))
        filters.append(or_(*matches))
    if status is not None:
        filters.append(Lead.status == status)

    total = db.scalar(select(func.count()).select_from(Lead).where(*filters)) or 0
    items = db.scalars(
        select(Lead)
        .where(*filters)
        .order_by(Lead.created_at.desc(), Lead.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total


def update_lead_status(db: Session, lead_id: uuid.UUID, status: LeadStatus) -> Lead:
    """Set a lead's status. Any status may follow any other; the same status is a no-op."""
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise LeadNotFoundError(lead_id)
    lead.status = status
    db.commit()
    return lead
