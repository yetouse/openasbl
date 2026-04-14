from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from accounts.models import PermissionLevel, UserProfile
from accounting.models import Budget, AssetSnapshot, Category, CategoryType, Entry, FiscalYear, FiscalYearStatus
from core.models import Organization

class DashboardViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.client.login(username="tresorier", password="test123")

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

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
