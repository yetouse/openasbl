"""Tests for OCR extraction module."""

import io
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from PIL import Image

from accounting.ocr import (
    extract_amount,
    extract_date,
    extract_description,
    extract_from_image,
    preprocess_image,
)


class ExtractAmountTest(TestCase):
    """Tests for amount extraction from OCR text."""

    def test_simple_amount(self):
        text = "TOTAL 14,50 EUR"
        self.assertEqual(extract_amount(text), Decimal("14.50"))

    def test_amount_with_dot_decimal(self):
        text = "Total: 25.99"
        self.assertEqual(extract_amount(text), Decimal("25.99"))

    def test_large_amount(self):
        text = "TOTAL TTC 1 234,56"
        self.assertEqual(extract_amount(text), Decimal("1234.56"))

    def test_multiple_amounts_takes_largest(self):
        text = """Article 1    5,00
Article 2   12,50
TVA          3,68
TOTAL       21,18"""
        self.assertEqual(extract_amount(text), Decimal("21.18"))

    def test_no_amount_found(self):
        text = "Merci de votre visite"
        self.assertIsNone(extract_amount(text))

    def test_amount_with_thousands_separator(self):
        text = "Montant: 2.500,00 EUR"
        self.assertEqual(extract_amount(text), Decimal("2500.00"))

    def test_zero_amount_ignored(self):
        text = "Remise 0,00\nTotal 15,00"
        self.assertEqual(extract_amount(text), Decimal("15.00"))


class ExtractDateTest(TestCase):
    """Tests for date extraction from OCR text."""

    def test_date_slash_format(self):
        text = "Date: 14/04/2026"
        self.assertEqual(extract_date(text), date(2026, 4, 14))

    def test_date_dash_format(self):
        text = "14-04-2026 Ticket"
        self.assertEqual(extract_date(text), date(2026, 4, 14))

    def test_date_dot_format(self):
        text = "14.04.2026"
        self.assertEqual(extract_date(text), date(2026, 4, 14))

    def test_date_two_digit_year(self):
        text = "Date 14/04/26"
        self.assertEqual(extract_date(text), date(2026, 4, 14))

    def test_no_date_found(self):
        text = "COLRUYT Namur"
        self.assertIsNone(extract_date(text))

    def test_invalid_date_ignored(self):
        text = "31/13/2026 invalid\n14/04/2026 valid"
        self.assertEqual(extract_date(text), date(2026, 4, 14))

    def test_multiple_dates_takes_most_recent(self):
        text = "01/01/2026\n14/04/2026"
        self.assertEqual(extract_date(text), date(2026, 4, 14))


class ExtractDescriptionTest(TestCase):
    """Tests for description extraction from OCR text."""

    def test_first_text_line(self):
        text = "COLRUYT\n14/04/2026\nArticle 1  5,00"
        self.assertEqual(extract_description(text), "COLRUYT")

    def test_skips_numeric_lines(self):
        text = "14/04/2026\n12:30\nCOLRUYT Namur"
        self.assertEqual(extract_description(text), "COLRUYT Namur")

    def test_empty_text(self):
        self.assertEqual(extract_description(""), "")

    def test_truncates_long_lines(self):
        text = "A" * 300
        result = extract_description(text)
        self.assertEqual(len(result), 200)

    def test_skips_short_lines(self):
        text = "AB\nCOLRUYT"
        self.assertEqual(extract_description(text), "COLRUYT")


class PreprocessImageTest(TestCase):
    """Tests for image preprocessing."""

    def test_converts_to_grayscale(self):
        img = Image.new("RGB", (100, 100), color="red")
        result = preprocess_image(img)
        self.assertEqual(result.mode, "L")

    def test_output_same_size(self):
        img = Image.new("RGB", (200, 150))
        result = preprocess_image(img)
        self.assertEqual(result.size, (200, 150))


class ExtractFromImageTest(TestCase):
    """Tests for the full extraction pipeline."""

    @patch("accounting.ocr.extract_text_from_image")
    def test_full_pipeline(self, mock_ocr):
        mock_ocr.return_value = "COLRUYT\n14/04/2026\nBeurre  3,50\nPain  2,00\nTOTAL  5,50"
        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        result = extract_from_image(buf)

        self.assertEqual(result["amount"], Decimal("5.50"))
        self.assertEqual(result["date"], date(2026, 4, 14))
        self.assertEqual(result["description"], "COLRUYT")
        self.assertIn("COLRUYT", result["raw_text"])

    @patch("accounting.ocr.extract_text_from_image")
    def test_no_data_extracted(self, mock_ocr):
        mock_ocr.return_value = ""
        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        result = extract_from_image(buf)

        self.assertIsNone(result["amount"])
        self.assertIsNone(result["date"])
        self.assertEqual(result["description"], "")
        self.assertEqual(result["raw_text"], "")
