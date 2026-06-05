import os
import logging
from sqlalchemy.orm import Session


import redis
import json
from app.core.config import settings

from worker.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.application import Document, Application, DocumentStatus, ApplicationStatus
from app.models.preprocessor import preprocess_document
from app.models.ocr_engine import extract_text
from app.models.ner_extractor import extract_fields
from app.models.field_comparator import compare_fields
from app.models.confidence_scorer import score_results
from app.services.application_service import sync_application_status

logger = logging.getLogger(__name__)


def get_redis_client():
    """Synchronous Redis client for pub/sub publishing from Celery."""
    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True
    )

@celery_app.task(bind=True, max_retries=3)
def process_document(self,document_id:str):
  """
    The main pipeline task. Called after every document upload.
    bind=True means 'self' refers to the task instance — useful for retries.
    max_retries=3 means if it crashes, Celery retries up to 3 times automatically.
  """
  
  db=SessionLocal()
  try:

    document=db.query(Document).filter(Document.id==document_id).first()
    print(f"TASK RECEIVED: {document_id}") 

    document.status=DocumentStatus.processing
    db.commit()

    file_path=document.file_path
    doc_type=document.document_type

    application=db.query(Application).filter(Application.id==document.application_id).first()

    form_data = {
    "full_name": application.full_name,
    "category": application.category,
    "degree": application.degree,
    "branch": application.branch,
    "graduation_year": application.graduation_year,
    "percentage": application.percentage,
    "gate_score": application.gate_score,
    "gate_rank": application.gate_rank,
    }

    logger.info(f"Starting pipeline for document {document_id} | type: {doc_type}")

    # --- STEP 1: Preprocess ---
        # OpenCV cleans and normalizes the image/PDF
    preprocessed_path=preprocess_document(file_path,doc_type)

    # --- STEP 2: OCR ---
        # PaddleOCR reads all text from the cleaned document
    raw_text, ocr_confidence = extract_text(preprocessed_path, file_path)
    logger.info(f"OCR confidence: {ocr_confidence}")
    logger.info(f"RAW TEXT FULL:\n{raw_text[:3000]}")  # first 1000 chars
    # In tasks.py, after raw_text is extracted
    # for i, line in enumerate(raw_text.splitlines()):
    #     if line.strip():
    #         logger.info(f"LINE {i}: {line.strip()}")


    # --- STEP 3: NER / Field Extraction ---
        # spaCy + regex pulls structured fields from the raw text
        # e.g. {"name": "Rahul Sharma", "percentage": "78.4", "year": "2022"}

    extracted_fields=extract_fields(raw_text, doc_type)
    logger.info(f"EXTRACTED VALUES: {extracted_fields}")


     # --- STEP 4: Field Comparison ---
        # Compare extracted fields against what the candidate wrote in the form

    comparison_results = compare_fields(extracted_fields, form_data, doc_type)

    # --- STEP 5: Confidence Scoring ---
        # Combine OCR confidence + field match rates into one verdict
    final_score, verdict,issues = score_results(ocr_confidence, comparison_results)

    import json

    # extracted_data is a JSON string column — store extracted fields + raw text together
    document.extracted_data = json.dumps(extracted_fields)

    # mismatch_details is a JSON string column — store the field-by-field comparison
    document.mismatch_details = json.dumps(comparison_results)

    document.confidence_score = final_score

    if verdict == "verified":
        document.status=DocumentStatus.verified
    elif verdict=="low_confidence":
        document.status=DocumentStatus.reupload_requested
        document.reupload_reason=issues
    else:
        document.status=DocumentStatus.mismatch
    db.commit()

    sync_application_status(application,db)

    try:
            r = get_redis_client()
            update_payload = {
                "type": "document_processed",
                "application_id": str(application.id),
                "document_id": str(document_id),
                "document_status": document.status,        # "verified" / "mismatch" / "reupload_requested"
                "application_status": application.status,  # derived status
                "confidence_score": document.confidence_score,
            }
            r.publish("intelliverify:admin_updates", json.dumps(update_payload))
            logger.info(f"Published WS update for doc {document_id}")
    except Exception as pub_err:
        # Never let pub/sub failure crash the pipeline
        logger.warning(f"Redis publish failed (non-fatal): {pub_err}")

    logger.info(f"Pipeline complete for document {document_id} | verdict: {verdict}") 



  except Exception as exc:
        logger.exception(f"Pipeline failed for document {document_id}: {exc}")
        # Retry with exponential backoff: 60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

  finally:
      db.close()


