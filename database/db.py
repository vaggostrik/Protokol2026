"""Database engine, session management, and helper queries."""
from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker, Session

from config.settings import DB_PATH
from database.models import (
    Base, Protocol, ProtocolCounter, DocumentDirection, RegistryType,
    ProcessingStatus, Department, JobPosition, Employee,
    Contact, RecipientList, FileFolder, DocumentTheme, DocumentType,
    Attachment, ProtocolHistory, EmailLog, AppUser, UserRole,
)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            connect_args={"check_same_thread": False},
            echo=False,
        )
    return _engine


def init_db():
    """Create all tables and seed default data."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    global _SessionLocal
    _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    _seed_defaults()


def get_session() -> Session:
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()


# ── Protocol number management ────────────────────────────────────────────────

# Short prefixes per registry type
REGISTRY_PREFIXES = {
    RegistryType.GENERAL:   "",
    RegistryType.CONSUMER:  "ΑΚ-",
    RegistryType.FINANCIAL: "ΟΥ-",
}


def next_protocol_number(session: Session, year: int,
                         registry_type: RegistryType = RegistryType.GENERAL) -> int:
    reg_val = registry_type.value if isinstance(registry_type, RegistryType) else registry_type
    counter = session.query(ProtocolCounter).filter_by(year=year, registry_type=reg_val).first()
    if counter is None:
        counter = ProtocolCounter(year=year, registry_type=reg_val, last_number=0)
        session.add(counter)
    counter.last_number += 1
    session.flush()
    return counter.last_number


def format_protocol_number(number: int, year: int, prefix: str = "",
                           registry_type: RegistryType = RegistryType.GENERAL) -> str:
    reg_prefix = REGISTRY_PREFIXES.get(registry_type, "")
    base = f"{number}/{year}"
    return f"{prefix}{reg_prefix}{base}" if prefix else f"{reg_prefix}{base}"


# ── User management ───────────────────────────────────────────────────────────

def authenticate_user(session: Session, username: str, password: str):
    """Return AppUser if credentials match, else None."""
    user = session.query(AppUser).filter_by(username=username, active=True).first()
    if user and user.check_password(password):
        from datetime import datetime
        user.last_login = datetime.utcnow()
        session.commit()
        return user
    return None


# ── Create protocol ───────────────────────────────────────────────────────────

def create_protocol(
    session: Session,
    direction: DocumentDirection,
    subject: str,
    protocol_date: Optional[date] = None,
    **kwargs,
) -> Protocol:
    today = protocol_date or date.today()
    year = today.year
    registry_type = kwargs.pop("registry_type", RegistryType.GENERAL)
    prefix = kwargs.pop("prefix", "")
    num = next_protocol_number(session, year, registry_type)
    full = format_protocol_number(num, year, prefix, registry_type)

    proto = Protocol(
        protocol_number=num,
        protocol_year=year,
        protocol_full=full,
        registry_type=registry_type,
        direction=direction,
        subject=subject,
        protocol_date=today,
        **kwargs,
    )
    session.add(proto)
    session.flush()

    # Initial history entry
    history = ProtocolHistory(
        protocol_id=proto.id,
        action="Καταχώρηση",
        new_status=proto.status.value if proto.status else None,
        notes=f"Αρχική καταχώρηση εγγράφου {full}",
    )
    session.add(history)
    return proto


# ── Search ────────────────────────────────────────────────────────────────────

def search_protocols(
    session: Session,
    keyword: str = "",
    direction: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sender_name: str = "",
    theme_id: Optional[int] = None,
    folder_id: Optional[int] = None,
    doc_type_id: Optional[int] = None,
    handler_id: Optional[int] = None,
    department_id: Optional[int] = None,
    year: Optional[int] = None,
    registry_type: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
):
    q = session.query(Protocol)

    if registry_type:
        q = q.filter(Protocol.registry_type == registry_type)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            Protocol.subject.ilike(like),
            Protocol.summary.ilike(like),
            Protocol.protocol_full.ilike(like),
            Protocol.ext_protocol_number.ilike(like),
        ))
    if direction:
        q = q.filter(Protocol.direction == direction)
    if status:
        q = q.filter(Protocol.status == status)
    if priority:
        q = q.filter(Protocol.priority == priority)
    if date_from:
        q = q.filter(Protocol.protocol_date >= date_from)
    if date_to:
        q = q.filter(Protocol.protocol_date <= date_to)
    if theme_id:
        q = q.filter(Protocol.theme_id == theme_id)
    if folder_id:
        q = q.filter(Protocol.folder_id == folder_id)
    if doc_type_id:
        q = q.filter(Protocol.doc_type_id == doc_type_id)
    if handler_id:
        q = q.filter(Protocol.handler_id == handler_id)
    if department_id:
        q = q.filter(Protocol.department_id == department_id)
    if year:
        q = q.filter(Protocol.protocol_year == year)
    if sender_name:
        like = f"%{sender_name}%"
        q = q.join(Contact, Protocol.sender_contact_id == Contact.id, isouter=True)
        q = q.filter(or_(
            Contact.name.ilike(like),
            Contact.organization.ilike(like),
        ))

    total = q.count()
    items = q.order_by(Protocol.protocol_year.desc(), Protocol.protocol_number.desc()) \
             .offset(offset).limit(limit).all()
    return items, total


# ── Default seed data ─────────────────────────────────────────────────────────

def _seed_defaults():
    with get_session() as s:
        # Document types
        if s.query(DocumentType).count() == 0:
            types = [
                ("ΑΙΤΗΣΗ", "Αίτηση", "INCOMING"),
                ("ΑΠΟΦΑΣΗ", "Απόφαση", "BOTH"),
                ("ΕΓΚΥΚΛΙΟΣ", "Εγκύκλιος", "INCOMING"),
                ("ΕΠΙΣΤΟΛΗ", "Επιστολή", "BOTH"),
                ("ΣΥΜΒΑΣΗ", "Σύμβαση", "BOTH"),
                ("ΔΙΑΒΙΒΑΣΤΙΚΟ", "Διαβιβαστικό", "BOTH"),
                ("ΓΝΩΜΟΔΟΤΗΣΗ", "Γνωμοδότηση", "BOTH"),
                ("ΥΠΟΜΝΗΜΑ", "Υπόμνημα", "INTERNAL"),
                ("ΕΣΩΤΕΡΙΚΟ", "Εσωτερικό σημείωμα", "INTERNAL"),
                ("ΕΚΘΕΣΗ", "Έκθεση", "BOTH"),
                ("ΠΡΑΚΤΙΚΟ", "Πρακτικό", "BOTH"),
                ("ΤΙΜΟΛΟΓΙΟ", "Τιμολόγιο", "INCOMING"),
                ("ΠΑΡΑΣΤΑΤΙΚΟ", "Παραστατικό", "INCOMING"),
            ]
            for code, name, direction in types:
                s.add(DocumentType(code=code, name=name, direction=direction))

        # Default admin user
        if s.query(AppUser).count() == 0:
            admin = AppUser(
                username="admin",
                full_name="Διαχειριστής",
                role=UserRole.ADMIN,
                active=True,
            )
            admin.set_password("admin123")
            s.add(admin)

        # Contact types seed
        if s.query(Contact).count() == 0:
            s.add(Contact(
                name="Άγνωστος Αποστολέας",
                code="UNKNOWN",
                contact_type="Φυσικό Πρόσωπο",
            ))

        s.commit()
