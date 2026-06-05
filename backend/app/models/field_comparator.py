# ml/field_comparator.py

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Fields to compare per document type.
# Maps doc_type → list of (extracted_field_key, form_field_key) tuples.
FIELD_MAPPING = {
    "marksheet": [
        ("candidate_name", "full_name"),
        ("percentage", "percentage"),
        ("year_of_passing", "graduation_year"),
    ],
    "gate_scorecard": [
        ("candidate_name", "full_name"),
        ("gate_score", "gate_score"),
        ("gate_rank", "gate_rank"),
    ],
    "degree_certificate": [
        ("candidate_name", "full_name"),
        ("degree", "degree"),
        ("branch", "branch"),
        ("year_of_passing", "graduation_year"),
    ],
    "caste_certificate": [
        ("candidate_name", "full_name"),
        ("category", "category"),
    ],
}


def compare_fields(
    extracted: dict,
    form_data: dict,
    doc_type: str,
) -> list[dict]:
    """
    Returns a list of comparison results, one per field.
    Each result looks like:
    {
        "field": "candidate_name",
        "extracted_value": "Rahul Sharma",
        "form_value": "Rahul Kumar Sharma",
        "match": "partial",       # "match", "partial", "mismatch", "missing"
        "similarity": 0.67
    }
    """
    fields_to_check = FIELD_MAPPING.get(doc_type, [])
    results = []

    for extracted_key, form_key in fields_to_check:
        extracted_val = extracted.get(extracted_key)
        form_val = form_data.get(form_key)

        result = _compare_single_field(extracted_key, extracted_val, form_val)
        results.append(result)

    return results


def _compare_single_field(
    field_name: str,
    extracted_value: Optional[str],
    form_value: Optional[str],
) -> dict:
    """
    Compare one field. Picks the right comparison strategy based on field type.
    """
    base = {
        "field": field_name,
        "extracted_value": extracted_value,
        "form_value": form_value,
    }

    # If either value is missing, we can't compare
    if not extracted_value or not form_value:
        return {**base, "match": "missing", "similarity": 0.0}

    # Choose comparison strategy
    if field_name == "candidate_name":
        match, similarity = _compare_names(extracted_value, form_value)

    elif field_name in ("percentage", "gate_score"):
        match, similarity = _compare_numbers(extracted_value, form_value)

    elif field_name in ("year_of_passing", "graduation_year", "tenth_year", "gate_rank"):
        match, similarity = _compare_exact(extracted_value, form_value)

    elif field_name == "category":
        match, similarity = _compare_category(extracted_value, form_value)

    else:
        # Default: normalized string comparison
        match, similarity = _compare_normalized(extracted_value, form_value)

    return {**base, "match": match, "similarity": similarity}


# ── Comparison strategies ─────────────────────────────────────────────────────

def _compare_names(extracted: str, form_val: str) -> tuple[str, float]:
    """
    Name comparison using token overlap.
    "Rahul Kumar Sharma" vs "Rahul Sharma" → partial match, 0.67
    Tolerates middle names and OCR inserting/dropping initials.
    """
    ext_tokens = set(_normalize_name(extracted).split())
    form_tokens = set(_normalize_name(form_val).split())

    if not ext_tokens or not form_tokens:
        return "missing", 0.0

    overlap = ext_tokens & form_tokens
    # Jaccard similarity: intersection / union
    similarity = len(overlap) / len(ext_tokens | form_tokens)

    if similarity >= 0.85:
        return "match", similarity
    elif similarity >= 0.5:
        return "partial", similarity
    else:
        return "mismatch", similarity


def _compare_numbers(extracted: str, form_val: str) -> tuple[str, float]:
    """
    Numeric comparison with tolerance.
    Handles: "78.4" vs "78.40" → match. "78.4" vs "79.1" → mismatch.
    """
    try:
        ext_num = float(re.sub(r"[^\d.]", "", extracted))
        form_num = float(re.sub(r"[^\d.]", "", form_val))
        diff = abs(ext_num - form_num)

        if diff <= 0.1:
            return "match", 1.0
        elif diff <= 1.0:
            # Small difference — might be rounding or OCR decimal error
            return "partial", 0.7
        else:
            return "mismatch", 0.0

    except ValueError:
        return "missing", 0.0


def _compare_exact(extracted: str, form_val: str) -> tuple[str, float]:
    """
    Exact match after normalizing whitespace and case.
    Used for years, roll numbers, ranks — these must be exact.
    """
    e = _clean(extracted)
    f = _clean(form_val)
    
    # Handle 2-digit year from marksheet e.g. "25" vs "2025"
    if len(e) == 2 and e.isdigit():
        e = "20" + e
    
    if e == f:
        return "match", 1.0
    return "mismatch", 0.0


def _compare_category(extracted: str, form_val: str) -> tuple[str, float]:
    """
    Category comparison: SC, ST, OBC, EWS, General.
    Normalize aliases: "obc-ncl" → "obc", "open" → "general".
    """
    ALIASES = {"obc-ncl": "obc", "open": "general", "gen": "general"}
    e = ALIASES.get(_clean(extracted), _clean(extracted))
    f = ALIASES.get(_clean(form_val), _clean(form_val))
    if e == f:
        return "match", 1.0
    return "mismatch", 0.0


def _compare_normalized(extracted: str, form_val: str) -> tuple[str, float]:
    """
    Generic normalized string comparison for fields like degree, branch.
    """
    e = _clean(extracted)
    f = _clean(form_val)
    if e == f:
        return "match", 1.0
    # Check if one contains the other (partial match)
    if e in f or f in e:
        return "partial", 0.7
    return "mismatch", 0.0


# ── Utilities ─────────────────────────────────────────────────────────────────

def _normalize_name(name: str) -> str:
    """Lowercase, remove punctuation like dots and dashes in names."""
    return re.sub(r"[^a-z\s]", "", name.lower()).strip()


def _clean(value: str) -> str:
    """Lowercase, collapse whitespace."""
    return re.sub(r"\s+", " ", value.lower()).strip()