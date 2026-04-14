import io
import json
import zipfile
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase

from accounting.models import (
    AssetSnapshot,
    Budget,
    Category,
    CategoryType,
    Entry,
    FiscalYear,
)
from accounts.models import PermissionLevel, UserProfile
from core.backup import generate_export_zip, restore_from_zip, validate_import_zip
from core.models import Organization


class BackupTestMixin:
    """Create a full dataset for export/import testing."""

    def setUp(self):
        self.org = Organization.objects.create(
            name="Test ASBL",
            address="Rue de Test 1, 5000 Namur",
            enterprise_number="0123.456.789",
            email="test@asbl.be",
            phone="081123456",
        )
        self.admin = User.objects.create_user("admin", password="admin123")
        UserProfile.objects.create(
            user=self.admin,
            organization=self.org,
            permission_level=PermissionLevel.ADMIN,
        )
        self.user = User.objects.create_user(
            "comptable", password="compta123", first_name="Jean", last_name="Dupont"
        )
        UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            permission_level=PermissionLevel.GESTION,
        )
        self.cat_income = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        self.cat_expense = Category.objects.create(
            organization=self.org,
            name="Fournitures",
            category_type=CategoryType.EXPENSE,
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        self.entry = Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            date=date(2025, 3, 15),
            amount=Decimal("250.00"),
            description="Cotisation membre",
            created_by=self.user,
        )
        Budget.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            planned_amount=Decimal("1000.00"),
        )
        AssetSnapshot.objects.create(
            fiscal_year=self.fy,
            date=date(2025, 12, 31),
            cash=Decimal("500.00"),
            bank=Decimal("10000.00"),
        )


class ExportTest(BackupTestMixin, TestCase):
    def test_export_creates_valid_zip(self):
        zip_bytes = generate_export_zip()
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        self.assertIn("manifest.json", zf.namelist())
        self.assertIn("data.json", zf.namelist())

    def test_export_manifest_has_correct_fields(self):
        zip_bytes = generate_export_zip()
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        manifest = json.loads(zf.read("manifest.json"))
        self.assertEqual(manifest["version"], "1.0")
        self.assertEqual(manifest["organization"], "Test ASBL")
        self.assertIn("data_checksum", manifest)
        self.assertIn("exported_at", manifest)

    def test_export_data_contains_all_sections(self):
        zip_bytes = generate_export_zip()
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        data = json.loads(zf.read("data.json"))
        self.assertIn("organization", data)
        self.assertIn("users", data)
        self.assertIn("categories", data)
        self.assertIn("fiscal_years", data)
        self.assertIn("entries", data)
        self.assertIn("budgets", data)
        self.assertIn("asset_snapshots", data)

    def test_export_data_counts(self):
        zip_bytes = generate_export_zip()
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        data = json.loads(zf.read("data.json"))
        self.assertEqual(len(data["users"]), 2)
        self.assertEqual(len(data["categories"]), 2)
        self.assertEqual(len(data["fiscal_years"]), 1)
        self.assertEqual(len(data["entries"]), 1)
        self.assertEqual(len(data["budgets"]), 1)
        self.assertEqual(len(data["asset_snapshots"]), 1)

    def test_export_preserves_org_details(self):
        zip_bytes = generate_export_zip()
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        data = json.loads(zf.read("data.json"))
        org = data["organization"]
        self.assertEqual(org["name"], "Test ASBL")
        self.assertEqual(org["enterprise_number"], "0123.456.789")

    def test_export_preserves_entry_details(self):
        zip_bytes = generate_export_zip()
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        data = json.loads(zf.read("data.json"))
        entry = data["entries"][0]
        self.assertEqual(entry["description"], "Cotisation membre")
        self.assertEqual(entry["amount"], "250.00")
        self.assertEqual(entry["created_by_username"], "comptable")


class ValidateImportTest(BackupTestMixin, TestCase):
    def test_validate_valid_zip(self):
        zip_bytes = generate_export_zip()
        data, raw = validate_import_zip(io.BytesIO(zip_bytes))
        self.assertIn("organization", data)

    def test_validate_rejects_non_zip(self):
        with self.assertRaises(ValueError) as ctx:
            validate_import_zip(io.BytesIO(b"not a zip"))
        self.assertIn("ZIP valide", str(ctx.exception))

    def test_validate_rejects_missing_manifest(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("data.json", "{}")
        buf.seek(0)
        with self.assertRaises(ValueError) as ctx:
            validate_import_zip(buf)
        self.assertIn("manifest.json", str(ctx.exception))

    def test_validate_rejects_missing_data(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("manifest.json", "{}")
        buf.seek(0)
        with self.assertRaises(ValueError) as ctx:
            validate_import_zip(buf)
        self.assertIn("data.json", str(ctx.exception))

    def test_validate_rejects_corrupted_checksum(self):
        zip_bytes = generate_export_zip()
        # Tamper with data inside the zip
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        manifest = json.loads(zf.read("manifest.json"))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as new_zf:
            new_zf.writestr("manifest.json", json.dumps(manifest))
            new_zf.writestr("data.json", '{"tampered": true}')
        buf.seek(0)
        with self.assertRaises(ValueError) as ctx:
            validate_import_zip(buf)
        self.assertIn("checksum", str(ctx.exception))


class RestoreTest(BackupTestMixin, TestCase):
    def test_full_roundtrip(self):
        """Export then import, verify data is restored correctly."""
        zip_bytes = generate_export_zip()

        # Wipe and restore
        restore_from_zip(zip_bytes)

        # Verify organization
        org = Organization.objects.first()
        self.assertEqual(org.name, "Test ASBL")
        self.assertEqual(org.enterprise_number, "0123.456.789")

        # Verify users
        self.assertTrue(User.objects.filter(username="comptable").exists())
        profile = UserProfile.objects.get(user__username="comptable")
        self.assertEqual(profile.permission_level, PermissionLevel.GESTION)

        # Verify categories
        self.assertEqual(Category.objects.count(), 2)

        # Verify fiscal year
        self.assertEqual(FiscalYear.objects.count(), 1)
        fy = FiscalYear.objects.first()
        self.assertEqual(fy.start_date, date(2025, 1, 1))

        # Verify entries
        self.assertEqual(Entry.objects.count(), 1)
        entry = Entry.objects.first()
        self.assertEqual(entry.description, "Cotisation membre")
        self.assertEqual(entry.amount, Decimal("250.00"))

        # Verify budgets
        self.assertEqual(Budget.objects.count(), 1)

        # Verify asset snapshots
        self.assertEqual(AssetSnapshot.objects.count(), 1)
        snap = AssetSnapshot.objects.first()
        self.assertEqual(snap.cash, Decimal("500.00"))
        self.assertEqual(snap.bank, Decimal("10000.00"))

    def test_restore_replaces_existing_data(self):
        """Import should clear existing data first."""
        # Create extra data that should be wiped
        Category.objects.create(
            organization=self.org, name="Extra", category_type=CategoryType.INCOME
        )

        zip_bytes = generate_export_zip()  # Export now has 3 categories

        # Restore — should have exactly the exported count
        restore_from_zip(zip_bytes)
        self.assertEqual(Category.objects.count(), 3)


class ExportViewTest(BackupTestMixin, TestCase):
    def test_export_requires_admin(self):
        self.client.login(username="comptable", password="compta123")
        response = self.client.get("/core/export/")
        self.assertEqual(response.status_code, 403)

    def test_export_returns_zip(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get("/core/export/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("openasbl_backup_", response["Content-Disposition"])


class ImportViewTest(BackupTestMixin, TestCase):
    def test_import_requires_admin(self):
        self.client.login(username="comptable", password="compta123")
        response = self.client.get("/core/import/")
        self.assertEqual(response.status_code, 403)

    def test_import_get_renders_form(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get("/core/import/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Restaurer une sauvegarde")

    def test_import_post_with_valid_zip(self):
        zip_bytes = generate_export_zip()
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            "/core/import/",
            {"file": io.BytesIO(zip_bytes)},
            format="multipart",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Organization.objects.first().name, "Test ASBL")

    def test_import_post_with_invalid_file(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(
            "/core/import/",
            {"file": io.BytesIO(b"not a zip")},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)  # re-renders form with error
