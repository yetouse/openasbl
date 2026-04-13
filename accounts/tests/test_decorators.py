from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.http import HttpResponse
from accounts.decorators import require_permission
from accounts.models import PermissionLevel, UserProfile
from core.models import Organization


@require_permission(PermissionLevel.GESTION)
def gestion_view(request):
    return HttpResponse("OK")


@require_permission(PermissionLevel.ADMIN)
def admin_view(request):
    return HttpResponse("OK")


class RequirePermissionTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.org = Organization.objects.create(name="Test", address="Namur")

    def _make_user(self, level):
        user = User.objects.create_user(username=f"user_{level}", password="testpass123")
        UserProfile.objects.create(user=user, organization=self.org, permission_level=level)
        return user

    def test_sufficient_permission(self):
        request = self.factory.get("/")
        request.user = self._make_user(PermissionLevel.GESTION)
        response = gestion_view(request)
        self.assertEqual(response.status_code, 200)

    def test_insufficient_permission(self):
        request = self.factory.get("/")
        request.user = self._make_user(PermissionLevel.LECTURE)
        response = gestion_view(request)
        self.assertEqual(response.status_code, 403)

    def test_admin_only(self):
        request = self.factory.get("/")
        request.user = self._make_user(PermissionLevel.VALIDATION)
        response = admin_view(request)
        self.assertEqual(response.status_code, 403)
