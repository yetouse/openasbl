from django.contrib.auth.models import User
from django.test import TestCase
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization

class LoginViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.user = User.objects.create_user(username="tresorier", password="testpass123")
        UserProfile.objects.create(user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN)

    def test_login_page_loads(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post("/accounts/login/", {"username": "tresorier", "password": "testpass123"})
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        response = self.client.post("/accounts/login/", {"username": "tresorier", "password": "wrong"})
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="tresorier", password="testpass123")
        response = self.client.post("/accounts/logout/")
        self.assertEqual(response.status_code, 302)

class UserListViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.admin_user = User.objects.create_user(username="admin", password="testpass123")
        UserProfile.objects.create(user=self.admin_user, organization=self.org, permission_level=PermissionLevel.ADMIN)
        self.reader_user = User.objects.create_user(username="reader", password="testpass123")
        UserProfile.objects.create(user=self.reader_user, organization=self.org, permission_level=PermissionLevel.LECTURE)

    def test_admin_can_see_user_list(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get("/accounts/users/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin")
        self.assertContains(response, "reader")

    def test_reader_cannot_see_user_list(self):
        self.client.login(username="reader", password="testpass123")
        response = self.client.get("/accounts/users/")
        self.assertEqual(response.status_code, 403)
