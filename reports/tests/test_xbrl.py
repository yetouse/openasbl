from datetime import date
from decimal import Decimal
from xml.etree.ElementTree import fromstring

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from accounting.models import AssetSnapshot, Category, CategoryType, Entry, FiscalYear
from core.models import Organization
from reports.generators.xbrl import generate_xbrl, _clean_enterprise_number


NS_XBRLI = "http://www.xbrl.org/2003/instance"
NS_MET = "http://www.nbb.be/be/fr/cbso/dict/met"


class CleanEnterpriseNumberTest(TestCase):
    def test_dots_removed(self):
        self.assertEqual(_clean_enterprise_number("0413.726.972"), "0413726972")

    def test_already_clean(self):
        self.assertEqual(_clean_enterprise_number("0413726972"), "0413726972")

    def test_with_be_prefix(self):
        self.assertEqual(_clean_enterprise_number("BE0413726972"), "0413726972")

    def test_empty(self):
        self.assertEqual(_clean_enterprise_number(""), "")


class GenerateXbrlTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("xbrl", password="pass")
        self.org = Organization.objects.create(
            name="Club Test ASBL",
            address="Rue du Test 1, 5000 Namur",
            enterprise_number="0413.726.972",
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        self.cat_income = Category.objects.create(
            organization=self.org, name="Cotisations", category_type=CategoryType.INCOME
        )
        self.cat_expense = Category.objects.create(
            organization=self.org, name="Fournitures", category_type=CategoryType.EXPENSE
        )
        Entry.objects.create(
            fiscal_year=self.fy, category=self.cat_income,
            date=date(2025, 3, 1), amount=Decimal("5000.00"),
            description="Cotisations membres", created_by=self.user,
        )
        Entry.objects.create(
            fiscal_year=self.fy, category=self.cat_expense,
            date=date(2025, 4, 15), amount=Decimal("1200.50"),
            description="Achat matériel", created_by=self.user,
        )
        AssetSnapshot.objects.create(
            fiscal_year=self.fy, date=date(2025, 12, 31),
            cash=Decimal("500.00"), bank=Decimal("8000.00"),
            receivables=Decimal("200.00"), debts=Decimal("1500.00"),
        )

    def test_returns_valid_xml(self):
        xml_bytes = generate_xbrl(self.fy)
        self.assertTrue(xml_bytes.startswith(b"<?xml"))
        root = fromstring(xml_bytes)
        self.assertIn("xbrl", root.tag)

    def test_entity_identifier(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        identifiers = root.findall(f".//{{{NS_XBRLI}}}identifier")
        self.assertTrue(len(identifiers) > 0)
        self.assertEqual(identifiers[0].text, "0413726972")

    def test_period_is_end_date(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        instants = root.findall(f".//{{{NS_XBRLI}}}instant")
        self.assertTrue(len(instants) > 0)
        self.assertEqual(instants[0].text, "2025-12-31")

    def test_income_total(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        # Find am1 facts - income should be 5000.00
        facts = root.findall(f".//{{{NS_MET}}}am1")
        values = [f.text for f in facts]
        self.assertIn("5000.00", values)

    def test_expense_total(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        facts = root.findall(f".//{{{NS_MET}}}am1")
        values = [f.text for f in facts]
        self.assertIn("1200.50", values)

    def test_result_is_income_minus_expense(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        # am2 is used for result (can be negative)
        facts = root.findall(f".//{{{NS_MET}}}am2")
        values = [f.text for f in facts]
        self.assertIn("3799.50", values)

    def test_balance_sheet_cash_bank(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        facts = root.findall(f".//{{{NS_MET}}}am1")
        values = [f.text for f in facts]
        # cash + bank = 500 + 8000 = 8500
        self.assertIn("8500.00", values)

    def test_balance_sheet_debts(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        facts = root.findall(f".//{{{NS_MET}}}am1")
        values = [f.text for f in facts]
        self.assertIn("1500.00", values)

    def test_organization_name(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        str_facts = root.findall(f".//{{{NS_MET}}}str2")
        names = [f.text for f in str_facts]
        self.assertIn("Club Test ASBL", names)

    def test_has_schema_ref(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        ns_link = "http://www.xbrl.org/2003/linkbase"
        refs = root.findall(f".//{{{ns_link}}}schemaRef")
        self.assertEqual(len(refs), 1)

    def test_no_snapshot_uses_zeros(self):
        """When no AssetSnapshot exists, balance sheet values are zero."""
        fy2 = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        xml_bytes = generate_xbrl(fy2)
        root = fromstring(xml_bytes)
        facts = root.findall(f".//{{{NS_MET}}}am1")
        values = [f.text for f in facts]
        # All balance sheet values should be 0.00
        self.assertIn("0.00", values)

    def test_eur_unit(self):
        xml_bytes = generate_xbrl(self.fy)
        root = fromstring(xml_bytes)
        units = root.findall(f".//{{{NS_XBRLI}}}unit")
        # Should be at least one unit (but units aren't namespaced in our output)
        # Check for EUR in raw XML
        self.assertIn(b"EUR", xml_bytes)


class XbrlViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("testuser", password="testpass")
        self.org = Organization.objects.create(
            name="Test ASBL", address="Bruxelles",
            enterprise_number="0999.999.999",
        )
        self.fy = FiscalYear.objects.create(
            organization=self.org,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )

    def test_requires_login(self):
        url = reverse("reports:annual_accounts_xbrl")
        response = self.client.get(url, {"fiscal_year": self.fy.pk})
        self.assertEqual(response.status_code, 302)

    def test_download_xbrl(self):
        self.client.login(username="testuser", password="testpass")
        url = reverse("reports:annual_accounts_xbrl")
        response = self.client.get(url, {"fiscal_year": self.fy.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn("xml", response["Content-Type"])
        self.assertIn(".xbrl", response["Content-Disposition"])

    def test_filename_contains_enterprise_number(self):
        self.client.login(username="testuser", password="testpass")
        url = reverse("reports:annual_accounts_xbrl")
        response = self.client.get(url, {"fiscal_year": self.fy.pk})
        self.assertIn("0999999999", response["Content-Disposition"])

    def test_filename_contains_year(self):
        self.client.login(username="testuser", password="testpass")
        url = reverse("reports:annual_accounts_xbrl")
        response = self.client.get(url, {"fiscal_year": self.fy.pk})
        self.assertIn("2025", response["Content-Disposition"])

    def test_404_without_fiscal_year(self):
        self.client.login(username="testuser", password="testpass")
        url = reverse("reports:annual_accounts_xbrl")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
