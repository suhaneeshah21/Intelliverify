# ml/ocr_engine.py

import pdfplumber
import logging
import os
import numpy as np
from paddleocr import PaddleOCR  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)

# Initialize PaddleOCR once at module load — loading it per-call is very slow.
# lang="en" for English. We can add "hi" later for Hindi support.
# use_angle_cls=True means it can read rotated text.
# use_gpu=False because most servers don't have a GPU.
_ocr_engine = None

def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False, show_log=False)
    return _ocr_engine


def extract_text(processed_image_path: str, original_file_path: str) -> tuple[str, float]:
    original_ext = os.path.splitext(original_file_path)[1].lower()

    # Always use pdfplumber for PDFs — even if text is garbled,
    # it's better than destroying the image with preprocessing
    if original_ext == ".pdf":
        logger.info(f"PDF detected, using pdfplumber: {original_file_path}")
        text = _extract_with_pdfplumber(original_file_path)
        return text, 0.98

    # Only use PaddleOCR for actual image files
    logger.info(f"Image file detected, using PaddleOCR: {processed_image_path}")
    return _extract_with_paddleocr(processed_image_path)


def _is_digital_pdf(file_path: str) -> bool:
    """
    Check if PDF has a clean, usable text layer.
    We check two things: text exists AND it contains recognizable English words.
    A corrupted Hindi scan with a bad text layer will fail the second check.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            if pdf.pages:
                text = pdf.pages[0].extract_text()
                if not text or len(text.strip()) < 20:
                    return False
                
                # Count recognizable English words (3+ letter, all alpha)
                words = [w for w in text.split() if w.isalpha() and len(w) >= 3]
                total_tokens = len(text.split())
                
                if total_tokens == 0:
                    return False
                
                # If less than 30% of tokens are clean English words, treat as scanned
                english_ratio = len(words) / total_tokens
                return english_ratio >= 0.30
                
    except Exception:
        pass
    return False


def _extract_with_pdfplumber(file_path: str) -> str:
    """
    Extract text from all pages of a digital PDF.
    pdfplumber preserves layout reasonably well.
    """
    full_text = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text=page.extract_text()
                if page_text:
                  full_text.append(page_text)
    except Exception as e:
        logger.error(f"pdfplumber failed on {file_path}: {e}")
        return ""

    return "\n".join(full_text)


def _extract_with_paddleocr(image_path: str) -> tuple[str, float]:
    """
    Run PaddleOCR on a preprocessed image.
    Returns full concatenated text and the average confidence across all detected boxes.
    
    PaddleOCR returns a nested list:
    [
        [  # page
            [  # detected text box
                [[x1,y1],[x2,y2],[x3,y3],[x4,y4]],  # bounding box
                ("extracted text", confidence_score)  # text + confidence
            ],
            ...
        ]
    ]
    """
    try:
        result = _get_ocr_engine.ocr(image_path, cls=True)

        if not result or not result[0]:
            logger.warning(f"PaddleOCR returned no results for: {image_path}")
            logger.info(f"Image exists: {os.path.exists(image_path)}")
            return "", 0.0

        lines = []
        confidences = []

        for line in result[0]:
            text, confidence = line[1]
            if text.strip():
                lines.append(text.strip())
                confidences.append(confidence)

        full_text = "\n".join(lines)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        logger.info(f"OCR complete. Lines: {len(lines)}, Avg confidence: {avg_confidence:.3f}")
        return full_text, avg_confidence

    except Exception as e:
        logger.error(f"PaddleOCR failed on {image_path}: {e}")
        return "", 0.0