from django.core.management.base import BaseCommand
from accounting.seed import seed_categories
from core.models import Organization


class Command(BaseCommand):
    help = "Seed default accounting categories for the organization"

    def handle(self, *args, **options):
        try:
            org = Organization.objects.get()
        except Organization.DoesNotExist:
            self.stderr.write("Aucune organisation configurée. Créez-en une d'abord.")
            return
        seed_categories(org)
        self.stdout.write(self.style.SUCCESS("Catégories par défaut créées."))
