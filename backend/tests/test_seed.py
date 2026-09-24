from sqlalchemy import func, select

from app.db import get_sessionmaker
from app.models import Lead
from scripts.seed import DEMO_LEADS, seed


def test_seed_inserts_demo_leads_across_all_statuses_and_is_idempotent() -> None:
    with get_sessionmaker()() as db:
        first = seed(db)
        second = seed(db)
        total = db.scalar(select(func.count()).select_from(Lead))
        statuses = set(db.scalars(select(Lead.status).distinct()))

    assert first == len(DEMO_LEADS) >= 25
    assert second == 0
    assert total == len(DEMO_LEADS)
    assert {s.value for s in statuses} == {"new", "contacted", "qualified", "lost"}
