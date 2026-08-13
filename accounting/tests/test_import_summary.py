import json
import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from accounting.models import (AssetSnapshot, Budget, Category, CategoryType, Entry,
                               FiscalYear)
from core.models import Organization


class ImportSummaryCommandTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_superuser("tresorier", "t@example.be", "secret")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def write_payload(self, payload):
        path = self.tmp_path / "data.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_creates_fiscal_year(self):
        path = self.write_payload(
            {
                "fiscal_years": [
                    {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31",
                        "cutoff_date": "2025-11-30",
                        "categories": [],
                    }
                ]
            }
        )

        call_command("import_summary", path)

        fiscal_year = FiscalYear.objects.get()
        self.assertEqual(fiscal_year.organization, self.org)
        self.assertEqual(fiscal_year.start_date, date(2025, 1, 1))
        self.assertEqual(fiscal_year.end_date, date(2025, 12, 31))

    def test_creates_categories_with_their_type(self):
        path = self.write_payload(
            {
                "fiscal_years": [
                    {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31",
                        "cutoff_date": "2025-11-30",
                        "categories": [
                            {"name": "Manifestations", "type": "income", "actual": "2987.22"},
                            {"name": "Assurances", "type": "expense", "actual": "3002.32"},
                        ],
                    }
                ]
            }
        )

        call_command("import_summary", path)

        self.assertEqual(Category.objects.count(), 2)
        manifestations = Category.objects.get(name="Manifestations")
        self.assertEqual(manifestations.organization, self.org)
        self.assertEqual(manifestations.category_type, CategoryType.INCOME)
        self.assertEqual(
            Category.objects.get(name="Assurances").category_type, CategoryType.EXPENSE
        )

    def test_creates_budget_from_planned_amount(self):
        path = self.write_payload(
            {
                "fiscal_years": [
                    {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31",
                        "cutoff_date": "2025-11-30",
                        "categories": [
                            {"name": "Manifestations", "type": "income", "budget": "2400.00"},
                        ],
                    }
                ]
            }
        )

        call_command("import_summary", path)

        budget = Budget.objects.get()
        self.assertEqual(budget.planned_amount, Decimal("2400.00"))
        self.assertEqual(budget.category.name, "Manifestations")
        self.assertEqual(budget.fiscal_year, FiscalYear.objects.get())

    def test_creates_no_budget_when_amount_absent(self):
        path = self.write_payload(
            {
                "fiscal_years": [
                    {
                        "start_date": "2024-01-01",
                        "end_date": "2024-12-31",
                        "cutoff_date": "2024-12-31",
                        "categories": [{"name": "Manifestations", "type": "income"}],
                    }
                ]
            }
        )

        call_command("import_summary", path)

        self.assertEqual(Budget.objects.count(), 0)

    def test_creates_summary_entry_dated_at_cutoff(self):
        path = self.write_payload(
            {
                "fiscal_years": [
                    {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31",
                        "cutoff_date": "2025-11-30",
                        "categories": [
                            {"name": "Manifestations", "type": "income", "actual": "2987.22"},
                        ],
                    }
                ]
            }
        )

        call_command("import_summary", path)

        entry = Entry.objects.get()
        self.assertEqual(entry.amount, Decimal("2987.22"))
        self.assertEqual(entry.date, date(2025, 11, 30))
        self.assertEqual(entry.category.name, "Manifestations")
        self.assertEqual(entry.created_by, self.user)
        self.assertEqual(
            entry.description,
            "Cumul du 01/01/2025 au 30/11/2025 — report de synthèse",
        )

    def test_creates_no_entry_for_zero_amount(self):
        path = self.write_payload(
            {
                "fiscal_years": [
                    {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31",
                        "cutoff_date": "2025-11-30",
                        "categories": [
                            {"name": "Dons", "type": "income", "actual": "0.00"},
                            {"name": "Manifestations", "type": "income", "actual": "2987.22"},
                        ],
                    }
                ]
            }
        )

        call_command("import_summary", path)

        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(Entry.objects.get().category.name, "Manifestations")
        self.assertTrue(Category.objects.filter(name="Dons").exists())

    def assets_payload(self):
        return {
            "fiscal_years": [
                {
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                    "cutoff_date": "2025-11-30",
                    "categories": [],
                    "assets": {
                        "cash": "121.50",
                        "accounts": [
                            {"label": "Compte courant", "amount": "23468.40"},
                            {"label": "Carnet de dépôt", "amount": "71835.51"},
                        ],
                        "receivables": "0.00",
                        "debts": "0.00",
                    },
                }
            ]
        }

    def test_asset_snapshot_sums_bank_accounts(self):
        call_command("import_summary", self.write_payload(self.assets_payload()))

        snapshot = AssetSnapshot.objects.get()
        self.assertEqual(snapshot.date, date(2025, 11, 30))
        self.assertEqual(snapshot.cash, Decimal("121.50"))
        self.assertEqual(snapshot.bank, Decimal("95303.91"))
        self.assertEqual(snapshot.net_worth, Decimal("95425.41"))

    def test_asset_snapshot_keeps_account_breakdown_in_notes(self):
        call_command("import_summary", self.write_payload(self.assets_payload()))

        notes = AssetSnapshot.objects.get().notes
        self.assertIn("Compte courant : 23 468,40 €", notes)
        self.assertIn("Carnet de dépôt : 71 835,51 €", notes)

    def full_payload(self):
        payload = self.assets_payload()
        payload["fiscal_years"][0]["categories"] = [
            {"name": "Manifestations", "type": "income", "budget": "2400.00", "actual": "2987.22"}
        ]
        return payload

    def test_second_run_does_not_duplicate(self):
        path = self.write_payload(self.full_payload())

        call_command("import_summary", path)
        call_command("import_summary", path)

        self.assertEqual(FiscalYear.objects.count(), 1)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Budget.objects.count(), 1)
        self.assertEqual(Entry.objects.count(), 1)
        self.assertEqual(AssetSnapshot.objects.count(), 1)

    def test_dry_run_writes_nothing(self):
        path = self.write_payload(self.full_payload())

        call_command("import_summary", path, dry_run=True)

        self.assertEqual(FiscalYear.objects.count(), 0)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Budget.objects.count(), 0)
        self.assertEqual(Entry.objects.count(), 0)
        self.assertEqual(AssetSnapshot.objects.count(), 0)

    def test_fails_clearly_without_organization(self):
        Organization.objects.all().delete()
        path = self.write_payload(self.full_payload())

        with self.assertRaises(CommandError) as context:
            call_command("import_summary", path)

        self.assertIn("organisation", str(context.exception).lower())
