from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import require_permission
from accounts.forms import UserCreateForm, UserEditForm, UserPasswordForm
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


@login_required
@require_permission(PermissionLevel.ADMIN)
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data.get("first_name", ""),
                last_name=form.cleaned_data.get("last_name", ""),
                email=form.cleaned_data.get("email", ""),
            )
            org = request.user.profile.organization
            UserProfile.objects.create(
                user=user,
                organization=org,
                permission_level=form.cleaned_data["permission_level"],
            )
            messages.success(request, f"Utilisateur « {user.username} » créé.")
            return redirect("accounts:user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {"form": form, "title": "Créer un utilisateur"})


@login_required
@require_permission(PermissionLevel.ADMIN)
def user_edit(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    profile = get_object_or_404(UserProfile, user=target_user)

    if request.method == "POST":
        form = UserEditForm(request.POST)
        if form.is_valid():
            target_user.first_name = form.cleaned_data["first_name"]
            target_user.last_name = form.cleaned_data["last_name"]
            target_user.email = form.cleaned_data["email"]
            target_user.is_active = form.cleaned_data["is_active"]
            target_user.save()
            profile.permission_level = form.cleaned_data["permission_level"]
            profile.save()
            messages.success(request, f"Utilisateur « {target_user.username} » modifié.")
            return redirect("accounts:user_list")
    else:
        form = UserEditForm(initial={
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
            "email": target_user.email,
            "is_active": target_user.is_active,
            "permission_level": profile.permission_level,
        })
    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": f"Modifier — {target_user.username}",
        "target_user": target_user,
    })


@login_required
@require_permission(PermissionLevel.ADMIN)
def user_password(request, pk):
    target_user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserPasswordForm(request.POST)
        if form.is_valid():
            target_user.set_password(form.cleaned_data["password"])
            target_user.save()
            messages.success(request, f"Mot de passe de « {target_user.username} » modifié.")
            return redirect("accounts:user_list")
    else:
        form = UserPasswordForm()
    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": f"Mot de passe — {target_user.username}",
        "target_user": target_user,
    })


@login_required
@require_permission(PermissionLevel.ADMIN)
def user_delete(request, pk):
    target_user = get_object_or_404(User, pk=pk)

    # Prevent self-deletion
    if target_user == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("accounts:user_list")

    if request.method == "POST":
        username = target_user.username
        target_user.delete()
        messages.success(request, f"Utilisateur « {username} » supprimé.")
        return redirect("accounts:user_list")

    return render(request, "accounts/user_confirm_delete.html", {"target_user": target_user})
