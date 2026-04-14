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
from core.models import Organization
from reports.generators.pdf import (
    generate_annual_accounts_pdf,
    generate_budget_tracking_pdf,
    generate_journal_pdf,
    generate_monthly_ca_pdf,
    generate_patrimony_pdf,
    generate_year_comparison_pdf,
)


class PdfTestMixin:
    """Common setup for PDF tests."""

    def setUp(self):
        self.org = Organization.objects.create(name="Test ASBL", address="Bruxelles")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        self.user = User.objects.create_user("testuser", password="testpass")
        self.cat_income = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        self.cat_expense = Category.objects.create(
            organization=self.org, name="Fournitures", category_type=CategoryType.EXPENSE
        )


class JournalPdfTest(PdfTestMixin, TestCase):
    def test_journal_pdf_returns_pdf_bytes(self):
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            date=date(2025, 3, 15),
            amount=Decimal("100.00"),
            description="Cotisation membre",
            created_by=self.user,
        )
        result = generate_journal_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))

    def test_journal_pdf_empty_fiscal_year(self):
        result = generate_journal_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))


class PatrimonyPdfTest(PdfTestMixin, TestCase):
    def test_patrimony_pdf_returns_pdf_bytes(self):
        AssetSnapshot.objects.create(
            fiscal_year=self.fy,
            date=date(2025, 6, 30),
            cash=Decimal("500.00"),
            bank=Decimal("10000.00"),
            receivables=Decimal("200.00"),
            debts=Decimal("1500.00"),
        )
        result = generate_patrimony_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))

    def test_patrimony_pdf_no_snapshot(self):
        result = generate_patrimony_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))


class MonthlyCaPdfTest(PdfTestMixin, TestCase):
    def test_monthly_ca_pdf_returns_pdf_bytes(self):
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            date=date(2025, 3, 15),
            amount=Decimal("100.00"),
            description="Cotisation",
            created_by=self.user,
        )
        Budget.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            planned_amount=Decimal("150.00"),
        )
        result = generate_monthly_ca_pdf(self.fy, 2025, 3)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))


class BudgetTrackingPdfTest(PdfTestMixin, TestCase):
    def test_budget_tracking_pdf_returns_pdf_bytes(self):
        Budget.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            planned_amount=Decimal("1000.00"),
        )
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            date=date(2025, 3, 15),
            amount=Decimal("500.00"),
            description="Cotisation",
            created_by=self.user,
        )
        result = generate_budget_tracking_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))

    def test_budget_tracking_pdf_empty(self):
        result = generate_budget_tracking_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))


class AnnualAccountsPdfTest(PdfTestMixin, TestCase):
    def test_annual_accounts_pdf_returns_pdf_bytes(self):
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            date=date(2025, 3, 15),
            amount=Decimal("1000.00"),
            description="Cotisation",
            created_by=self.user,
        )
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_expense,
            date=date(2025, 4, 10),
            amount=Decimal("200.00"),
            description="Achat fournitures",
            created_by=self.user,
        )
        AssetSnapshot.objects.create(
            fiscal_year=self.fy,
            date=date(2025, 12, 31),
            cash=Decimal("500.00"),
            bank=Decimal("10000.00"),
        )
        result = generate_annual_accounts_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))

    def test_annual_accounts_pdf_empty(self):
        result = generate_annual_accounts_pdf(self.fy)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))


class YearComparisonPdfTest(PdfTestMixin, TestCase):
    def test_year_comparison_pdf_returns_pdf_bytes(self):
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            date=date(2025, 3, 15),
            amount=Decimal("500.00"),
            description="Cotisation",
            created_by=self.user,
        )
        result = generate_year_comparison_pdf([self.fy])
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))

    def test_year_comparison_multiple_years(self):
        fy2 = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat_income,
            date=date(2025, 3, 15),
            amount=Decimal("500.00"),
            description="Cotisation 2025",
            created_by=self.user,
        )
        Entry.objects.create(
            fiscal_year=fy2,
            category=self.cat_income,
            date=date(2024, 3, 15),
            amount=Decimal("400.00"),
            description="Cotisation 2024",
            created_by=self.user,
        )
        result = generate_year_comparison_pdf([fy2, self.fy])
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))
