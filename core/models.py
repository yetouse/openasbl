from django.core.exceptions import ValidationError
from django.db import models


class Organization(models.Model):
    name = models.CharField("Nom de l'ASBL", max_length=255)
    address = models.TextField("Adresse du siège social")
    enterprise_number = models.CharField("Numéro d'entreprise (BCE)", max_length=20, blank=True, default="")
    email = models.EmailField("Email", blank=True, default="")
    phone = models.CharField("Téléphone", max_length=30, blank=True, default="")
    logo = models.ImageField("Logo", upload_to="logos/", blank=True)

    class Meta:
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"

    def __str__(self):
        return self.name

    def clean(self):
        if not self.pk and Organization.objects.exists():
            raise ValidationError("Une seule organisation peut être configurée par instance.")
