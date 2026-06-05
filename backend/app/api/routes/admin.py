
from sqlalchemy.orm import Session
import json

from fastapi import APIRouter, Depends,HTTPException
from typing import List
from worker.tasks import process_document
from app.models.application import DocumentStatus

from datetime import datetime, timedelta, timezone
from sqlalchemy import func, cast, Date

from fastapi.responses import StreamingResponse
from io import BytesIO
from app.services.report_service import generate_application_report

from app.api.deps import get_current_user, require_admin, require_candidate,get_db
from app.models.user import User
from app.models.application import ApplicationStatus
from app.schemas.schemas import ApplicationCreate, ApplicationResponse
from app.services import application_service
from app.services.application_service import sync_application_status
from app.models.application import Application, Document

router = APIRouter(prefix="/admin", tags=["admin"])



# ── helper: recompute application status from its documents ────────────────



@router.get("/all", response_model=List[ApplicationResponse])
def admin_get_all_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin views every application across all candidates."""
    apps = application_service.get_all_applications(db)
    return [ApplicationResponse.from_orm_safe(a) for a in apps]





@router.get("/stats/summary")
def get_stats_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    # --- Applications by status ---
    status_counts = (
        db.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )
    by_status = {status.value: count for status, count in status_counts}

    # --- Total applications ---
    total = sum(by_status.values())

    # --- Documents by type and verdict ---
    # verdict = "verified" | "mismatch" | "other"
    doc_type_stats = (
        db.query(Document.document_type, Document.status, func.count(Document.id))
        .group_by(Document.document_type, Document.status)
        .all()
    )

    by_document_type = {}
    for doc_type, doc_status, count in doc_type_stats:
        if doc_type not in by_document_type:
            by_document_type[doc_type] = {"verified": 0, "mismatch": 0, "other": 0}
        status_val = doc_status.value
        if status_val == "verified":
            by_document_type[doc_type]["verified"] += count
        elif status_val == "mismatch":
            by_document_type[doc_type]["mismatch"] += count
        else:
            by_document_type[doc_type]["other"] += count

    # --- Submissions over last 30 days ---
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    daily_counts = (
        db.query(
            cast(Application.created_at, Date).label("date"),
            func.count(Application.id).label("count"),
        )
        .filter(Application.created_at >= thirty_days_ago)
        .group_by(cast(Application.created_at, Date))
        .order_by(cast(Application.created_at, Date))
        .all()
    )
    submissions_over_time = [
        {"date": str(row.date), "count": row.count}
        for row in daily_counts
    ]

    return {
        "total": total,
        "by_status": by_status,
        "by_document_type": by_document_type,
        "submissions_over_time": submissions_over_time,
    }




@router.post("/documents/{document_id}/action")
def document_action(
    document_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    action = payload.get("action")  # "approve", "reject", "clarify"
    reason = payload.get("reason", "")

    if action not in ("approve", "reject", "clarify"):
        raise HTTPException(status_code=400, detail="Invalid action")

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    

    if action == "approve":
        doc.status = DocumentStatus.verified
        doc.reupload_reason = None
    elif action == "reject":
        doc.status = DocumentStatus.rejected
        doc.reupload_reason = reason
    elif action == "clarify":
        doc.status = DocumentStatus.reupload_requested
        doc.reupload_reason = reason

    db.commit()
    sync_application_status(doc.application, db)

    return {"message": f"Document {action}d", "document_id": document_id}







@router.post("/{application_id}/reject")
def admin_reject_application(
    application_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin rejects the entire application with a reason."""
    reason = payload.get("reason", "Application rejected by admin.")
    app = application_service.get_application_by_id(db, application_id)
    app.status = "rejected"
    app.admin_remarks = reason
    # Also mark all non-verified documents as rejected
    

    for doc in app.documents:
        if doc.status != DocumentStatus.verified:
            doc.status = DocumentStatus.rejected
            doc.reupload_reason = reason
    db.commit()
    return {"message": "Application rejected"}

    



# ── GET /admin/applications/{id} ───────────────────────────────────────────
@router.get("/{application_id}")
def get_application_detail(
    application_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    # Build document list — parse JSON strings back into dicts
    documents = []
    for doc in application.documents:
        extracted = {}
        mismatches = {}

        if doc.extracted_data:
            try:
                extracted = json.loads(doc.extracted_data)
            except (json.JSONDecodeError, TypeError):
                extracted = {}

        if doc.mismatch_details:
            try:
                mismatches = json.loads(doc.mismatch_details)
            except (json.JSONDecodeError, TypeError):
                mismatches = {}

        documents.append({
            "id": doc.id,
            "document_type": doc.document_type,
            "status": doc.status,
            "confidence_score": doc.confidence_score,
            "extracted_data": extracted,
            "mismatch_details": mismatches,
            "reupload_reason": doc.reupload_reason,
            "file_path": doc.file_path,
        })

    return {
        "id": application.id,
        "status": application.status,
        "submitted_at": application.created_at,
        # ── form fields ──
        "form_data": {
            "full_name": application.full_name,
            "date_of_birth": str(application.date_of_birth) if application.date_of_birth else None,
            "phone": application.phone,
            "category": application.category,
            "degree": application.degree,
            "branch": application.branch,
            "college": application.college,
            "graduation_year": application.graduation_year,
            "percentage": application.percentage,
            "gate_score": application.gate_score,
            "gate_rank": application.gate_rank,
        },
        "documents": documents,
        "candidate": {
        "id": str(application.candidate.id),
        "name": application.candidate.full_name,
        "email": application.candidate.email,
        }
    }



@router.get("/{application_id}/report")
def download_application_report(
    application_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    ):
    try:
        pdf_bytes = generate_application_report(db, application_id)
    except Exception as e:
        import traceback
        traceback.print_exc()          # prints full error to uvicorn terminal
        raise HTTPException(status_code=500, detail=str(e))

    filename = f"intelliverify_application_{application_id}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
