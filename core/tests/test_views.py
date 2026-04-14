from django.contrib.auth.models import User
from django.test import TestCase
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


class SetupWizardTest(TestCase):
    def test_wizard_shows_when_no_org(self):
        response = self.client.get("/core/setup/")
        self.assertEqual(response.status_code, 200)

    def test_wizard_creates_org_and_admin(self):
        response = self.client.post("/core/setup/", {
            "org_name": "RCVD", "org_address": "Dave, Namur",
            "org_enterprise_number": "0123.456.789", "org_email": "info@rcvd.be", "org_phone": "",
            "admin_username": "tresorier", "admin_password": "securepass123",
            "admin_first_name": "Jean", "admin_last_name": "Dupont", "admin_email": "jean@rcvd.be",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Organization.objects.exists())
        self.assertTrue(User.objects.filter(username="tresorier").exists())
        profile = User.objects.get(username="tresorier").profile
        self.assertEqual(profile.permission_level, PermissionLevel.ADMIN)

    def test_wizard_blocked_when_org_exists(self):
        Organization.objects.create(name="Exists", address="Test")
        response = self.client.get("/core/setup/")
        self.assertEqual(response.status_code, 302)


class OrganizationSettingsTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="RCVD", address="Dave")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.client.login(username="admin", password="test123")

    def test_settings_page_loads(self):
        response = self.client.get("/core/settings/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RCVD")

    def test_non_admin_cannot_access(self):
        self.user.profile.permission_level = PermissionLevel.GESTION
        self.user.profile.save()
        response = self.client.get("/core/settings/")
        self.assertEqual(response.status_code, 403)
