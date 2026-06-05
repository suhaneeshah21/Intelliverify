# ml/confidence_scorer.py

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Thresholds — tune these as you test on real documents
OCR_LOW_CONFIDENCE_THRESHOLD = 0.65   # Below this → can't trust the read at all
FINAL_VERIFIED_THRESHOLD = 0.80        # Above this → auto-verified
FINAL_FLAG_THRESHOLD = 0.50            # Below this → definite mismatch, flag for admin


def score_results(
    ocr_confidence: float,
    comparison_results: list[dict],
) -> tuple[float, str, Optional[str]]:
    """
    Returns: (final_score, verdict, issues_string)
    
    verdict is one of:
      "verified"         — all good, no human review needed
      "low_confidence"   — OCR couldn't read the doc clearly, ask for reupload
      "mismatch_flagged" — clear mismatch found, needs admin review
    
    issues_string is a human-readable description of what went wrong,
    shown to the candidate (for reupload) or admin (for review).
    """

    # ── Check 1: Was OCR confident enough to trust the read? ──────────────────
    if ocr_confidence < OCR_LOW_CONFIDENCE_THRESHOLD:
        issues = _build_ocr_issue_message(ocr_confidence)
        logger.info(f"Low OCR confidence ({ocr_confidence:.2f}) → requesting reupload")
        return ocr_confidence, "low_confidence", issues

    # ── Check 2: Score the field comparisons ──────────────────────────────────
    field_score, mismatched_fields = _score_comparisons(comparison_results)

    # Combine OCR confidence (30% weight) with field match score (70% weight)
    # OCR being good is less important than the actual fields matching
    final_score = (0.30 * ocr_confidence) + (0.70 * field_score)

    logger.info(
        f"Final score: {final_score:.2f} | OCR: {ocr_confidence:.2f} | Fields: {field_score:.2f}"
    )

    # ── Check 3: Verdict based on final score ─────────────────────────────────
    if final_score >= FINAL_VERIFIED_THRESHOLD and not mismatched_fields:
        return final_score, "verified", None

    elif mismatched_fields:
        issues = _build_mismatch_message(mismatched_fields)
        logger.info(f"Mismatches found in: {[f['field'] for f in mismatched_fields]}")
        return final_score, "mismatch_flagged", issues

    else:
        # Score between thresholds — borderline, send to admin review
        issues = f"Verification confidence is low ({final_score:.0%}). Manual review required."
        return final_score, "mismatch_flagged", issues


def _score_comparisons(comparison_results: list[dict]) -> tuple[float, list[dict]]:
    """
    Convert field comparison results into a 0-1 score.
    Weights:
      match    → 1.0
      partial  → 0.6  (OCR may have slightly mangled the value)
      missing  → 0.4  (field not found in document — could be extraction failure)
      mismatch → 0.0
    
    Returns the average score and a list of fields that are mismatched.
    """
    SCORE_MAP = {"match": 1.0, "partial": 0.6, "missing": 0.4, "mismatch": 0.0}

    if not comparison_results:
        return 0.5, []  # No fields to compare — neutral score

    scores = []
    mismatches = []

    for result in comparison_results:
        match_status = result.get("match", "missing")
        score = SCORE_MAP.get(match_status, 0.0)
        scores.append(score)

        if match_status == "mismatch":
            mismatches.append(result)

    avg_score = sum(scores) / len(scores)
    return avg_score, mismatches


def _build_ocr_issue_message(ocr_confidence: float) -> str:
    """Human-readable message for the candidate when OCR confidence is low."""
    pct = int(ocr_confidence * 100)
    return (
        f"The uploaded document could not be read clearly (clarity: {pct}%). "
        "Please re-upload a clearer scan or photograph. Ensure good lighting, "
        "no shadows, and all text is fully visible."
    )


def _build_mismatch_message(mismatched_fields: list[dict]) -> str:
    """
    Build a message listing what mismatched.
    Admin sees both values. Candidate only sees field names (not values, for privacy).
    """
    lines = ["The following fields do not match your application form:"]
    for field in mismatched_fields:
        field_name = field["field"].replace("_", " ").title()
        extracted = field.get("extracted_value", "Not found")
        form_val = field.get("form_value", "Not provided")
        lines.append(f"  • {field_name}: Document shows '{extracted}', form says '{form_val}'")

    return "\n".join(lines)