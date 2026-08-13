"""Tests du redressement automatique des photos de tickets."""

import io

from django.test import TestCase
from PIL import Image, ImageDraw, ImageFont

from accounting.ocr import estimate_skew, extract_from_image

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

TICKET = """COLRUYT
Rue de Dave 100
5100 NAMUR

Farine 1kg           2,35
Sucre fin            1,89
Lait demi-ecreme     5,94
Cafe moulu 500g      7,49

TOTAL MARCHANDISES  17,67
A PAYER             17,67

13/08/2026  14:32
"""


def build_ticket(tilt=0):
    """Fabrique l'image d'un ticket, éventuellement penchée de `tilt` degrés."""
    image = Image.new("L", (620, 620), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, 22)
    y = 30
    for line in TICKET.split("\n"):
        draw.text((40, y), line, fill="black", font=font)
        y += 30
    if tilt:
        image = image.rotate(tilt, expand=True, fillcolor="white")
    return image


def as_upload(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


class EstimateSkewTest(TestCase):
    def test_straight_image_needs_no_correction(self):
        self.assertAlmostEqual(estimate_skew(build_ticket()), 0, delta=1)

    def test_detects_counter_clockwise_tilt(self):
        # L'image est tournée de +10°, la correction attendue est de -10°.
        self.assertAlmostEqual(estimate_skew(build_ticket(tilt=10)), -10, delta=1.5)

    def test_detects_clockwise_tilt(self):
        self.assertAlmostEqual(estimate_skew(build_ticket(tilt=-8)), 8, delta=1.5)


class TiltedTicketExtractionTest(TestCase):
    """Une photo prise à main levée est toujours un peu de travers."""

    def test_reads_amount_and_date_on_tilted_photo(self):
        data = extract_from_image(as_upload(build_ticket(tilt=10)))

        self.assertEqual(str(data["amount"]), "17.67")
        self.assertEqual(str(data["date"]), "2026-08-13")
