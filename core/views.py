from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from accounts.decorators import require_permission
from accounts.models import PermissionLevel, UserProfile
from accounting.seed import seed_categories
from core.forms import OrganizationForm, SetupWizardForm
from core.models import Organization


def setup_wizard(request):
    if Organization.objects.exists():
        return redirect("accounting:dashboard")
    if request.method == "POST":
        form = SetupWizardForm(request.POST)
        if form.is_valid():
            org = Organization.objects.create(
                name=form.cleaned_data["org_name"],
                address=form.cleaned_data["org_address"],
                enterprise_number=form.cleaned_data.get("org_enterprise_number", ""),
                email=form.cleaned_data.get("org_email", ""),
                phone=form.cleaned_data.get("org_phone", ""),
            )
            user = User.objects.create_user(
                username=form.cleaned_data["admin_username"],
                password=form.cleaned_data["admin_password"],
                first_name=form.cleaned_data.get("admin_first_name", ""),
                last_name=form.cleaned_data.get("admin_last_name", ""),
                email=form.cleaned_data.get("admin_email", ""),
            )
            UserProfile.objects.create(user=user, organization=org, permission_level=PermissionLevel.ADMIN)
            seed_categories(org)
            login(request, user)
            return redirect("accounting:dashboard")
    else:
        form = SetupWizardForm()
    return render(request, "core/setup_wizard.html", {"form": form})


@login_required
@require_permission(PermissionLevel.ADMIN)
def organization_settings(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = OrganizationForm(request.POST, instance=org)
        if form.is_valid():
            form.save()
            return redirect("core:organization_settings")
    else:
        form = OrganizationForm(instance=org)
    return render(request, "core/organization_settings.html", {"form": form})
