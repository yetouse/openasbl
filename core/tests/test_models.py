from django.test import TestCase
from core.models import Organization

class OrganizationModelTest(TestCase):
    def test_create_organization(self):
        org = Organization.objects.create(
            name="Royal Cercle de Voile de Dave",
            address="Dave, Namur",
            enterprise_number="0123.456.789",
            email="info@rcvd.be",
            phone="+32 81 123456",
        )
        self.assertEqual(org.name, "Royal Cercle de Voile de Dave")
        self.assertEqual(str(org), "Royal Cercle de Voile de Dave")

    def test_enterprise_number_optional(self):
        org = Organization.objects.create(name="Test ASBL", address="Bruxelles")
        self.assertEqual(org.enterprise_number, "")

    def test_only_one_organization(self):
        Organization.objects.create(name="First ASBL", address="Namur")
        org2 = Organization(name="Second ASBL", address="Liège")
        with self.assertRaises(Exception):
            org2.full_clean()
