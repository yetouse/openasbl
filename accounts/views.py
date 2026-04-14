from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.decorators import require_permission
from accounts.models import PermissionLevel, UserProfile

class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"

class LogoutView(auth_views.LogoutView):
    pass

@login_required
@require_permission(PermissionLevel.ADMIN)
def user_list(request):
    profiles = UserProfile.objects.select_related("user").all()
    return render(request, "accounts/user_list.html", {"profiles": profiles})
