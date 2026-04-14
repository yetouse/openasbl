from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounting.models import (
    AssetSnapshot,
    Budget,
    Category,
    CategoryType,
    Entry,
    FiscalYear,
    FiscalYearStatus,
)
from accounting.seed import seed_categories
from core.models import Organization


# Budget 2026 — montants prévus par catégorie
BUDGETS_2026 = {
    # Recettes
    ("income", "Carnet de dépôt"): Decimal("17000.00"),
    ("income", "Dons"): Decimal("0.00"),
    ("income", "Echos & publicité"): Decimal("1700.00"),
    ("income", "Fédération licences"): Decimal("0.00"),
    ("income", "Manifestations"): Decimal("3200.00"),
    ("income", "Rentrées consommations"): Decimal("7200.00"),
    ("income", "Rentrées école voile"): Decimal("4200.00"),
    ("income", "Subsides autres (adeps)"): Decimal("0.00"),
    ("income", "Subsides Namur"): Decimal("1500.00"),
    ("income", "Voile adultes"): Decimal("1900.00"),
    ("income", "Versements membres"): Decimal("25815.00"),
    # Dépenses
    ("expense", "Assurances"): Decimal("3300.00"),
    ("expense", "Contrats moniteurs"): Decimal("6300.00"),
    ("expense", "Echos & publicité"): Decimal("100.00"),
    ("expense", "Elect & eau"): Decimal("1800.00"),
    ("expense", "Fédération licences"): Decimal("5300.00"),
    ("expense", "Frais école voile"): Decimal("5000.00"),
    ("expense", "Gestion admin"): Decimal("1600.00"),
    ("expense", "Maintenance TT"): Decimal("17000.00"),
    ("expense", "Régates manif"): Decimal("1600.00"),
    ("expense", "Repas boissons"): Decimal("6500.00"),
    ("expense", "Taxes & locations"): Decimal("2300.00"),
    ("expense", "Travaux entretiens"): Decimal("3300.00"),
    ("expense", "Voile adultes"): Decimal("1600.00"),
    ("expense", "Transfert vers carnet dépôt"): Decimal("3000.00"),
}

# Écritures réelles au 31/03/2026 — ventilées en écritures individuelles
# Les montants globaux du rapport sont répartis en écritures plausibles
ENTRIES_2026 = [
    # Recettes
    {
        "category": ("income", "Fédération licences"),
        "date": date(2026, 1, 15),
        "amount": Decimal("2320.68"),
        "description": "Licences fédération 2026",
    },
    {
        "category": ("income", "Manifestations"),
        "date": date(2026, 3, 8),
        "amount": Decimal("54.00"),
        "description": "Entrées journée portes ouvertes",
    },
    {
        "category": ("income", "Rentrées consommations"),
        "date": date(2026, 1, 18),
        "amount": Decimal("125.50"),
        "description": "Consommations bar - janvier",
    },
    {
        "category": ("income", "Rentrées consommations"),
        "date": date(2026, 2, 15),
        "amount": Decimal("98.27"),
        "description": "Consommations bar - février",
    },
    {
        "category": ("income", "Rentrées consommations"),
        "date": date(2026, 3, 14),
        "amount": Decimal("155.00"),
        "description": "Consommations bar - mars",
    },
    {
        "category": ("income", "Versements membres"),
        "date": date(2026, 1, 5),
        "amount": Decimal("3200.00"),
        "description": "Cotisations membres - virement Assoconnect janvier",
    },
    {
        "category": ("income", "Versements membres"),
        "date": date(2026, 1, 10),
        "amount": Decimal("230.00"),
        "description": "Cotisations membres - virement Crelan",
    },
    {
        "category": ("income", "Versements membres"),
        "date": date(2026, 2, 5),
        "amount": Decimal("4100.00"),
        "description": "Cotisations membres - virement Assoconnect février",
    },
    {
        "category": ("income", "Versements membres"),
        "date": date(2026, 3, 5),
        "amount": Decimal("3537.03"),
        "description": "Cotisations membres - virement Assoconnect mars",
    },
    {
        "category": ("income", "Versements membres"),
        "date": date(2026, 3, 15),
        "amount": Decimal("944.06"),
        "description": "Souper de début de saison",
    },
    # Dépenses
    {
        "category": ("expense", "Assurances"),
        "date": date(2026, 1, 10),
        "amount": Decimal("874.53"),
        "description": "Assurance RC annuelle - acompte",
    },
    {
        "category": ("expense", "Assurances"),
        "date": date(2026, 3, 1),
        "amount": Decimal("800.00"),
        "description": "Assurance bateaux 2026",
    },
    {
        "category": ("expense", "Fédération licences"),
        "date": date(2026, 1, 20),
        "amount": Decimal("5240.00"),
        "description": "Cotisation FFYB et licences 2026",
    },
    {
        "category": ("expense", "Elect & eau"),
        "date": date(2026, 2, 28),
        "amount": Decimal("309.00"),
        "description": "Facture électricité T1 2026",
    },
    {
        "category": ("expense", "Gestion admin"),
        "date": date(2026, 1, 8),
        "amount": Decimal("450.00"),
        "description": "Comptabilité et secrétariat",
    },
    {
        "category": ("expense", "Gestion admin"),
        "date": date(2026, 2, 10),
        "amount": Decimal("520.21"),
        "description": "Frais bancaires et administratifs",
    },
    {
        "category": ("expense", "Gestion admin"),
        "date": date(2026, 3, 10),
        "amount": Decimal("446.00"),
        "description": "Fournitures bureau et timbres",
    },
    {
        "category": ("expense", "Maintenance TT"),
        "date": date(2026, 2, 20),
        "amount": Decimal("1076.90"),
        "description": "Travaux maintenance terre-plein",
    },
    {
        "category": ("expense", "Repas boissons"),
        "date": date(2026, 1, 25),
        "amount": Decimal("320.00"),
        "description": "Achat boissons bar",
    },
    {
        "category": ("expense", "Repas boissons"),
        "date": date(2026, 2, 22),
        "amount": Decimal("280.05"),
        "description": "Réapprovisionnement bar",
    },
    {
        "category": ("expense", "Repas boissons"),
        "date": date(2026, 3, 20),
        "amount": Decimal("347.00"),
        "description": "Achat boissons + snacks",
    },
    {
        "category": ("expense", "Taxes & locations"),
        "date": date(2026, 1, 31),
        "amount": Decimal("126.97"),
        "description": "Taxe communale",
    },
    {
        "category": ("expense", "Travaux entretiens"),
        "date": date(2026, 2, 15),
        "amount": Decimal("875.11"),
        "description": "Réparation toiture péniche",
    },
    {
        "category": ("expense", "Travaux entretiens"),
        "date": date(2026, 3, 10),
        "amount": Decimal("500.00"),
        "description": "Entretien pontons",
    },
]


class Command(BaseCommand):
    help = "Seed database with real RCVD data (budget 2026, entries Q1 2026, asset snapshots)"

    def handle(self, *args, **options):
        # 1. Organisation
        org, created = Organization.objects.get_or_create(
            defaults={
                "name": "Royal Cercle de Voile de Dave asbl",
                "address": "Rue de Dave, 735\n5100 Namur",
                "enterprise_number": "0412110339",
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Organisation RCVD créée."))
        else:
            self.stdout.write("Organisation existante, mise à jour ignorée.")

        # 2. Catégories
        seed_categories(org)
        self.stdout.write(self.style.SUCCESS("Catégories créées/vérifiées."))

        # 3. Exercice 2025 (clôturé) et 2026 (ouvert)
        fy2025, _ = FiscalYear.objects.get_or_create(
            organization=org,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            defaults={"status": FiscalYearStatus.CLOSED},
        )
        fy2026, _ = FiscalYear.objects.get_or_create(
            organization=org,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            defaults={"status": FiscalYearStatus.OPEN},
        )
        self.stdout.write(self.style.SUCCESS("Exercices 2025 et 2026 créés/vérifiés."))

        # 4. Budgets 2026
        budget_count = 0
        for (cat_type, cat_name), amount in BUDGETS_2026.items():
            if amount == Decimal("0.00"):
                continue
            cat = Category.objects.get(
                organization=org, name=cat_name, category_type=cat_type
            )
            _, created = Budget.objects.get_or_create(
                fiscal_year=fy2026,
                category=cat,
                defaults={"planned_amount": amount},
            )
            if created:
                budget_count += 1
        self.stdout.write(self.style.SUCCESS(f"{budget_count} budgets 2026 créés."))

        # 5. Utilisateur pour les écritures
        user, _ = User.objects.get_or_create(
            username="tresorier",
            defaults={
                "first_name": "Trésorier",
                "last_name": "RCVD",
                "is_staff": False,
            },
        )

        # 6. Écritures réelles Q1 2026
        entry_count = 0
        for entry_data in ENTRIES_2026:
            cat_type, cat_name = entry_data["category"]
            cat = Category.objects.get(
                organization=org, name=cat_name, category_type=cat_type
            )
            _, created = Entry.objects.get_or_create(
                fiscal_year=fy2026,
                category=cat,
                date=entry_data["date"],
                amount=entry_data["amount"],
                description=entry_data["description"],
                defaults={"created_by": user},
            )
            if created:
                entry_count += 1
        self.stdout.write(self.style.SUCCESS(f"{entry_count} écritures Q1 2026 créées."))

        # 7. Snapshots patrimoine
        # Fin 2024 : Caisse 226.56, CC 23617.36, Dépôt 55143.10
        AssetSnapshot.objects.get_or_create(
            fiscal_year=fy2025,
            date=date(2024, 12, 31),
            defaults={
                "cash": Decimal("226.56"),
                "bank": Decimal("78760.46"),  # 23617.36 + 55143.10
                "notes": "Situation fin 2024 — CC: 23 617,36 + Carnet dépôt: 55 143,10",
            },
        )
        # Fin 2025 : Caisse 121.50, CC 23789.48, Dépôt 71835.51
        AssetSnapshot.objects.get_or_create(
            fiscal_year=fy2025,
            date=date(2025, 12, 31),
            defaults={
                "cash": Decimal("121.50"),
                "bank": Decimal("95624.99"),  # 23789.48 + 71835.51
                "notes": "Situation fin 2025 — CC: 23 789,48 + Carnet dépôt: 71 835,51",
            },
        )
        # Au 31/03/2026 : Caisse 121.50, CC 26388.25, Dépôt 71835.51
        AssetSnapshot.objects.get_or_create(
            fiscal_year=fy2026,
            date=date(2026, 3, 31),
            defaults={
                "cash": Decimal("121.50"),
                "bank": Decimal("98223.76"),  # 26388.25 + 71835.51
                "notes": "Situation au 31/03/2026 — CC: 26 388,25 + Carnet dépôt: 71 835,51",
            },
        )
        self.stdout.write(self.style.SUCCESS("Snapshots patrimoine créés."))

        # Résumé
        total_income = sum(
            e["amount"] for e in ENTRIES_2026
            if e["category"][0] == "income"
        )
        total_expense = sum(
            e["amount"] for e in ENTRIES_2026
            if e["category"][0] == "expense"
        )
        self.stdout.write("")
        self.stdout.write(f"  Recettes Q1 2026 : {total_income:>10.2f} €")
        self.stdout.write(f"  Dépenses Q1 2026 : {total_expense:>10.2f} €")
        self.stdout.write(f"  Solde             : {total_income - total_expense:>10.2f} €")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Seed RCVD terminé !"))
