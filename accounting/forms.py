from django import forms
from accounting.models import AssetSnapshot, Budget, Category, Entry, FiscalYear

class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ("fiscal_year", "category", "date", "amount", "description", "attachment")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "class": "form-control"}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Cotisation Jean Dupont"}),
            "fiscal_year": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "date": "Date de l'opération (doit être dans l'exercice sélectionné).",
            "amount": "Montant en euros, minimum 0,01 €.",
            "category": "Choisissez la catégorie correspondant à cette opération.",
            "description": "Brève description de l'opération (ex : Cotisation Jean Dupont).",
            "attachment": "Optionnel. Joignez un scan ou une photo du justificatif (PDF, JPG, PNG…).",
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "category_type", "description")

class FiscalYearForm(forms.ModelForm):
    class Meta:
        model = FiscalYear
        fields = ("start_date", "end_date")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ("category", "planned_amount")
        widgets = {"planned_amount": forms.NumberInput(attrs={"step": "0.01"})}

class AssetSnapshotForm(forms.ModelForm):
    class Meta:
        model = AssetSnapshot
        fields = ("date", "cash", "bank", "receivables", "debts", "notes")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "cash": forms.NumberInput(attrs={"step": "0.01"}),
            "bank": forms.NumberInput(attrs={"step": "0.01"}),
            "receivables": forms.NumberInput(attrs={"step": "0.01"}),
            "debts": forms.NumberInput(attrs={"step": "0.01"}),
        }
