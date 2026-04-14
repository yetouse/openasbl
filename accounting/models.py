from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from decimal import Decimal


class FiscalYearStatus(models.TextChoices):
    OPEN = "open", "Ouvert"
    CLOSED = "closed", "Cl\u00f4tur\u00e9"


class CategoryType(models.TextChoices):
    INCOME = "income", "Recette"
    EXPENSE = "expense", "D\u00e9pense"


class FiscalYear(models.Model):
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="fiscal_years")
    start_date = models.DateField("Date de d\u00e9but")
    end_date = models.DateField("Date de fin")
    status = models.CharField("Statut", max_length=10, choices=FiscalYearStatus.choices, default=FiscalYearStatus.OPEN)

    class Meta:
        verbose_name = "Exercice comptable"
        verbose_name_plural = "Exercices comptables"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.start_date} \u2192 {self.end_date}"

    def clean(self):
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError("La date de fin doit \u00eatre post\u00e9rieure \u00e0 la date de d\u00e9but.")


class Category(models.Model):
    organization = models.ForeignKey("core.Organization", on_delete=models.CASCADE, related_name="categories")
    name = models.CharField("Nom", max_length=255)
    category_type = models.CharField("Type", max_length=10, choices=CategoryType.choices)
    description = models.TextField("Description", blank=True, default="")

    class Meta:
        verbose_name = "Cat\u00e9gorie"
        verbose_name_plural = "Cat\u00e9gories"
        ordering = ["category_type", "name"]
        unique_together = [("organization", "name", "category_type")]

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class Entry(models.Model):
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name="entries")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="entries")
    date = models.DateField("Date")
    amount = models.DecimalField("Montant", max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    description = models.CharField("Description", max_length=500)
    attachment = models.FileField("Justificatif", upload_to="attachments/%Y/%m/", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="entries")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "\u00c9criture"
        verbose_name_plural = "\u00c9critures"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} \u2014 {self.description} ({self.amount}\u20ac)"

    @property
    def entry_type(self):
        return self.category.category_type

    def clean(self):
        if self.fiscal_year_id and self.fiscal_year.status == FiscalYearStatus.CLOSED:
            raise ValidationError("Impossible d'ajouter une \u00e9criture sur un exercice cl\u00f4tur\u00e9.")
        if self.fiscal_year_id and self.date and not (self.fiscal_year.start_date <= self.date <= self.fiscal_year.end_date):
            raise ValidationError("La date de l'\u00e9criture doit \u00eatre comprise dans l'exercice comptable.")


class Budget(models.Model):
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name="budgets")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    planned_amount = models.DecimalField("Montant pr\u00e9vu", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"
        unique_together = [("fiscal_year", "category")]

    def __str__(self):
        return f"Budget {self.category.name} \u2014 {self.planned_amount}\u20ac"


class AssetSnapshot(models.Model):
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.CASCADE, related_name="asset_snapshots")
    date = models.DateField("Date du relev\u00e9")
    cash = models.DecimalField("Caisse", max_digits=12, decimal_places=2, default=Decimal("0"))
    bank = models.DecimalField("Banque", max_digits=12, decimal_places=2, default=Decimal("0"))
    receivables = models.DecimalField("Cr\u00e9ances", max_digits=12, decimal_places=2, default=Decimal("0"))
    debts = models.DecimalField("Dettes", max_digits=12, decimal_places=2, default=Decimal("0"))
    notes = models.TextField("Notes", blank=True, default="")

    class Meta:
        verbose_name = "\u00c9tat du patrimoine"
        verbose_name_plural = "\u00c9tats du patrimoine"
        ordering = ["-date"]

    def __str__(self):
        return f"Patrimoine au {self.date}"

    @property
    def net_worth(self):
        return self.cash + self.bank + self.receivables - self.debts
