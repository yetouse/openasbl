from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


class AccountsTestMixin:
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.admin_user = User.objects.create_user(username="admin", password="testpass123")
        UserProfile.objects.create(
            user=self.admin_user, organization=self.org, permission_level=PermissionLevel.ADMIN
        )
        self.reader_user = User.objects.create_user(username="reader", password="testpass123")
        UserProfile.objects.create(
            user=self.reader_user, organization=self.org, permission_level=PermissionLevel.LECTURE
        )


class LoginViewTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name="Test", address="Namur")
        self.user = User.objects.create_user(username="tresorier", password="testpass123")
        UserProfile.objects.create(
            user=self.user, organization=self.org, permission_level=PermissionLevel.ADMIN
        )

    def test_login_page_loads(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(
            "/accounts/login/", {"username": "tresorier", "password": "testpass123"}
        )
        self.assertEqual(response.status_code, 302)

    def test_login_failure(self):
        response = self.client.post(
            "/accounts/login/", {"username": "tresorier", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username="tresorier", password="testpass123")
        response = self.client.post("/accounts/logout/")
        self.assertEqual(response.status_code, 302)


class UserListViewTest(AccountsTestMixin, TestCase):
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

    def test_shows_permission_badges(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get("/accounts/users/")
        self.assertContains(response, "Admin")
        self.assertContains(response, "Lecture")

    def test_shows_create_button(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get("/accounts/users/")
        self.assertContains(response, "Créer un utilisateur")


class UserCreateViewTest(AccountsTestMixin, TestCase):
    def test_create_requires_admin(self):
        self.client.login(username="reader", password="testpass123")
        response = self.client.get("/accounts/users/create/")
        self.assertEqual(response.status_code, 403)

    def test_create_form_renders(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get("/accounts/users/create/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Créer un utilisateur")

    def test_create_user_success(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post("/accounts/users/create/", {
            "username": "newuser",
            "first_name": "Jean",
            "last_name": "Dupont",
            "email": "jean@test.be",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "permission_level": PermissionLevel.GESTION,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        profile = UserProfile.objects.get(user__username="newuser")
        self.assertEqual(profile.permission_level, PermissionLevel.GESTION)

    def test_create_duplicate_username_fails(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post("/accounts/users/create/", {
            "username": "admin",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "permission_level": PermissionLevel.LECTURE,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "déjà pris")

    def test_create_password_mismatch_fails(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post("/accounts/users/create/", {
            "username": "newuser",
            "password": "pass1",
            "password_confirm": "pass2",
            "permission_level": PermissionLevel.LECTURE,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ne correspondent pas")


class UserEditViewTest(AccountsTestMixin, TestCase):
    def test_edit_requires_admin(self):
        self.client.login(username="reader", password="testpass123")
        response = self.client.get(f"/accounts/users/{self.reader_user.pk}/edit/")
        self.assertEqual(response.status_code, 403)

    def test_edit_form_renders(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get(f"/accounts/users/{self.reader_user.pk}/edit/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reader")

    def test_edit_user_success(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(f"/accounts/users/{self.reader_user.pk}/edit/", {
            "first_name": "Pierre",
            "last_name": "Martin",
            "email": "pierre@test.be",
            "is_active": True,
            "permission_level": PermissionLevel.GESTION,
        })
        self.assertEqual(response.status_code, 302)
        self.reader_user.refresh_from_db()
        self.assertEqual(self.reader_user.first_name, "Pierre")
        profile = UserProfile.objects.get(user=self.reader_user)
        self.assertEqual(profile.permission_level, PermissionLevel.GESTION)

    def test_edit_can_deactivate_user(self):
        self.client.login(username="admin", password="testpass123")
        self.client.post(f"/accounts/users/{self.reader_user.pk}/edit/", {
            "first_name": "",
            "last_name": "",
            "email": "",
            "permission_level": PermissionLevel.LECTURE,
            # is_active not sent = False (unchecked checkbox)
        })
        self.reader_user.refresh_from_db()
        self.assertFalse(self.reader_user.is_active)


class UserPasswordViewTest(AccountsTestMixin, TestCase):
    def test_password_requires_admin(self):
        self.client.login(username="reader", password="testpass123")
        response = self.client.get(f"/accounts/users/{self.reader_user.pk}/password/")
        self.assertEqual(response.status_code, 403)

    def test_password_form_renders(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get(f"/accounts/users/{self.reader_user.pk}/password/")
        self.assertEqual(response.status_code, 200)

    def test_change_password_success(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(f"/accounts/users/{self.reader_user.pk}/password/", {
            "password": "newpass456",
            "password_confirm": "newpass456",
        })
        self.assertEqual(response.status_code, 302)
        # Verify the new password works
        self.assertTrue(self.client.login(username="reader", password="newpass456"))

    def test_password_mismatch_fails(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(f"/accounts/users/{self.reader_user.pk}/password/", {
            "password": "pass1",
            "password_confirm": "pass2",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ne correspondent pas")


class UserDeleteViewTest(AccountsTestMixin, TestCase):
    def test_delete_requires_admin(self):
        self.client.login(username="reader", password="testpass123")
        response = self.client.get(f"/accounts/users/{self.reader_user.pk}/delete/")
        self.assertEqual(response.status_code, 403)

    def test_delete_confirm_renders(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get(f"/accounts/users/{self.reader_user.pk}/delete/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reader")

    def test_delete_user_success(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(f"/accounts/users/{self.reader_user.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="reader").exists())

    def test_cannot_delete_self(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.post(f"/accounts/users/{self.admin_user.pk}/delete/")
        self.assertEqual(response.status_code, 302)
        # Admin still exists
        self.assertTrue(User.objects.filter(username="admin").exists())

    def test_delete_nonexistent_user_404(self):
        self.client.login(username="admin", password="testpass123")
        response = self.client.get("/accounts/users/9999/delete/")
        self.assertEqual(response.status_code, 404)
