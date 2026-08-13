"""
OCR extraction module for ticket/receipt scanning.

Uses Tesseract OCR to extract text from receipt images,
then parses amount, date, and description using regex patterns.
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def fix_orientation(image):
    """
    Corrige l'orientation de l'image via les métadonnées EXIF,
    puis via la détection automatique de Tesseract (OSD).
    """
    # 1. Correction EXIF (photos de téléphone souvent mal orientées)
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # 2. Détection d'orientation via Tesseract OSD
    try:
        osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
        angle = osd.get("rotate", 0)
        if angle != 0:
            image = image.rotate(-angle, expand=True)
    except Exception:
        pass  # OSD peut échouer sur des images très dégradées — on continue quand même

    return image


def _line_contrast(binary, angle):
    """
    Mesure à quel point les lignes de texte sont horizontales à cet angle.

    On moyenne chaque ligne de pixels : quand le texte est droit, le profil
    alterne franchement entre lignes écrites et interlignes vides. La somme
    des écarts au carré est donc maximale à l'angle correct.
    """
    rotated = binary.rotate(angle, resample=Image.BILINEAR, fillcolor=0)
    profile = list(rotated.resize((1, rotated.height)).getdata())
    return sum(
        (profile[i + 1] - profile[i]) ** 2 for i in range(len(profile) - 1)
    )


def estimate_skew(image, max_angle=12.0):
    """
    Estime l'angle de correction, en degrés, à passer à ``image.rotate()``
    pour redresser le texte.

    Tesseract ne corrige que les rotations d'un quart de tour ; or une photo
    prise à main levée est toujours penchée de quelques degrés, ce qui suffit
    à faire échouer la lecture.

    Returns:
        float : angle de correction, 0.0 si aucune inclinaison nette.
    """
    work = image.convert("L")
    if work.width > 800:
        work = work.resize((800, max(1, work.height * 800 // work.width)))

    # Texte en blanc sur fond noir : la rotation comble avec du noir, ce qui
    # n'ajoute aucun faux contraste sur les bords.
    binary = work.point(lambda pixel: 255 if pixel < 160 else 0)

    reference = _line_contrast(binary, 0.0)
    if reference <= 0:
        # Image uniforme ou sans texte : rien à redresser.
        return 0.0

    coarse = max(
        (a / 2 for a in range(int(-max_angle * 2), int(max_angle * 2) + 1, 4)),
        key=lambda a: _line_contrast(binary, a),
    )
    best = max(
        (coarse + step / 2 for step in range(-4, 5)),
        key=lambda a: _line_contrast(binary, a),
    )

    # Sans gain net, mieux vaut ne pas tourner l'image inutilement.
    if _line_contrast(binary, best) < reference * 1.05:
        return 0.0

    return round(best, 1)


def upscale_small_image(image, target_width=1200):
    """
    Tesseract lit mal les caractères de moins d'une vingtaine de pixels.
    Une photo recadrée ou compressée gagne à être agrandie avant lecture.
    """
    if image.width >= target_width:
        return image
    height = max(1, image.height * target_width // image.width)
    return image.resize((target_width, height), Image.LANCZOS)


def preprocess_image(image):
    """
    Pre-process image for better OCR results.

    Corrige l'orientation, redresse le texte, agrandit les petites images,
    puis renforce le contraste et la netteté.
    """
    image = fix_orientation(image)
    image = image.convert("L")

    angle = estimate_skew(image)
    if abs(angle) >= 0.5:
        image = image.rotate(
            angle, resample=Image.BICUBIC, expand=True, fillcolor=255
        )

    image = upscale_small_image(image)
    image = ImageOps.autocontrast(image)
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
    except UnidentifiedImageError:
        raise RuntimeError(
            "L'image n'a pas pu être lue. Format non supporté ou fichier corrompu."
        )

    image = preprocess_image(image)

    try:
        text = pytesseract.image_to_string(image, lang="fra")
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR n'est pas installé sur le serveur. "
            "Installez-le avec: sudo apt install tesseract-ocr tesseract-ocr-fra"
        )
    except pytesseract.TesseractError as e:
        raise RuntimeError(
            f"Erreur Tesseract lors de la lecture du ticket : {e}. "
            "Vérifiez que le paquet de langue française est installé "
            "(sudo apt install tesseract-ocr-fra)."
        )

    return text.strip()


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

    Cherche d'abord des mots-clés de total (À PAYER, TOTAL, etc.),
    sinon retourne le plus grand montant trouvé.

    Returns:
        Decimal or None
    """
    # 1. Chercher les mots-clés de total sur la même ligne
    total_keywords = [
        r"(?:à\s*payer|a\s*payer|total\s*(?:marchandises|ttc|tva\s*incluse)?|montant\s*total|net\s*à\s*payer)\s*[:\-]?\s*([\d\s.,]+)",
    ]
    for pattern in total_keywords:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = _normalize_amount(match.group(1).strip())
            try:
                amount = Decimal(raw)
                if amount > 0:
                    return amount
            except InvalidOperation:
                continue

    # 2. Fallback : plus grand montant trouvé
    patterns = [
        r"(\d{1,3}(?:[. ]\d{3})*[.,]\d{2})\b",
        r"\b(\d+[.,]\d{2})\b",
    ]
    amounts = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            raw = _normalize_amount(match.group(1))
            try:
                amount = Decimal(raw)
                if 0 < amount < 10000:  # sanity check
                    amounts.append(amount)
            except InvalidOperation:
                continue

    return max(set(amounts)) if amounts else None


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

    Cherche d'abord des noms de magasins connus ou des patterns
    typiques (ligne en majuscules courte, nom de ville, etc.).
    Sinon prend la première ligne lisible.

    Returns:
        str (may be empty)
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 1. Chercher des noms de magasins/enseignes connus
    known_stores = [
        "colruyt", "delhaize", "carrefour", "lidl", "aldi", "proxy",
        "spar", "okay", "cora", "match", "louis delhaize", "albert heijn",
        "action", "brico", "ikea", "fnac", "media markt", "decathlon",
        "shell", "q8", "total", "texaco",
    ]
    for line in lines[:20]:  # chercher dans les 20 premières lignes
        line_lower = line.lower()
        for store in known_stores:
            if store in line_lower:
                # Nettoyer et retourner
                clean = re.sub(r'[^\w\s&.\'-]', ' ', line).strip()
                if len(clean) >= 3:
                    return clean[:200]

    # 2. Prendre la première ligne qui ressemble à un nom propre
    # (uppercase, pas que des chiffres, longueur raisonnable)
    for line in lines[:15]:
        if re.match(r"^[^\d]{3,}", line) and not re.match(r"^[a-z]", line):
            if not re.match(r"^[\d/.:\-,€$ ]+$", line) and len(line) >= 3:
                clean = re.sub(r'[^\w\s&.\'-]', ' ', line).strip()
                if len(clean) >= 3:
                    return clean[:200]

    # 3. Fallback : première ligne non vide non numérique
    for line in lines:
        if not re.match(r"^[\d/.:\-,€$ ]+$", line) and len(line) >= 3:
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
