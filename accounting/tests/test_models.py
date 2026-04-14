from datetime import date
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from accounting.models import (AssetSnapshot, Budget, Category, CategoryType, Entry, FiscalYear, FiscalYearStatus)
from core.models import Organization

class FiscalYearModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")

    def test_create_fiscal_year(self):
        fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.assertEqual(fy.status, FiscalYearStatus.OPEN)
        self.assertEqual(str(fy), "2026-01-01 \u2192 2026-12-31")

    def test_end_date_after_start_date(self):
        fy = FiscalYear(organization=self.org, start_date=date(2026, 12, 31), end_date=date(2026, 1, 1))
        with self.assertRaises(ValidationError):
            fy.full_clean()

    def test_close_fiscal_year(self):
        fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        fy.status = FiscalYearStatus.CLOSED
        fy.save()
        self.assertEqual(fy.status, FiscalYearStatus.CLOSED)

class CategoryModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")

    def test_create_income_category(self):
        cat = Category.objects.create(organization=self.org, name="Cotisations membres", category_type=CategoryType.INCOME)
        self.assertEqual(str(cat), "Cotisations membres (Recette)")

    def test_create_expense_category(self):
        cat = Category.objects.create(organization=self.org, name="Entretien p\u00e9niche", category_type=CategoryType.EXPENSE)
        self.assertEqual(str(cat), "Entretien p\u00e9niche (D\u00e9pense)")

class EntryModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.category = Category.objects.create(organization=self.org, name="Cotisations", category_type=CategoryType.INCOME)
        self.user = User.objects.create_user(username="tresorier", password="test123")

    def test_create_entry(self):
        entry = Entry.objects.create(fiscal_year=self.fy, category=self.category, date=date(2026, 3, 15), amount=Decimal("50.00"), description="Cotisation annuelle \u2014 Jean Dupont", created_by=self.user)
        self.assertEqual(entry.amount, Decimal("50.00"))
        self.assertEqual(entry.entry_type, CategoryType.INCOME)

    def test_entry_date_within_fiscal_year(self):
        entry = Entry(fiscal_year=self.fy, category=self.category, date=date(2025, 6, 15), amount=Decimal("50.00"), description="Hors exercice", created_by=self.user)
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_entry_on_closed_fiscal_year(self):
        self.fy.status = FiscalYearStatus.CLOSED
        self.fy.save()
        entry = Entry(fiscal_year=self.fy, category=self.category, date=date(2026, 3, 15), amount=Decimal("50.00"), description="Test", created_by=self.user)
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_amount_must_be_positive(self):
        entry = Entry(fiscal_year=self.fy, category=self.category, date=date(2026, 3, 15), amount=Decimal("-10.00"), description="N\u00e9gatif", created_by=self.user)
        with self.assertRaises(ValidationError):
            entry.full_clean()

class BudgetModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        self.category = Category.objects.create(organization=self.org, name="Cotisations", category_type=CategoryType.INCOME)

    def test_create_budget(self):
        budget = Budget.objects.create(fiscal_year=self.fy, category=self.category, planned_amount=Decimal("5000.00"))
        self.assertEqual(budget.planned_amount, Decimal("5000.00"))

    def test_unique_budget_per_category_per_year(self):
        Budget.objects.create(fiscal_year=self.fy, category=self.category, planned_amount=Decimal("5000.00"))
        with self.assertRaises(Exception):
            Budget.objects.create(fiscal_year=self.fy, category=self.category, planned_amount=Decimal("6000.00"))

class AssetSnapshotModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.fy = FiscalYear.objects.create(organization=self.org, start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))

    def test_create_snapshot(self):
        snapshot = AssetSnapshot.objects.create(fiscal_year=self.fy, date=date(2026, 12, 31), cash=Decimal("1200.00"), bank=Decimal("15000.00"), receivables=Decimal("500.00"), debts=Decimal("300.00"))
        self.assertEqual(snapshot.net_worth, Decimal("16400.00"))

    def test_net_worth_calculation(self):
        snapshot = AssetSnapshot(cash=Decimal("100.00"), bank=Decimal("200.00"), receivables=Decimal("50.00"), debts=Decimal("150.00"))
        self.assertEqual(snapshot.net_worth, Decimal("200.00"))
