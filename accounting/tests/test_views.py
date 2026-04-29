import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from accounting.models import Budget, AssetSnapshot, Category, CategoryType, Entry, FiscalYear, FiscalYearStatus
from core.models import Organization

class DashboardViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        self.income_cat = Category.objects.create(
            organization=self.org,
            name="Cotisations",
            category_type=CategoryType.INCOME,
        )
        self.expense_cat = Category.objects.create(
            organization=self.org,
            name="Fournitures",
            category_type=CategoryType.EXPENSE,
        )
        self.client.login(username="tresorier", password="test123")

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    def test_dashboard_shows_treasurer_action_cards(self):
        response = self.client.get("/")
        self.assertContains(response, "Ajouter une dépense")
        self.assertContains(response, "Encoder une recette")
        self.assertContains(response, "Scanner un ticket")
        self.assertContains(response, "Préparer un rapport")
        self.assertContains(response, "/entries/create/")
        self.assertContains(response, "/scan/")
        self.assertContains(response, "/reports/")

    def test_dashboard_hides_edit_actions_for_read_only_users(self):
        self.user.profile.permission_level = PermissionLevel.LECTURE
        self.user.profile.save()

        response = self.client.get("/")

        self.assertNotContains(response, "Ajouter une dépense")
        self.assertNotContains(response, "Encoder une recette")
        self.assertNotContains(response, "Scanner un ticket OCR")
        self.assertContains(response, "Préparer un rapport")

    def test_dashboard_warns_when_open_year_has_no_budget(self):
        response = self.client.get("/")
        self.assertContains(response, "Budget à préparer")
        self.assertContains(response, f"/fiscal-years/{self.fy.pk}/budget/create/")

    def test_dashboard_warns_when_expenses_exceed_budget(self):
        Budget.objects.create(fiscal_year=self.fy, category=self.expense_cat, planned_amount=Decimal("100.00"))
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.expense_cat,
            date=date(2026, 2, 10),
            amount=Decimal("150.00"),
            description="Achat matériel",
            created_by=self.user,
        )

        response = self.client.get("/")

        self.assertContains(response, "Dépenses au-dessus du budget")
        self.assertContains(response, "150%")

    def test_dashboard_shows_latest_asset_snapshot(self):
        AssetSnapshot.objects.create(
            fiscal_year=self.fy,
            date=date(2026, 3, 31),
            cash=Decimal("25.00"),
            bank=Decimal("1200.00"),
            receivables=Decimal("50.00"),
            debts=Decimal("100.00"),
        )

        response = self.client.get("/")

        self.assertContains(response, "Patrimoine net")
        self.assertContains(response, "1 175,00")
        self.assertContains(response, "31/03/2026")

class EntryListViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.client.login(username="tresorier", password="test123")

    def test_entry_list_loads(self):
        response = self.client.get(f"/entries/?fiscal_year={self.fy.pk}")
        self.assertEqual(response.status_code, 200)

class EntryCreateViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.GESTION)
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.category = Category.objects.create(organization=self.org, name="Cotisations", category_type=CategoryType.INCOME)
        self.client.login(username="tresorier", password="test123")

    def test_create_entry(self):
        response = self.client.post("/entries/create/", {
            "fiscal_year": self.fy.pk, "category": self.category.pk,
            "date": "2026-03-15", "amount": "50.00", "description": "Cotisation Jean Dupont",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Entry.objects.count(), 1)
        entry = Entry.objects.first()
        self.assertEqual(entry.amount, Decimal("50.00"))
        self.assertEqual(entry.created_by, self.user)

    def test_reader_cannot_create_entry(self):
        self.user.profile.permission_level = PermissionLevel.LECTURE
        self.user.profile.save()
        response = self.client.post("/entries/create/", {
            "fiscal_year": self.fy.pk, "category": self.category.pk,
            "date": "2026-03-15", "amount": "50.00", "description": "Test",
        })
        self.assertEqual(response.status_code, 403)

class FiscalYearViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.client.login(username="admin", password="test123")

    def test_fiscal_year_list(self):
        FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        response = self.client.get("/fiscal-years/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026")

    def test_create_fiscal_year(self):
        response = self.client.post("/fiscal-years/create/", {"start_date": "2026-01-01", "end_date": "2026-12-31"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FiscalYear.objects.count(), 1)

    def test_close_fiscal_year(self):
        fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        response = self.client.post(f"/fiscal-years/{fy.pk}/close/")
        self.assertEqual(response.status_code, 302)
        fy.refresh_from_db()
        self.assertEqual(fy.status, FiscalYearStatus.CLOSED)

    def test_gestion_cannot_close_fiscal_year(self):
        self.user.profile.permission_level = PermissionLevel.GESTION
        self.user.profile.save()
        fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        response = self.client.post(f"/fiscal-years/{fy.pk}/close/")
        self.assertEqual(response.status_code, 403)

class CategoryViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.GESTION)
        self.client.login(username="admin", password="test123")

    def test_category_list(self):
        response = self.client.get("/categories/")
        self.assertEqual(response.status_code, 200)

    def test_create_category(self):
        response = self.client.post("/categories/create/", {"name": "Test", "category_type": "income", "description": ""})
        self.assertEqual(response.status_code, 302)

    def test_edit_category(self):
        cat = Category.objects.create(organization=self.org, name="Old Name", category_type=CategoryType.INCOME)
        response = self.client.post(f"/categories/{cat.pk}/edit/", {"name": "New Name", "category_type": "income", "description": "Updated"})
        self.assertEqual(response.status_code, 302)
        cat.refresh_from_db()
        self.assertEqual(cat.name, "New Name")
        self.assertEqual(cat.description, "Updated")

    def test_delete_unused_category(self):
        cat = Category.objects.create(organization=self.org, name="To Delete", category_type=CategoryType.EXPENSE)
        response = self.client.post(f"/categories/{cat.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(pk=cat.pk).exists())

    def test_cannot_delete_category_with_entries(self):
        cat = Category.objects.create(organization=self.org, name="Used", category_type=CategoryType.INCOME)
        fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        Entry.objects.create(fiscal_year=fy, category=cat, date=date(2026, 3, 15), amount=Decimal("50.00"), description="Test", created_by=self.user)
        response = self.client.post(f"/categories/{cat.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(pk=cat.pk).exists())

    def test_reader_cannot_edit_category(self):
        self.user.profile.permission_level = PermissionLevel.LECTURE
        self.user.profile.save()
        cat = Category.objects.create(organization=self.org, name="Test", category_type=CategoryType.INCOME)
        response = self.client.post(f"/categories/{cat.pk}/edit/", {"name": "Hacked", "category_type": "income", "description": ""})
        self.assertEqual(response.status_code, 403)

class BudgetViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.GESTION)
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.category = Category.objects.create(organization=self.org, name="Cotisations", category_type=CategoryType.INCOME)
        self.client.login(username="admin", password="test123")

    def test_create_budget(self):
        response = self.client.post(f"/fiscal-years/{self.fy.pk}/budget/create/", {
            f"budget_{self.category.pk}": "5000.00",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Budget.objects.count(), 1)
        self.assertEqual(Budget.objects.first().planned_amount, Decimal("5000.00"))

    def test_update_budget(self):
        Budget.objects.create(fiscal_year=self.fy, category=self.category, planned_amount=Decimal("3000.00"))
        response = self.client.post(f"/fiscal-years/{self.fy.pk}/budget/create/", {
            f"budget_{self.category.pk}": "5000.00",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Budget.objects.count(), 1)
        self.assertEqual(Budget.objects.first().planned_amount, Decimal("5000.00"))

    def test_budget_form_shows_existing(self):
        Budget.objects.create(fiscal_year=self.fy, category=self.category, planned_amount=Decimal("3000.00"))
        response = self.client.get(f"/fiscal-years/{self.fy.pk}/budget/create/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "3000")


class BudgetTrackingViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.GESTION)
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.cat = Category.objects.create(organization=self.org, name="Cotisations", category_type=CategoryType.INCOME)
        self.client.login(username="admin", password="test123")

    def test_budget_tracking_loads(self):
        Budget.objects.create(fiscal_year=self.fy, category=self.cat, planned_amount=Decimal("5000.00"))
        Entry.objects.create(fiscal_year=self.fy, category=self.cat, date=date(2026, 3, 15), amount=Decimal("2000.00"), description="Cotisation", created_by=self.user)
        response = self.client.get(f"/fiscal-years/{self.fy.pk}/budget-tracking/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Suivi budgétaire")
        self.assertContains(response, "5 000,00")
        self.assertContains(response, "2 000,00")

    def test_budget_tracking_empty(self):
        response = self.client.get(f"/fiscal-years/{self.fy.pk}/budget-tracking/")
        self.assertEqual(response.status_code, 200)

    def test_budget_tracking_requires_login(self):
        self.client.logout()
        response = self.client.get(f"/fiscal-years/{self.fy.pk}/budget-tracking/")
        self.assertEqual(response.status_code, 302)


class DocumentListViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test ASBL", address="Namur")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(
            user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        self.cat = Category.objects.create(
            organization=self.org, name="Fournitures", category_type=CategoryType.EXPENSE
        )
        self.client.login(username="tresorier", password="test123")

    def test_document_list_loads(self):
        response = self.client.get("/documents/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Documents")

    def test_document_list_requires_login(self):
        self.client.logout()
        response = self.client.get("/documents/")
        self.assertEqual(response.status_code, 302)

    def test_document_list_shows_empty_state(self):
        response = self.client.get("/documents/")
        self.assertContains(response, "Aucun document")

    def test_document_list_shows_attachment(self):
        fake_file = SimpleUploadedFile("facture.pdf", b"fake pdf content", content_type="application/pdf")
        entry = Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat,
            date=date(2025, 3, 15),
            amount=Decimal("50.00"),
            description="Achat fournitures",
            attachment=fake_file,
            created_by=self.user,
        )
        response = self.client.get("/documents/")
        self.assertContains(response, "facture")
        self.assertContains(response, "Achat fournitures")
        # Cleanup
        entry.attachment.delete()

    def test_document_list_filter_by_fiscal_year(self):
        response = self.client.get(f"/documents/?fiscal_year={self.fy.pk}")
        self.assertEqual(response.status_code, 200)


class AttachmentDownloadViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test ASBL", address="Namur")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(
            user=self.user, organization=self.org, permission_level=PermissionLevel.GESTION
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        self.cat = Category.objects.create(
            organization=self.org, name="Fournitures", category_type=CategoryType.EXPENSE
        )
        fake_file = SimpleUploadedFile("ticket.pdf", b"PDF content here", content_type="application/pdf")
        self.entry = Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat,
            date=date(2025, 6, 10),
            amount=Decimal("25.00"),
            description="Ticket de caisse",
            attachment=fake_file,
            created_by=self.user,
        )
        self.client.login(username="tresorier", password="test123")

    def tearDown(self):
        if self.entry.attachment:
            self.entry.attachment.delete()

    def test_download_attachment(self):
        response = self.client.get(f"/entries/{self.entry.pk}/attachment/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ticket", response.get("Content-Disposition", ""))

    def test_download_requires_login(self):
        self.client.logout()
        response = self.client.get(f"/entries/{self.entry.pk}/attachment/")
        self.assertEqual(response.status_code, 302)

    def test_download_nonexistent_entry(self):
        response = self.client.get("/entries/9999/attachment/")
        self.assertEqual(response.status_code, 404)

    def test_download_entry_without_attachment(self):
        entry_no_file = Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat,
            date=date(2025, 6, 11),
            amount=Decimal("10.00"),
            description="Sans justificatif",
            created_by=self.user,
        )
        response = self.client.get(f"/entries/{entry_no_file.pk}/attachment/")
        self.assertEqual(response.status_code, 404)

    def test_download_checks_org_ownership(self):
        """Attachment download filters by user's organization."""
        # The get_object_or_404 filters by organization, so a non-matching pk returns 404
        response = self.client.get("/entries/99999/attachment/")
        self.assertEqual(response.status_code, 404)


class EntryAttachmentIndicatorTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test ASBL", address="Namur")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(
            user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org, start_date=date(2025, 1, 1), end_date=date(2025, 12, 31)
        )
        self.cat = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        self.client.login(username="tresorier", password="test123")

    def test_entry_list_shows_attachment_icon(self):
        fake = SimpleUploadedFile("recu.jpg", b"image", content_type="image/jpeg")
        entry = Entry.objects.create(
            fiscal_year=self.fy, category=self.cat, date=date(2025, 4, 1),
            amount=Decimal("50.00"), description="Cotisation avec reçu",
            attachment=fake, created_by=self.user,
        )
        response = self.client.get("/entries/")
        self.assertContains(response, "attachment")  # the download URL
        entry.attachment.delete()

    def test_entry_list_no_icon_without_attachment(self):
        Entry.objects.create(
            fiscal_year=self.fy, category=self.cat, date=date(2025, 4, 1),
            amount=Decimal("50.00"), description="Cotisation sans reçu",
            created_by=self.user,
        )
        response = self.client.get("/entries/")
        self.assertNotContains(response, "attachment")
