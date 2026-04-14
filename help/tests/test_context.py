from django.contrib.auth.models import User
from django.test import TestCase
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization
from help.context import get_help_text, HELP_TEXTS


class HelpContextTest(TestCase):
    def test_known_topic(self):
        text = get_help_text("entry_create")
        self.assertIsInstance(text, str)
        self.assertTrue(len(text) > 0)

    def test_unknown_topic(self):
        text = get_help_text("nonexistent_topic")
        self.assertEqual(text, "")

    def test_all_topics_are_strings(self):
        for topic, text in HELP_TEXTS.items():
            self.assertIsInstance(text, str, f"Topic '{topic}' is not a string")


class HelpViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.user = User.objects.create_user(username="test", password="test123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.LECTURE)
        self.client.login(username="test", password="test123")

    def test_help_panel_loads(self):
        response = self.client.get("/help/panel/?topic=entry_create")
        self.assertEqual(response.status_code, 200)
