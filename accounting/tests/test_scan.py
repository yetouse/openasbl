"""Tests for the ticket scanning view."""

import io
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from accounts.models import PermissionLevel, UserProfile
from accounting.models import Category, CategoryType, Entry, FiscalYear
from core.models import Organization


def _make_test_image():
    """Create a minimal PNG image for upload tests."""
    img = Image.new("RGB", (100, 50), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile("ticket.png", buf.read(), content_type="image/png")


class ScanTicketViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(
            user=self.user, organization=self.org,
            permission_level=PermissionLevel.GESTION,
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.category = Category.objects.create(
            organization=self.org, name="Achats",
            category_type=CategoryType.EXPENSE,
        )
        self.client.login(username="tresorier", password="test123")

    def test_scan_requires_login(self):
        self.client.logout()
        response = self.client.get("/scan/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_scan_requires_gestion_permission(self):
        reader = User.objects.create_user(username="lecteur", password="test123")
        UserProfile.objects.create(
            user=reader, organization=self.org,
            permission_level=PermissionLevel.LECTURE,
        )
        self.client.login(username="lecteur", password="test123")
        response = self.client.get("/scan/")
        self.assertEqual(response.status_code, 403)

    def test_scan_get_shows_upload_form(self):
        response = self.client.get("/scan/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scanner un ticket")
        self.assertContains(response, 'name="ticket_image"')

    def test_scan_no_open_fiscal_year(self):
        self.fy.status = "closed"
        self.fy.save()
        response = self.client.get("/scan/")
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/fiscal-years/")

    def test_scan_post_without_image(self):
        response = self.client.post("/scan/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "sélectionner une image")

    def test_scan_post_non_image_file(self):
        bad_file = SimpleUploadedFile("doc.txt", b"hello", content_type="text/plain")
        response = self.client.post("/scan/", {"ticket_image": bad_file})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "doit être une image")

    @patch("accounting.views.extract_from_image")
    def test_scan_post_image_shows_prefilled_form(self, mock_extract):
        mock_extract.return_value = {
            "amount": Decimal("25.50"),
            "date": date(2026, 3, 15),
            "description": "COLRUYT NAMUR",
            "raw_text": "COLRUYT NAMUR\n15/03/2026\nTOTAL 25,50 EUR",
        }
        image = _make_test_image()
        response = self.client.post("/scan/", {"ticket_image": image})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vérifier les données extraites")
        self.assertContains(response, "25.50")
        self.assertContains(response, "COLRUYT NAMUR")

    @patch("accounting.views.extract_from_image")
    def test_scan_post_image_shows_warning_when_partial(self, mock_extract):
        mock_extract.return_value = {
            "amount": None,
            "date": None,
            "description": "",
            "raw_text": "unreadable",
        }
        image = _make_test_image()
        response = self.client.post("/scan/", {"ticket_image": image})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pas pu être extraits")

    def test_scan_submit_creates_entry(self):
        response = self.client.post("/scan/", {
            "fiscal_year": self.fy.pk,
            "category": self.category.pk,
            "date": "2026-03-15",
            "amount": "25.50",
            "description": "COLRUYT NAMUR",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entry.objects.count(), 1)
        entry = Entry.objects.first()
        self.assertEqual(entry.amount, Decimal("25.50"))
        self.assertEqual(entry.description, "COLRUYT NAMUR")
        self.assertEqual(entry.created_by, self.user)

    def test_scan_submit_and_scan_another(self):
        response = self.client.post("/scan/", {
            "fiscal_year": self.fy.pk,
            "category": self.category.pk,
            "date": "2026-03-15",
            "amount": "25.50",
            "description": "COLRUYT",
            "scan_another": "1",
        })
        self.assertRedirects(response, "/scan/")
        self.assertEqual(Entry.objects.count(), 1)

    def test_scan_submit_invalid_form(self):
        response = self.client.post("/scan/", {
            "fiscal_year": self.fy.pk,
            "category": self.category.pk,
            "date": "2026-03-15",
            "amount": "",  # missing
            "description": "Test",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Entry.objects.count(), 0)
