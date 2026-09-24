"""Insert demo leads. Idempotent: leads whose email already exists are skipped.

Run: `uv run python -m scripts.seed` (uses DATABASE_URL from the environment or `.env`).
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db import get_sessionmaker
from app.models import EMAIL_UNIQUE_CONSTRAINT, Lead
from app.schemas import LeadStatus

# (name, email, phone, status, days ago). Phones are already in the normalized stored form.
DEMO_LEADS: list[tuple[str, str, str, LeadStatus, int]] = [
    ("Priya Sharma", "priya.sharma@finlytics.in", "+919820011223", LeadStatus.NEW, 0),
    ("Marcus Chen", "marcus@northwind.io", "+14155550142", LeadStatus.CONTACTED, 1),
    ("Aisha Okafor", "aisha.okafor@brightpath.ng", "+2348035550199", LeadStatus.QUALIFIED, 1),
    ("Tom Becker", "tom.becker@alpenwerk.de", "+493055501234", LeadStatus.LOST, 2),
    ("Elena Rossi", "elena@studiorossi.it", "+390655507788", LeadStatus.NEW, 2),
    ("Arjun Mehta", "arjun.mehta@kiteworks.in", "+919845012345", LeadStatus.CONTACTED, 3),
    ("Sofia Lindqvist", "sofia@nordlys.se", "+46855501234", LeadStatus.QUALIFIED, 4),
    ("Kenji Watanabe", "kenji.watanabe@hikari.jp", "+81355501234", LeadStatus.NEW, 5),
    ("Fatima Zahra", "fatima.zahra@atlasgrid.ma", "+212522555012", LeadStatus.CONTACTED, 6),
    ("Lucas Moreau", "lucas.moreau@veloce.fr", "+33155501234", LeadStatus.LOST, 7),
    ("Chloe Nguyen", "chloe@lotuslabs.vn", "+84285550123", LeadStatus.QUALIFIED, 8),
    ("Daniel Osei", "daniel.osei@goldcoast.gh", "+233302555012", LeadStatus.NEW, 9),
    ("Hannah Kowalski", "hannah@wislamedia.pl", "+48225550123", LeadStatus.CONTACTED, 10),
    ("Ravi Iyer", "ravi.iyer@carvaka.in", "+914425550123", LeadStatus.QUALIFIED, 12),
    ("Isabela Costa", "isabela@marazul.br", "+551135550123", LeadStatus.NEW, 13),
    ("Omar Haddad", "omar@haddadtrading.ae", "+97145550123", LeadStatus.LOST, 14),
    ("Mei Tanaka", "mei.tanaka@sakuradesign.jp", "+81665550123", LeadStatus.CONTACTED, 16),
    ("Jonas Berg", "jonas.berg@fjordtech.no", "+4722555012", LeadStatus.QUALIFIED, 18),
    ("Ananya Rao", "ananya.rao@quillhq.in", "+918025550123", LeadStatus.NEW, 19),
    ("Diego Alvarez", "diego@sierrasolar.mx", "+525555501234", LeadStatus.CONTACTED, 21),
    ("Grace Kim", "grace.kim@hanbitlabs.kr", "+82255501234", LeadStatus.LOST, 23),
    ("Nikolai Petrov", "nikolai@volgasoft.ru", "+74955550123", LeadStatus.NEW, 24),
    ("Leila Farouk", "leila.farouk@nileanalytics.eg", "+20225550123", LeadStatus.QUALIFIED, 26),
    ("Samuel Adeyemi", "samuel@lagoscloud.ng", "+2341555012", LeadStatus.CONTACTED, 28),
    ("Zoe Martin", "zoe.martin@harbourco.au", "+61295550123", LeadStatus.NEW, 30),
]


def seed(db: Session) -> int:
    """Insert missing demo leads; returns how many were inserted."""
    now = datetime.now(UTC)
    rows = [
        {
            "name": name,
            "email": email,
            "phone": phone,
            "status": status,
            "created_at": now - timedelta(days=days, hours=index),
        }
        for index, (name, email, phone, status, days) in enumerate(DEMO_LEADS)
    ]
    result = db.execute(
        insert(Lead)
        .values(rows)
        .on_conflict_do_nothing(constraint=EMAIL_UNIQUE_CONSTRAINT)
        .returning(Lead.id)
    )
    inserted = len(result.all())
    db.commit()
    return inserted


def main() -> None:
    with get_sessionmaker()() as db:
        inserted = seed(db)
    print(f"Inserted {inserted} demo leads ({len(DEMO_LEADS) - inserted} already present).")


if __name__ == "__main__":
    main()
