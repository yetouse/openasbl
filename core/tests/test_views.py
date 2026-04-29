from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


class SetupWizardTest(TestCase):
    def test_wizard_shows_when_no_org(self):
        response = self.client.get("/core/setup/")
        self.assertEqual(response.status_code, 200)

    def test_wizard_creates_org_and_admin(self):
        response = self.client.post("/core/setup/", {
            "org_name": "Mon ASBL", "org_address": "Bruxelles",
            "org_enterprise_number": "0123.456.789", "org_email": "info@monasbl.be", "org_phone": "",
            "admin_username": "tresorier", "admin_password": "securepass123",
            "admin_first_name": "Jean", "admin_last_name": "Dupont", "admin_email": "jean@monasbl.be",
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
        self.org = Organization.objects.create(name="Mon ASBL", address="Bruxelles")
        self.user = User.objects.create_user(username="admin", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.client.login(username="admin", password="test123")

    def test_settings_page_loads(self):
        response = self.client.get("/core/settings/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mon ASBL")

    def test_non_admin_cannot_access(self):
        self.user.profile.permission_level = PermissionLevel.GESTION
        self.user.profile.save()
        response = self.client.get("/core/settings/")
        self.assertEqual(response.status_code, 403)


class VersionFooterTest(TestCase):
    def test_version_appears_in_footer(self):
        Organization.objects.create(name="Test ASBL", address="Bxl")
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        from django.conf import settings
        expected = (settings.BASE_DIR / "VERSION").read_text(encoding="utf-8").strip()
        self.assertContains(response, f"v{expected}")


class UpdateBannerTest(TestCase):
    def setUp(self):
        Organization.objects.create(name="Test ASBL", address="Bxl")

    @override_settings(OPENASBL_UPDATE_CHECK_ENABLED=True)
    @patch("core.context_processors.check_for_update")
    def test_update_banner_shows_when_update_available(self, mock_check):
        mock_check.return_value = {
            "update_available": True,
            "current_version": "2.5.0",
            "latest_version": "2.6.0",
            "update_url": "https://github.com/yetouse/openasbl/releases/latest",
            "update_command": "./install-desktop.sh",
        }
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OpenASBL est disponible")
        self.assertContains(response, "v2.6.0")
        self.assertContains(response, "./install-desktop.sh")

    @override_settings(OPENASBL_UPDATE_CHECK_ENABLED=False)
    @patch("core.context_processors.check_for_update")
    def test_update_banner_hidden_when_check_disabled(self, mock_check):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Une nouvelle version d")
        mock_check.assert_not_called()
