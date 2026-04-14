# OCR Ticket Scan — Design Spec

**Date:** 2026-04-14
**Status:** Approved

## Overview

Add a dedicated mobile-first page for scanning receipts/tickets. Users photograph a receipt, Tesseract OCR extracts key data (amount, date, description), and a pre-filled form lets them verify before creating an accounting entry.

## User Flow

1. User navigates to "Scanner un ticket" (link in navbar dropdown)
2. User takes a photo or selects an image (`accept="image/*"`, `capture="environment"` for smartphone camera)
3. Image is uploaded via POST to `/accounting/scan/`
4. Backend runs OCR extraction, returns pre-filled form
5. Form displays: amount, date, description (extracted), category (default: first expense category), fiscal year (current open)
6. User verifies, adjusts if needed, and submits
7. Entry is created with the scanned image saved as attachment
8. Success message with options: "Scanner un autre" or "Voir le journal"

## Technical Design

### New Files

- `accounting/ocr.py` — OCR extraction module
- `accounting/templates/accounting/scan_ticket.html` — scan page template

### Modified Files

- `accounting/views.py` — add `scan_ticket` view
- `accounting/urls.py` — add `/scan/` URL
- `requirements.txt` — add `pytesseract`, `Pillow`
- `templates/base.html` — add "Scanner un ticket" link in navbar
- `help/context.py` — add help text for scan page
- `help/templates/help/guide_asbl.html` — mention OCR capability
- `README.md` — add scan feature to feature list

### OCR Module (`accounting/ocr.py`)

```python
def extract_from_image(image_file) -> dict:
    """
    Extract ticket data from an image file.

    Returns:
        {
            "amount": Decimal or None,
            "date": date or None,
            "description": str,
            "raw_text": str,
        }
    """
```

**Processing pipeline:**

1. Open image with Pillow
2. Pre-process: convert to grayscale, enhance contrast (ImageEnhance)
3. Run Tesseract with French language (`lang='fra'`)
4. Parse raw text with regex:
   - **Amounts:** find all `\d{1,3}([. ]\d{3})*[.,]\d{2}` patterns, take the largest as total
   - **Dates:** find `\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}` patterns, parse and take the most recent valid date
   - **Description:** first non-empty line of the OCR text (typically the store name)
5. Return extracted dict

### View (`scan_ticket`)

- **GET:** Render upload form (image input only)
- **POST with image (no form data):** Run OCR, render pre-filled entry form with extracted data
- **POST with form data:** Validate and create Entry, save image as attachment
- Permission: `@require_permission(PermissionLevel.GESTION)`
- Login required (enforced by decorator)

Two-step POST distinguished by presence of `amount` field in POST data:
- No `amount` → step 1 (OCR extraction)
- Has `amount` → step 2 (entry creation)

### Template (`scan_ticket.html`)

**Step 1 — Upload:**
- Mobile-first card layout
- Large file input with camera icon
- `accept="image/*"` and `capture="environment"` attributes
- Submit button: "Analyser le ticket"
- Help button with contextual help

**Step 2 — Verify & Save:**
- Pre-filled form (same fields as entry_create: fiscal_year, category, date, amount, description)
- Image thumbnail preview
- Info alert if OCR couldn't extract some fields: "Certains champs n'ont pas pu etre extraits automatiquement."
- Buttons: "Enregistrer", "Scanner un autre", "Annuler"
- Category dropdown filtered to expense categories by default
- Type defaults to expense

### URL

```python
path("scan/", views.scan_ticket, name="scan_ticket"),
```

### Dependencies

**Python packages (requirements.txt):**
- `pytesseract>=0.3.10` — Python wrapper for Tesseract
- `Pillow>=10.0` — Image processing

**System packages (server):**
- `tesseract-ocr`
- `tesseract-ocr-fra`

Install on Hostinger VPS: `apt install tesseract-ocr tesseract-ocr-fra`

### Navigation

Add "Scanner un ticket" link in the navbar actions dropdown, with a camera icon (Bootstrap Icons or Unicode).

### Error Handling

- No text extracted: show empty form with warning "Aucun texte n'a pu etre extrait. Verifiez la qualite de l'image."
- Tesseract not installed: catch `TesseractNotFoundError`, show user-friendly error
- Invalid image file: show form error
- No open fiscal year: redirect with error message (same behavior as entry_create)

### Permissions

Same as entry creation: requires `PermissionLevel.GESTION` or higher.

## Testing

### Unit Tests (`accounting/tests/test_ocr.py`)

- `test_extract_amount_from_text` — regex finds correct total
- `test_extract_date_from_text` — regex finds and parses date
- `test_extract_description_from_text` — first line extraction
- `test_no_amount_found` — returns None
- `test_no_date_found` — returns None
- `test_multiple_amounts_takes_largest` — picks the total, not subtotals
- `test_extract_from_image` — full pipeline with a test image

### View Tests (`accounting/tests/test_scan.py`)

- `test_scan_requires_login` — redirects to login
- `test_scan_requires_permission` — LECTURE users get 403
- `test_scan_get_shows_upload_form` — step 1 renders
- `test_scan_post_image_shows_prefilled_form` — OCR extraction works
- `test_scan_post_form_creates_entry` — entry created with attachment
- `test_scan_no_open_fiscal_year` — proper error handling

## Out of Scope

- Automatic category detection (future enhancement)
- Batch upload of multiple tickets at once (future enhancement)
- PDF ticket support (image only for v1)
- Training custom OCR models
