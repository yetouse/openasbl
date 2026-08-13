import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounting.models import AssetSnapshot, Budget, Category, Entry, FiscalYear
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


def format_amount(value):
    """Formate un montant à la française : 23 468,40"""
    return f"{value:,.2f}".replace(",", " ").replace(".", ",")


class Command(BaseCommand):
    help = "Importe des données comptables agrégées depuis un fichier JSON"

    def add_arguments(self, parser):
        parser.add_argument("source", help="Chemin du fichier JSON à importer")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Affiche ce qui serait importé, sans rien écrire en base",
        )
        parser.add_argument(
            "--user",
            dest="user",
            help="Compte qui signera les écritures (défaut : un administrateur)",
        )

    def handle(self, *args, **options):
        payload = json.loads(Path(options["source"]).read_text(encoding="utf-8"))

        organization = Organization.objects.first()
        if organization is None:
            raise CommandError(
                "Aucune organisation configurée. "
                "Lancez d'abord l'assistant de configuration."
            )

        author = self.resolve_author(options["user"])

        with transaction.atomic():
            for year in payload["fiscal_years"]:
                self.import_year(year, organization, author)

            if options["dry_run"]:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Simulation : rien n'a été écrit."))
            else:
                self.stdout.write(self.style.SUCCESS("Import terminé."))

    def resolve_author(self, username):
        """Compte qui signera les écritures importées."""
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f"Utilisateur inconnu : {username}")

        superuser = User.objects.filter(is_superuser=True).order_by("pk").first()
        if superuser:
            return superuser

        # L'assistant de configuration crée un administrateur applicatif, qui
        # n'est pas un superutilisateur Django.
        profile = (
            UserProfile.objects.filter(permission_level=PermissionLevel.ADMIN)
            .order_by("pk")
            .first()
        )
        if profile:
            return profile.user

        raise CommandError(
            "Aucun compte administrateur pour signer les écritures. "
            "Précisez un compte avec --user."
        )

    def import_year(self, year, organization, author):
        start_date = date.fromisoformat(year["start_date"])
        cutoff_date = date.fromisoformat(year["cutoff_date"])

        fiscal_year, _ = FiscalYear.objects.get_or_create(
            organization=organization,
            start_date=start_date,
            end_date=date.fromisoformat(year["end_date"]),
        )

        description = (
            f"Cumul du {start_date:%d/%m/%Y} au {cutoff_date:%d/%m/%Y}"
            " — report de synthèse"
        )

        entries = 0
        for line in year.get("categories", []):
            category, _ = Category.objects.get_or_create(
                organization=organization,
                name=line["name"],
                category_type=line["type"],
            )

            if "budget" in line:
                Budget.objects.update_or_create(
                    fiscal_year=fiscal_year,
                    category=category,
                    defaults={"planned_amount": Decimal(line["budget"])},
                )

            # Le modèle impose un montant strictement positif : une rubrique
            # sans mouvement ne donne pas d'écriture, seulement une catégorie.
            actual = Decimal(line.get("actual", "0"))
            if actual > 0:
                Entry.objects.update_or_create(
                    fiscal_year=fiscal_year,
                    category=category,
                    date=cutoff_date,
                    defaults={
                        "amount": actual,
                        "description": description,
                        "created_by": author,
                    },
                )
                entries += 1

        self.import_assets(year.get("assets"), fiscal_year, cutoff_date)

        self.stdout.write(
            f"  {start_date:%Y} : {len(year.get('categories', []))} rubriques, "
            f"{entries} écritures au {cutoff_date:%d/%m/%Y}"
        )

    def import_assets(self, assets, fiscal_year, cutoff_date):
        if not assets:
            return

        # AssetSnapshot n'a qu'un champ "banque" : on additionne les comptes et
        # on conserve leur ventilation dans les notes.
        accounts = assets.get("accounts", [])
        bank = sum((Decimal(a["amount"]) for a in accounts), Decimal("0"))
        notes = " ; ".join(
            f"{a['label']} : {format_amount(Decimal(a['amount']))} €" for a in accounts
        )

        AssetSnapshot.objects.update_or_create(
            fiscal_year=fiscal_year,
            date=cutoff_date,
            defaults={
                "cash": Decimal(assets.get("cash", "0")),
                "bank": bank,
                "receivables": Decimal(assets.get("receivables", "0")),
                "debts": Decimal(assets.get("debts", "0")),
                "notes": notes,
            },
        )
