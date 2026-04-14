from django import forms
from core.models import Organization


class SetupWizardForm(forms.Form):
    org_name = forms.CharField(label="Nom de l'ASBL", max_length=255)
    org_address = forms.CharField(label="Adresse du siège social", widget=forms.Textarea(attrs={"rows": 2}))
    org_enterprise_number = forms.CharField(label="Numéro d'entreprise (BCE)", max_length=20, required=False)
    org_email = forms.EmailField(label="Email de l'ASBL", required=False)
    org_phone = forms.CharField(label="Téléphone", max_length=30, required=False)
    admin_username = forms.CharField(label="Nom d'utilisateur admin", max_length=150)
    admin_password = forms.CharField(label="Mot de passe admin", widget=forms.PasswordInput)
    admin_first_name = forms.CharField(label="Prénom", max_length=150, required=False)
    admin_last_name = forms.CharField(label="Nom", max_length=150, required=False)
    admin_email = forms.EmailField(label="Email admin", required=False)


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ("name", "address", "enterprise_number", "email", "phone", "logo")


class ImportForm(forms.Form):
    file = forms.FileField(label="Fichier de sauvegarde (.zip)")
