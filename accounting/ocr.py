"""
OCR extraction module for ticket/receipt scanning.

Uses Tesseract OCR to extract text from receipt images,
then parses amount, date, and description using regex patterns.
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from PIL import Image, ImageEnhance, ImageFilter

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def preprocess_image(image):
    """
    Pre-process image for better OCR results.
    Converts to grayscale, enhances contrast, and sharpens.
    """
    image = image.convert("L")
    image = ImageEnhance.Contrast(image).enhance(2.0)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def extract_text_from_image(image_file):
    """
    Run Tesseract OCR on an image file.

    Args:
        image_file: A file-like object (e.g., UploadedFile).

    Returns:
        Extracted text as string, or empty string on failure.

    Raises:
        RuntimeError: If Tesseract is not installed.
    """
    if not TESSERACT_AVAILABLE:
        raise RuntimeError(
            "pytesseract n'est pas installé. "
            "Installez-le avec: pip install pytesseract"
        )

    try:
        image = Image.open(image_file)
        image = preprocess_image(image)
        text = pytesseract.image_to_string(image, lang="fra")
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR n'est pas installé sur le serveur. "
            "Installez-le avec: sudo apt install tesseract-ocr tesseract-ocr-fra"
        )
    except Exception:
        return ""


def _normalize_amount(raw):
    """
    Normalize a raw amount string to a Python decimal string.

    Handles European formats (1.234,56 or 1 234,56) and
    dot-decimal formats (25.99).
    """
    raw = raw.replace(" ", "")
    # If comma is present, it's the decimal separator (European)
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    else:
        # Dot only: check if it's a thousands separator or decimal
        # Thousands separator: dot followed by exactly 3 digits (e.g., 2.500)
        # Decimal separator: dot followed by exactly 2 digits (e.g., 25.99)
        if re.match(r"^\d{1,3}(\.\d{3})+$", raw):
            # All dots are thousands separators (e.g., 2.500 or 1.234.567)
            raw = raw.replace(".", "")
        # else: dot is decimal separator (e.g., 25.99) — keep as-is
    return raw


def extract_amount(text):
    """
    Extract the most likely total amount from OCR text.

    Looks for decimal numbers (e.g., 14,50 or 14.50 or 1 234,56).
    Returns the largest amount found (likely the total).

    Returns:
        Decimal or None
    """
    patterns = [
        r"(\d{1,3}(?:[. ]\d{3})*[.,]\d{2})\b",
        r"\b(\d+[.,]\d{2})\b",
    ]

    amounts = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            raw = match.group(1)
            raw = _normalize_amount(raw)
            try:
                amount = Decimal(raw)
                if amount > 0:
                    amounts.append(amount)
            except InvalidOperation:
                continue

    if not amounts:
        return None

    # Deduplicate and return the largest (most likely the total)
    return max(set(amounts))


def extract_date(text):
    """
    Extract a date from OCR text.

    Supports formats: dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy,
    and 2-digit year variants.

    Returns:
        date or None
    """
    pattern = r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})\b"

    candidates = []
    for match in re.finditer(pattern, text):
        day_str, month_str, year_str = match.groups()
        try:
            day = int(day_str)
            month = int(month_str)
            year = int(year_str)

            if year < 100:
                year += 2000

            d = date(year, month, day)
            # Sanity check: not in the far future or too old
            if date(2000, 1, 1) <= d <= date(2099, 12, 31):
                candidates.append(d)
        except (ValueError, OverflowError):
            continue

    if not candidates:
        return None

    # Return the most recent date (most likely the transaction date)
    return max(candidates)


def extract_description(text):
    """
    Extract a description from OCR text.

    Takes the first non-empty, non-numeric line as the store/vendor name.

    Returns:
        str (may be empty)
    """
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Skip lines that are only numbers, dates, or very short
        if re.match(r"^[\d/.\-,: €$%]+$", line):
            continue
        if len(line) < 3:
            continue
        # Clean up and truncate
        return line[:200]

    return ""


def extract_from_image(image_file):
    """
    Extract ticket data from an image file.

    Full pipeline: OCR → parse amount, date, description.

    Args:
        image_file: A file-like object (e.g., UploadedFile).

    Returns:
        dict with keys: amount, date, description, raw_text
    """
    raw_text = extract_text_from_image(image_file)

    return {
        "amount": extract_amount(raw_text),
        "date": extract_date(raw_text),
        "description": extract_description(raw_text),
        "raw_text": raw_text,
    }
