from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from accounting.models import Category, CategoryType, Entry, FiscalYear
from core.models import Organization


class ReportViewTestMixin:
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("testuser", password="testpass")
        self.org = Organization.objects.create(name="Test ASBL", address="Bruxelles")
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        self.cat = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        Entry.objects.create(
            fiscal_year=self.fy,
            category=self.cat,
            date=date(2025, 3, 15),
            amount=Decimal("100.00"),
            description="Test entry",
            created_by=self.user,
        )


class ReportSelectViewTest(ReportViewTestMixin, TestCase):
    def test_page_loads(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("reports:report_select"))
        self.assertEqual(response.status_code, 200)

    def test_requires_login(self):
        response = self.client.get(reverse("reports:report_select"))
        self.assertEqual(response.status_code, 302)


class JournalPdfViewTest(ReportViewTestMixin, TestCase):
    def test_download_pdf(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:journal_pdf"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


class JournalExcelViewTest(ReportViewTestMixin, TestCase):
    def test_download_excel(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:journal_excel"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])


class JournalCsvViewTest(ReportViewTestMixin, TestCase):
    def test_download_csv(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:journal_csv"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("csv", response["Content-Type"])


class BudgetTrackingExcelViewTest(ReportViewTestMixin, TestCase):
    def test_download_excel(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:budget_tracking_excel"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])


class BudgetTrackingPdfViewTest(ReportViewTestMixin, TestCase):
    def test_download_pdf(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:budget_tracking_pdf"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


class AnnualAccountsPdfViewTest(ReportViewTestMixin, TestCase):
    def test_download_pdf(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:annual_accounts_pdf"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


class AnnualAccountsExcelViewTest(ReportViewTestMixin, TestCase):
    def test_download_excel(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:annual_accounts_excel"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])


class YearComparisonPdfViewTest(ReportViewTestMixin, TestCase):
    def test_download_pdf(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(
            reverse("reports:year_comparison_pdf"), {"fiscal_year": self.fy.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_download_pdf_all_years(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("reports:year_comparison_pdf"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


class LoginRequiredTest(TestCase):
    def test_all_views_require_login(self):
        urls = [
            reverse("reports:report_select"),
            reverse("reports:journal_pdf"),
            reverse("reports:journal_excel"),
            reverse("reports:journal_csv"),
            reverse("reports:patrimony_pdf"),
            reverse("reports:monthly_ca_pdf"),
            reverse("reports:budget_tracking_pdf"),
            reverse("reports:budget_tracking_excel"),
            reverse("reports:annual_accounts_pdf"),
            reverse("reports:annual_accounts_excel"),
            reverse("reports:annual_accounts_xbrl"),
            reverse("reports:year_comparison_pdf"),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, f"{url} should require login")
