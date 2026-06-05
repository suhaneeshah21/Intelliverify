# ml/preprocessor.py

import cv2
import numpy as np
import os
import tempfile
import logging
from pdf2image import convert_from_path 
    
logger = logging.getLogger(__name__)

# Where we save cleaned images temporarily
PROCESSED_DIR = "uploads/processed"
os.makedirs(PROCESSED_DIR, exist_ok=True)


def preprocess_document(file_path: str, doc_type: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    # For PDFs we use pdfplumber directly — no image preprocessing needed
    if ext == ".pdf":
        return file_path  # return original path, won't be used anyway

    # Only preprocess actual image files
    return _preprocess_image(file_path, doc_type)


def _preprocess_pdf(file_path: str, doc_type: str) -> str:
    """
    Convert first page of PDF to image, then preprocess that image.
    We use the first page for most certificates.
    For multi-page docs, this can be extended later.
    """
    logger.info(f"Converting PDF to image: {file_path}")
    pages = convert_from_path(file_path, dpi=300, first_page=1, last_page=1)

    if not pages:
        raise ValueError(f"Could not extract pages from PDF: {file_path}")

    # Save first page as a temp PNG, then process it as an image
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=PROCESSED_DIR) as tmp:
        pages[0].save(tmp.name, "PNG")
        temp_path = tmp.name

    return _preprocess_image(temp_path, doc_type)


def _preprocess_image(file_path: str, doc_type: str) -> str:
    """
    The core OpenCV pipeline:
    1. Read image
    2. Convert to grayscale (removes colour noise)
    3. Deskew (fix tilt from camera angle)
    4. Denoise (remove scan artifacts)
    5. Binarize (convert to black/white — best for OCR)
    6. Save cleaned image
    """
    logger.info(f"Preprocessing image: {file_path}")
    img = cv2.imread(file_path)

    if img is None:
        raise ValueError(f"Could not read image at: {file_path}")

    # Step 1 — Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2 — Deskew (fix rotation caused by phone camera tilt)
    gray = _deskew(gray)

    # Step 3 — Denoise: removes salt-and-pepper artifacts from cheap scanners
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Step 4 — Binarize using Otsu's threshold
    # Otsu automatically finds the best black/white cutoff point
    binary = cv2.adaptiveThreshold(
    denoised, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 31, 10
    )
    # Step 5 — Morphological closing: fills tiny holes in characters
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    # Save the cleaned image to processed dir
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(PROCESSED_DIR, f"{base_name}_processed.png")
    cv2.imwrite(output_path, cleaned)

    logger.info(f"Preprocessed image saved to: {output_path}")
    return output_path


def _deskew(gray_img: np.ndarray) -> np.ndarray:
    """
    Only correct small, confident angles. Skip if angle seems wrong.
    """
    try:
        coords = np.column_stack(np.where(gray_img > 0))
        
        if len(coords) < 100:
            return gray_img
            
        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Only correct small angles — large angles mean deskew is wrong
        if abs(angle) > 10:
            return gray_img  # skip, don't rotate

        if abs(angle) < 0.5:
            return gray_img  # too small, not worth it

        h, w = gray_img.shape
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            gray_img, rotation_matrix, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )
        return rotated
        
    except Exception:
        return gray_img  # if anything fails, return original