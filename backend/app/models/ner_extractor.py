# ml/ner_extractor.py

import re
import spacy
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Load spaCy's small English model.
# This handles PERSON entity detection (candidate names).
# Run once: python -m spacy download en_core_web_sm
try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    _nlp = None


# ── Regex patterns ────────────────────────────────────────────────────────────
# These are designed to match common formats on Indian educational certificates.

PATTERNS = {
    # Matches: "GATE Score: 331"
    "gate_score": r"GATE\s*Score[:\s]*(\d{2,3}(?:\.\d{1,2})?)",

    # Matches: "All India Rank (AIR) in the test paper: 34140"
    "gate_rank": r"(?:All\s*India\s*Rank|AIR)[\s\S]{0,50}?(\d{4,6})",

    # Matches: "Computer Science and Information Technology (CS)" → extracts "CS"
    "gate_paper": r"Test\s*Paper[^(]*\(([A-Z]{2,4})\)",

    # Matches: "Registration Number: CS26S32111041"
    "roll_number": r"Registration\s*Number[:\s]*([A-Z0-9]{8,15})",

    # Matches: "Name of the Candidate: SUHANEE HRISHIKESH SHAH"
    "candidate_name": r"Name\s*of\s*the\s*Candidate[:\s]*([A-Z][A-Z\s]{3,40})",

    # Matches 4-digit years between 2000-2030
    "year_of_passing": r"\b(20[0-2]\d)\b",

    # Marksheet patterns
    "percentage": r"(?:percentage|marks obtained|cgpa|score)[^\d]*(\d{1,3}(?:\.\d{1,2})?)\s*(?:%|percent)?",

    # Degree
    "degree": r"\b(b\.?\s*tech|m\.?\s*tech|b\.?\s*e\.?|m\.?\s*e\.?|m\.?\s*sc|ph\.?\s*d|bachelor|master)\b",

    # Branch
    "branch": r"(?:branch|specialization|discipline|stream)[^\w]*([A-Za-z\s&]{5,40}?)(?:\n|,|\.|$)",

    # University
    "university": r"(?:university|institute|board)[^\n]*?([A-Z][A-Za-z\s]{5,50})(?:\n|,)",

    # Category
    "category": r"\b(sc|st|obc(?:-ncl)?|ews|general|open)\b",
}


def extract_fields(raw_text: str, doc_type: str) -> dict:
    if not raw_text or not raw_text.strip():
        return {}

    text_lower = raw_text.lower()
    extracted = {}

    if doc_type == "marksheet":
        extracted["candidate_name"] = _extract_name(raw_text)
        extracted.update(_extract_marksheet_fields(text_lower))

    elif doc_type == "gate_scorecard":
        # Name extracted inside _extract_gate_fields positionally
        extracted.update(_extract_gate_fields(raw_text))  # pass original, not lowercased

    elif doc_type == "degree_certificate":
        extracted["candidate_name"] = _extract_name(raw_text)
        extracted.update(_extract_degree_fields(text_lower))

    elif doc_type == "caste_certificate":
        extracted["candidate_name"] = _extract_name(raw_text)
        extracted.update(_extract_caste_fields(text_lower))

    extracted = {k: v for k, v in extracted.items() if v is not None}
    logger.info(f"Extracted fields for {doc_type}: {list(extracted.keys())}")
    return extracted

# ── Document-specific extraction functions ────────────────────────────────────

def _extract_marksheet_fields(text: str) -> dict:
    all_decimals = re.findall(r'\b(\d{2,3}\.\d{1,2})\b', text)
    percentage = None
    for num in all_decimals:
        val = float(num)
        if 30.0 <= val <= 100.0:
            percentage = num
            break
    
    if not percentage:
        percentage = _percentage_from_words(text)

    year = _regex_first(
        r"(?:january|february|march|april|may|june|july|august|"
        r"september|october|november|december)[\s\-]+(\d{2,4})",
        text
    )
    if year and len(year) == 2:
        year = "20" + year

    return {
        "percentage": percentage,
        "year_of_passing": year,
        "roll_number": _regex_first(r"\b([A-Za-z]\d{6,10})\b", text),
    }


def _extract_gate_fields(text: str) -> dict:
    """
    pdfplumber extracts GATE scorecard without labels — just raw values.
    We extract by line position and value shape.
    """
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    
    result = {
        "gate_score": None,
        "gate_rank": None,
        "gate_paper": None,
        "roll_number": None,
        "year_of_passing": None,
        "candidate_name": None,
    }


    for i, line in enumerate(lines):

        # Registration number — mix of letters and digits, 8-15 chars
        if re.match(r'^[A-Z0-9]{8,15}$', line) and re.search(r'[A-Z]', line) and re.search(r'\d', line):
            result["roll_number"] = line

        # Test paper — line containing "(CS)" or "(ME)" etc.
        paper_match = re.search(r'\(([A-Z]{2,4})\)$', line)
        if paper_match and len(line) > 10:
            result["gate_paper"] = paper_match.group(1)

        # GATE score — line with pattern "331 28.4" (score + marks on same line)
        score_match = re.match(r'^(\d{3}(?:\.\d{1,2})?)\s+\d{1,3}(?:\.\d{1,2})?$', line)
        if score_match:
            result["gate_score"] = score_match.group(1)

       
        # AIR rank — standalone 4-6 digit number, only take the first one
        rank_match = re.match(r'^(\d{4,6})$', line)
        if rank_match and result["gate_rank"] is None:  # ← add this check
            result["gate_rank"] = rank_match.group(1)

        # Year — 4 digit year in any line
        year_match = re.search(r'\b(20[2-9]\d)\b', line)  # 2020 and above only
        if year_match and not result["year_of_passing"]:
            result["year_of_passing"] = year_match.group(1)

        # Candidate name — all caps, 2+ words, appears in first 3 lines
        if i < 3 and re.match(r'^[A-Z][A-Z\s]{5,40}$', line) and len(line.split()) >= 2:
            if result["candidate_name"] is None:
                result["candidate_name"] = line

    return result


def _extract_degree_fields(text: str) -> dict:
    return {
        "degree": _regex_first(PATTERNS["degree"], text),
        "branch": _regex_first(PATTERNS["branch"], text),
        "year_of_passing": _regex_first(PATTERNS["year_of_passing"], text),
        "university": _regex_first(PATTERNS["university"], text),
    }


def _extract_caste_fields(text: str) -> dict:
    return {
        "category": _regex_first(PATTERNS["category"], text),
    }


# ── Helper functions ──────────────────────────────────────────────────────────

def _extract_name(raw_text: str) -> Optional[str]:
    # Try label-based first — most reliable
    label_match = re.search(
        r"candidate'?s?\s+full\s+name[^\n]*\n([A-Za-z][A-Za-z\s]{3,50})",
        raw_text,
        re.IGNORECASE,
    )
    if label_match:
        return label_match.group(1).strip()

    # Try "Name of the Candidate:" pattern
    name_match = re.search(
        r"name\s*of\s*the\s*candidate[:\s]*([A-Za-z][A-Za-z\s]{3,40})",
        raw_text,
        re.IGNORECASE,
    )
    if name_match:
        return name_match.group(1).strip()

    # Fall back to spaCy only if label-based fails
    if _nlp:
        doc = _nlp(raw_text[:1000])
        persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
        if persons:
            return max(persons, key=len)

    return None


def _name_fallback(text: str) -> Optional[str]:
    # Matches the line immediately after "CANDIDATE'S FULL NAME"
    match = re.search(
        r"candidate'?s?\s+full\s+name[^\n]*\n([A-Za-z][A-Za-z\s]{3,50})",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    
    # Generic fallback
    match = re.search(
        r"(?:name|student)[^\w]*([A-Z][a-zA-Z\s]{3,40})",
        text,
        re.IGNORECASE,
    )
    return match.group(1).strip() if match else None

def _regex_first(pattern: str, text: str) -> Optional[str]:
    """
    Apply a regex pattern and return the first captured group, cleaned up.
    Returns None if no match.
    """
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None




# Add this helper at the bottom of ner_extractor.py
WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100,
}

def _percentage_from_words(text: str) -> Optional[str]:
    # Fix 1 — total marks: look for standalone 3-digit number near "600" or after "/"
    # The marksheet shows "600" as max marks — find it directly
    total_match = re.search(r'\b([3-9]\d{2}|[1-9]\d{3})\b', text)
    # This finds first 3-4 digit number between 300-9999
    # But we need specifically the max marks (500, 600 etc.)
    # Better — look for the pattern "X 600" or just find 600 directly
    total_match = re.search(r'\b(500|600|700|800|900|1000)\b', text)
    logger.info(f"TOTAL MATCH V2: {total_match.group(1) if total_match else None}")

    # Fix 2 — written number: capture the full phrase including combined words
    written_match = re.search(
        r'((?:one|two|three|four|five|six|seven|eight|nine)\s*hundred'
        r'\s*(?:and\s*)?[a-z]*)',
        text, re.IGNORECASE
    )

    logger.info(f"WRITTEN MATCH V2: {written_match.group(1) if written_match else None}")
    ...

    if total_match and written_match:
        try:
            total = int(total_match.group(1))
            # written_match gives us "three hundred and sixtyseven"
            phrase = written_match.group(1).lower().replace('and', '').strip()
            words = phrase.split()
            obtained = _parse_written_number(words)
            if total > 0 and obtained > 0:
                pct = round((obtained / total) * 100, 2)
                if 30.0 <= pct <= 100.0:
                    return str(pct)
        except Exception as e:
            logger.info(f"Percentage calc failed: {e}")
    
    return None


def _parse_written_number(words: list) -> int:
    """Convert list of number words to integer."""
    result = 0
    current = 0
    for word in words:
        word = word.strip()
        if word == "hundred":
            current *= 100
        elif word in WORD_TO_NUM:
            current += WORD_TO_NUM[word]
        # Handle combined words like "sixtyseven"
        else:
            for tens in ["sixty", "seventy", "eighty", "ninety", "forty", "fifty", "thirty", "twenty"]:
                if word.startswith(tens):
                    remainder = word[len(tens):]
                    current += WORD_TO_NUM.get(tens, 0) + WORD_TO_NUM.get(remainder, 0)
                    break
    result += current
    return result