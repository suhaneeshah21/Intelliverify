# backend/models/application.py

import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class ApplicationStatus(str, enum.Enum):
    submitted = "submitted"
    processing = "processing"
    verified = "verified"
    action_required = "action_required"
    under_review = "under_review"
    rejected = "rejected"


class DocumentType(str, enum.Enum):
    marksheet = "marksheet"
    gate_scorecard = "gate_scorecard"
    degree_certificate = "degree_certificate"
    caste_certificate = "caste_certificate"
    ews_certificate = "ews_certificate"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    verified = "verified"
    mismatch = "mismatch"
    reupload_requested = "reupload_requested"
    pending="pending"
    rejected = "rejected"


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Personal details
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(String(20), nullable=False)   # stored as string "YYYY-MM-DD"
    phone = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)        # General / OBC / SC / ST / EWS

    # Education details
    degree = Column(String(255), nullable=False)
    branch = Column(String(255), nullable=False)
    college = Column(String(500), nullable=False)
    graduation_year = Column(String(10), nullable=False)
    percentage = Column(String(10), nullable=False)
    gate_score = Column(String(10), nullable=True)       # optional
    gate_rank = Column(String(10), nullable=True)        # optional

    # Status
    status = Column(SAEnum(ApplicationStatus), default=ApplicationStatus.submitted, nullable=False)
    admin_remarks = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    candidate = relationship("User", back_populates="applications")
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=False)

    document_type = Column(SAEnum(DocumentType), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)   # UUID-renamed file on disk
    file_path = Column(String(1000), nullable=False)        # full path in uploads/

    status = Column(SAEnum(DocumentStatus), default=DocumentStatus.uploaded, nullable=False)
    confidence_score = Column(Float, nullable=True)         # filled after OCR — Week 3
    extracted_data = Column(Text, nullable=True)            # JSON string — filled after OCR
    mismatch_details = Column(Text, nullable=True)          # JSON string — filled after comparison
    reupload_reason = Column(Text, nullable=True)           # reason sent to candidate

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    application = relationship("Application", back_populates="documents")