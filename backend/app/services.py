from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import LeadEmailConflictError
from app.models import Lead
from app.schemas import LeadCreate

EMAIL_UNIQUE_CONSTRAINT = "uq_leads_email"


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
    db.refresh(lead)
    return lead
