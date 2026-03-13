"""SQLAlchemy ORM models for the protocol management system."""
from datetime import datetime, date
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Date, DateTime,
    Boolean, ForeignKey, Table, Enum as SAEnum
)
from sqlalchemy.orm import DeclarativeBase, relationship, Session
import enum


class Base(DeclarativeBase):
    pass


# ── Enumerations ──────────────────────────────────────────────────────────────

class DocumentDirection(str, enum.Enum):
    INCOMING = "ΕΙΣΕΡΧΟΜΕΝΟ"
    OUTGOING = "ΕΞΕΡΧΟΜΕΝΟ"
    INTERNAL = "ΕΣΩΤΕΡΙΚΟ"


class DocumentPriority(str, enum.Enum):
    NORMAL = "ΚΑΝΟΝΙΚΟ"
    URGENT = "ΕΠΕΙΓΟΝ"
    VERY_URGENT = "ΑΜΕΣΩΣ ΕΠΕΙΓΟΝ"
    CONFIDENTIAL = "ΑΠΟΡΡΗΤΟ"
    TOP_SECRET = "ΑΥΣΤΗΡΩΣ ΑΠΟΡΡΗΤΟ"


class ProcessingStatus(str, enum.Enum):
    RECEIVED = "ΕΛΛΗΦΘΗ"
    PENDING = "ΣΕ ΕΚΚΡΕΜΟΤΗΤΑ"
    IN_PROGRESS = "ΣΕ ΕΞΕΛΙΞΗ"
    FORWARDED = "ΔΙΑΒΙΒΑΣΤΗΚΕ"
    COMPLETED = "ΔΙΕΚΠΕΡΑΙΩΘΗΚΕ"
    ARCHIVED = "ΑΡΧΕΙΟΘΕΤΗΘΗΚΕ"
    CANCELLED = "ΑΚΥΡΩΘΗΚΕ"


# ── Association tables ────────────────────────────────────────────────────────

protocol_recipients = Table(
    "protocol_recipients",
    Base.metadata,
    Column("protocol_id", Integer, ForeignKey("protocols.id"), primary_key=True),
    Column("contact_id", Integer, ForeignKey("contacts.id"), primary_key=True),
)

protocol_cc = Table(
    "protocol_cc",
    Base.metadata,
    Column("protocol_id", Integer, ForeignKey("protocols.id"), primary_key=True),
    Column("contact_id", Integer, ForeignKey("contacts.id"), primary_key=True),
)

recipient_list_members = Table(
    "recipient_list_members",
    Base.metadata,
    Column("list_id", Integer, ForeignKey("recipient_lists.id"), primary_key=True),
    Column("contact_id", Integer, ForeignKey("contacts.id"), primary_key=True),
)


# ── Parametric / Lookup tables ────────────────────────────────────────────────

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)
    employees = relationship("Employee", back_populates="department")
    created_at = Column(DateTime, default=datetime.utcnow)


class JobPosition(Base):
    __tablename__ = "job_positions"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    active = Column(Boolean, default=True)
    employees = relationship("Employee", back_populates="position")


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    position_id = Column(Integer, ForeignKey("job_positions.id"))
    email = Column(String(200))
    phone = Column(String(50))
    active = Column(Boolean, default=True)
    department = relationship("Department", back_populates="employees")
    position = relationship("JobPosition", back_populates="employees")
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name}"


class Contact(Base):
    """External senders / recipients."""
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    code = Column(String(20))
    name = Column(String(300), nullable=False)
    organization = Column(String(300))
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    phone = Column(String(50))
    fax = Column(String(50))
    email = Column(String(200))
    contact_type = Column(String(50))  # Φυσικό Πρόσωπο / Νομικό Πρόσωπο / Δημόσια Αρχή
    active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def display_name(self):
        if self.organization:
            return f"{self.name} ({self.organization})"
        return self.name


class RecipientList(Base):
    """Πίνακες αποδεκτών (distribution lists)."""
    __tablename__ = "recipient_lists"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)
    members = relationship("Contact", secondary=recipient_list_members)
    created_at = Column(DateTime, default=datetime.utcnow)


class FileFolder(Base):
    """Φάκελοι αρχείου."""
    __tablename__ = "file_folders"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True)
    name = Column(String(300), nullable=False)
    parent_id = Column(Integer, ForeignKey("file_folders.id"))
    description = Column(Text)
    active = Column(Boolean, default=True)
    children = relationship("FileFolder")
    protocols = relationship("Protocol", back_populates="folder")
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentTheme(Base):
    """Θέματα εγγράφων."""
    __tablename__ = "document_themes"
    id = Column(Integer, primary_key=True)
    code = Column(String(50))
    name = Column(String(300), nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)
    protocols = relationship("Protocol", back_populates="theme")


class DocumentType(Base):
    """Είδος εγγράφου (Απόφαση, Εγκύκλιος, Αίτηση, κλπ)."""
    __tablename__ = "document_types"
    id = Column(Integer, primary_key=True)
    code = Column(String(50))
    name = Column(String(200), nullable=False)
    direction = Column(String(20))  # INCOMING / OUTGOING / BOTH
    active = Column(Boolean, default=True)
    protocols = relationship("Protocol", back_populates="doc_type")


# ── Core Protocol table ───────────────────────────────────────────────────────

class Protocol(Base):
    __tablename__ = "protocols"

    id = Column(Integer, primary_key=True)

    # Protocol number
    protocol_number = Column(Integer, nullable=False, index=True)
    protocol_year = Column(Integer, nullable=False, index=True)
    protocol_full = Column(String(50), index=True)  # e.g. "1234/2026"

    direction = Column(SAEnum(DocumentDirection), nullable=False)
    priority = Column(SAEnum(DocumentPriority), default=DocumentPriority.NORMAL)
    status = Column(SAEnum(ProcessingStatus), default=ProcessingStatus.RECEIVED)

    # Dates
    protocol_date = Column(Date, nullable=False, default=date.today)
    received_date = Column(Date)
    deadline_date = Column(Date)

    subject = Column(Text, nullable=False)
    summary = Column(Text)

    # External reference (for incoming docs)
    ext_protocol_number = Column(String(100))
    ext_protocol_date = Column(Date)

    # Relations
    sender_contact_id = Column(Integer, ForeignKey("contacts.id"))
    sender_employee_id = Column(Integer, ForeignKey("employees.id"))
    handler_id = Column(Integer, ForeignKey("employees.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    folder_id = Column(Integer, ForeignKey("file_folders.id"))
    theme_id = Column(Integer, ForeignKey("document_themes.id"))
    doc_type_id = Column(Integer, ForeignKey("document_types.id"))

    # Related protocol
    related_protocol_id = Column(Integer, ForeignKey("protocols.id"))

    # ORM relationships
    sender_contact = relationship("Contact", foreign_keys=[sender_contact_id])
    sender_employee = relationship("Employee", foreign_keys=[sender_employee_id])
    handler = relationship("Employee", foreign_keys=[handler_id])
    department = relationship("Department")
    folder = relationship("FileFolder", back_populates="protocols")
    theme = relationship("DocumentTheme", back_populates="protocols")
    doc_type = relationship("DocumentType", back_populates="protocols")
    recipients = relationship("Contact", secondary=protocol_recipients)
    cc_contacts = relationship("Contact", secondary=protocol_cc)
    related_protocol = relationship("Protocol", remote_side=[id])
    attachments = relationship("Attachment", back_populates="protocol", cascade="all, delete-orphan")
    history = relationship("ProtocolHistory", back_populates="protocol", cascade="all, delete-orphan",
                           order_by="ProtocolHistory.created_at")
    email_logs = relationship("EmailLog", back_populates="protocol")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))

    def __repr__(self):
        return f"<Protocol {self.protocol_full} - {self.subject[:50]}>"


class Attachment(Base):
    """Files attached to a protocol entry."""
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500))
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50))   # pdf, docx, xlsx, jpg, scan, email, etc.
    file_size = Column(Integer)
    description = Column(Text)
    is_scan = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    protocol = relationship("Protocol", back_populates="attachments")


class ProtocolHistory(Base):
    """Audit trail / processing stages."""
    __tablename__ = "protocol_history"
    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"), nullable=False)
    action = Column(String(200), nullable=False)
    old_status = Column(String(100))
    new_status = Column(String(100))
    notes = Column(Text)
    employee_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    protocol = relationship("Protocol", back_populates="history")


class EmailLog(Base):
    """Record of emails sent for protocols."""
    __tablename__ = "email_logs"
    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey("protocols.id"))
    recipients = Column(Text)
    subject = Column(String(500))
    body = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    protocol = relationship("Protocol", back_populates="email_logs")


class ProtocolCounter(Base):
    """Yearly protocol number counter."""
    __tablename__ = "protocol_counters"
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False, unique=True)
    last_number = Column(Integer, default=0)
