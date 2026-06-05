# backend/routers/applications.py

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from worker.tasks import process_document
import os
import shutil
import uuid
from app.api.deps import get_current_user, require_admin, require_candidate,get_db
from app.models.user import User
from app.models.application import ApplicationStatus
from app.schemas.schemas import ApplicationCreate, ApplicationResponse
from app.services import application_service
from app.models.application import Application, Document
from fastapi import HTTPException

router = APIRouter(prefix="/applications", tags=["applications"])


# ─── CANDIDATE ROUTES ────────────────────────────────────────────────────────

@router.post("/", response_model=ApplicationResponse)
def submit_application(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Candidate submits the application form (no files yet)."""
    app = application_service.create_application(db, str(current_user.id), data)
    return ApplicationResponse.from_orm_safe(app)


@router.post("/{application_id}/documents")
def upload_document(
    application_id: str,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Candidate uploads one document. Called once per document type."""
    doc = application_service.attach_document(
        db, application_id, str(current_user.id), document_type, file
    )
    process_document.delay(str(doc.id))

    return {
        "id": str(doc.id),
        "document_type": doc.document_type.value,
        "original_filename": doc.original_filename,
        "status": doc.status.value,
        "message": "Document uploaded successfully"
    }


@router.get("/my", response_model=List[ApplicationResponse])
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Candidate views all their own applications."""
    apps = application_service.get_candidate_applications(db, str(current_user.id))
    return [ApplicationResponse.from_orm_safe(a) for a in apps]


@router.get("/my/{application_id}", response_model=ApplicationResponse)
def get_my_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_candidate),
):
    """Candidate views one specific application (with documents)."""
    app = application_service.get_application_by_id(db, application_id, str(current_user.id))
    return ApplicationResponse.from_orm_safe(app)




@router.post("/{application_id}/documents/{document_id}/reupload")
async def reupload_document(
    application_id: str,
    document_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify ownership
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.candidate_id == current_user.id
    ).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.application_id == application_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Only allow reupload if status is reupload_requested
    if doc.status != "reupload_requested":
        raise HTTPException(
            status_code=400,
            detail="This document is not currently requesting a reupload."
        )

    # Save new file — overwrite old path with new unique name
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Reset document state for fresh processing
    doc.file_path = file_path
    doc.status = "uploaded"
    doc.extracted_data = None
    doc.mismatch_details = None
    doc.confidence_score = None
    doc.reupload_reason = None
    db.commit()

    # Re-queue the ML pipeline
    from worker.tasks import process_document
    process_document.delay(str(doc.id))

    return {"message": "Document reuploaded and queued for processing", "document_id": str(doc.id)}