from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from accounts.models import PermissionLevel, UserProfile
from accounting.models import Category, CategoryType, Entry, FiscalYear
from core.models import Organization

class DashboardViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
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
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="tresorier", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.client.login(username="tresorier", password="test123")

    def test_entry_list_loads(self):
        response = self.client.get(f"/entries/?fiscal_year={self.fy.pk}")
        self.assertEqual(response.status_code, 200)

class EntryCreateViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
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
