# backend/services/application_service.py

import uuid
import os
import shutil
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.application import Application, Document, DocumentType, ApplicationStatus
from app.schemas.schemas import ApplicationCreate


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB = 5



ACTIVE_STATUSES = [
    ApplicationStatus.submitted,
    ApplicationStatus.processing,
    ApplicationStatus.under_review,
    ApplicationStatus.action_required,
]




# backend/app/services/application_service.py

def sync_application_status(application, db):
    """Recalculate and save application status based on its documents."""
    docs = application.documents
    if not docs:
        return

    statuses = [d.status.value if hasattr(d.status, "value") else d.status for d in docs]

    if any(s == "rejected" for s in statuses):
        application.status = "rejected"
    elif any(s in ("reupload_requested", "mismatch", "processing", "uploaded") for s in statuses):
        application.status = "action_required"
    elif all(s == "verified" for s in statuses):
        application.status = "verified"
    else:
        application.status = "under_review"
    db.commit()


def create_application(db: Session, candidate_id: str, data: ApplicationCreate) -> Application:
    """Create a new application row. Documents are attached separately."""
    # One candidate, one active application at a time
    existing = db.query(Application).filter(
    Application.candidate_id == candidate_id,
    Application.status != ApplicationStatus.rejected
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have an active application. Please wait for it to be processed."
        )

    app = Application(
        candidate_id=candidate_id,
        **data.model_dump()
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def attach_document(
    db: Session,
    application_id: str,
    candidate_id: str,
    document_type: str,
    file: UploadFile
) -> Document:
    """Save uploaded file to disk and create a Document row."""
    # Verify application belongs to this candidate
    app = db.query(Application).filter(
        Application.id == application_id,
        Application.candidate_id == candidate_id
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Validate document type
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid document type: {document_type}")

    # Validate file extension
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Upload PDF, JPG, or PNG."
        )

    # Save file — rename to UUID to prevent collisions
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check file size after saving
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f} MB). Max allowed is {MAX_FILE_SIZE_MB} MB."
        )

    # Create Document row
    doc = Document(
        application_id=application_id,
        document_type=doc_type,
        original_filename=file.filename,
        stored_filename=stored_name,
        file_path=file_path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_application_by_id(db: Session, application_id: str, candidate_id: str = None) -> Application:
    """Fetch one application. If candidate_id provided, enforce ownership."""
    query = db.query(Application).filter(Application.id == application_id)
    if candidate_id:
        query = query.filter(Application.candidate_id == candidate_id)
    app = query.first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


def get_all_applications(db: Session) -> list[Application]:
    """Admin — fetch all applications, newest first."""
    return db.query(Application).order_by(Application.created_at.desc()).all()


def get_candidate_applications(db: Session, candidate_id: str) -> list[Application]:
    """Candidate — fetch only their own applications."""
    return db.query(Application).filter(
        Application.candidate_id == candidate_id
    ).order_by(Application.created_at.desc()).all()


def update_application_status(
    db: Session,
    application_id: str,
    new_status: str,
    admin_remarks: str = None
) -> Application:
    """Admin action — change status and optionally add remarks."""
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    try:
        app.status = ApplicationStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

    if admin_remarks:
        app.admin_remarks = admin_remarks

    db.commit()
    db.refresh(app)
    return app