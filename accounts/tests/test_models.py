from django.contrib.auth.models import User
from django.test import TestCase
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test ASBL", address="Namur")
        self.user = User.objects.create_user(username="tresorier", password="testpass123")

    def test_create_profile(self):
        profile = UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.assertEqual(profile.permission_level, PermissionLevel.ADMIN)
        self.assertEqual(str(profile), "tresorier (Admin)")

    def test_permission_levels(self):
        self.assertEqual(PermissionLevel.LECTURE, "lecture")
        self.assertEqual(PermissionLevel.GESTION, "gestion")
        self.assertEqual(PermissionLevel.VALIDATION, "validation")
        self.assertEqual(PermissionLevel.ADMIN, "admin")

    def test_can_edit(self):
        profile = UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.GESTION)
        self.assertTrue(profile.can_edit)
        profile.permission_level = PermissionLevel.LECTURE
        self.assertFalse(profile.can_edit)

    def test_can_validate(self):
        profile = UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.VALIDATION)
        self.assertTrue(profile.can_validate)
        profile.permission_level = PermissionLevel.GESTION
        self.assertFalse(profile.can_validate)

    def test_can_manage_users(self):
        profile = UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.assertTrue(profile.can_manage_users)
        profile.permission_level = PermissionLevel.VALIDATION
        self.assertFalse(profile.can_manage_users)
