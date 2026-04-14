from django import forms
from django.contrib.auth.models import User
from accounts.models import PermissionLevel


class UserCreateForm(forms.Form):
    username = forms.CharField(label="Nom d'utilisateur", max_length=150)
    first_name = forms.CharField(label="Prénom", max_length=150, required=False)
    last_name = forms.CharField(label="Nom", max_length=150, required=False)
    email = forms.EmailField(label="Email", required=False)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput)
    permission_level = forms.ChoiceField(
        label="Niveau de permission",
        choices=PermissionLevel.choices,
        initial=PermissionLevel.LECTURE,
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return username

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "Les mots de passe ne correspondent pas.")
        return cleaned


class UserEditForm(forms.Form):
    first_name = forms.CharField(label="Prénom", max_length=150, required=False)
    last_name = forms.CharField(label="Nom", max_length=150, required=False)
    email = forms.EmailField(label="Email", required=False)
    is_active = forms.BooleanField(label="Actif", required=False, initial=True)
    permission_level = forms.ChoiceField(
        label="Niveau de permission",
        choices=PermissionLevel.choices,
    )


class UserPasswordForm(forms.Form):
    password = forms.CharField(label="Nouveau mot de passe", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Confirmer", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "Les mots de passe ne correspondent pas.")
        return cleaned
