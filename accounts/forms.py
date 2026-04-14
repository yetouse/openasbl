from django import forms
from django.contrib.auth.models import User
from accounts.models import PermissionLevel, UserProfile

class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    permission_level = forms.ChoiceField(choices=PermissionLevel.choices, label="Niveau de permission")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {"username": "Nom d'utilisateur", "first_name": "Prénom", "last_name": "Nom", "email": "Email"}
