from django.test import TestCase
from core.models import Organization

class OrganizationModelTest(TestCase):
    def test_create_organization(self):
        org = Organization.objects.create(
            name="Mon ASBL",
            address="Rue de la Loi 1, 1000 Bruxelles",
            enterprise_number="0123.456.789",
            email="info@monasbl.be",
            phone="+32 2 123456",
        )
        self.assertEqual(org.name, "Mon ASBL")
        self.assertEqual(str(org), "Mon ASBL")

    def test_enterprise_number_optional(self):
        org = Organization.objects.create(name="Test ASBL", address="Bruxelles")
        self.assertEqual(org.enterprise_number, "")

    def test_only_one_organization(self):
        Organization.objects.create(name="First ASBL", address="Namur")
        org2 = Organization(name="Second ASBL", address="Liège")
        with self.assertRaises(Exception):
            org2.full_clean()
