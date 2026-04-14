from django.test import TestCase
from accounting.models import Category, CategoryType
from accounting.seed import DEFAULT_CATEGORIES, seed_categories
from core.models import Organization

class SeedCategoriesTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")

    def test_seed_creates_categories(self):
        seed_categories(self.org)
        self.assertEqual(Category.objects.filter(organization=self.org).count(), len(DEFAULT_CATEGORIES))

    def test_seed_is_idempotent(self):
        seed_categories(self.org)
        seed_categories(self.org)
        self.assertEqual(Category.objects.filter(organization=self.org).count(), len(DEFAULT_CATEGORIES))

    def test_seed_has_income_and_expense(self):
        seed_categories(self.org)
        income = Category.objects.filter(organization=self.org, category_type=CategoryType.INCOME).count()
        expense = Category.objects.filter(organization=self.org, category_type=CategoryType.EXPENSE).count()
        self.assertGreater(income, 0)
        self.assertGreater(expense, 0)
