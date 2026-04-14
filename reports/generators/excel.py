import csv
import io
from decimal import Decimal

from openpyxl import Workbook

from accounting.models import AssetSnapshot, Budget, Category, CategoryType, Entry


def generate_journal_excel(fiscal_year):
    """Generate an Excel workbook of the journal for a given fiscal year."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Journal"

    headers = ["Date", "Description", "Catégorie", "Recette", "Dépense"]
    ws.append(headers)

    entries = Entry.objects.filter(fiscal_year=fiscal_year).select_related("category").order_by("date", "pk")

    total_income = Decimal("0")
    total_expense = Decimal("0")
    for entry in entries:
        income = entry.amount if entry.entry_type == CategoryType.INCOME else None
        expense = entry.amount if entry.entry_type == CategoryType.EXPENSE else None
        if income:
            total_income += income
        if expense:
            total_expense += expense
        ws.append(
            [
                entry.date.isoformat(),
                entry.description,
                entry.category.name,
                float(income) if income else "",
                float(expense) if expense else "",
            ]
        )

    ws.append([])
    ws.append(["", "", "TOTAUX", float(total_income), float(total_expense)])
    ws.append(["", "", "SOLDE", float(total_income - total_expense)])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def generate_journal_csv(fiscal_year):
    """Generate a CSV string of the journal for a given fiscal year."""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    headers = ["Date", "Description", "Catégorie", "Recette", "Dépense"]
    writer.writerow(headers)

    entries = Entry.objects.filter(fiscal_year=fiscal_year).select_related("category").order_by("date", "pk")

    total_income = Decimal("0")
    total_expense = Decimal("0")
    for entry in entries:
        income = entry.amount if entry.entry_type == CategoryType.INCOME else None
        expense = entry.amount if entry.entry_type == CategoryType.EXPENSE else None
        if income:
            total_income += income
        if expense:
            total_expense += expense
        writer.writerow(
            [
                entry.date.isoformat(),
                entry.description,
                entry.category.name,
                str(income) if income else "",
                str(expense) if expense else "",
            ]
        )

    writer.writerow([])
    writer.writerow(["", "", "TOTAUX", str(total_income), str(total_expense)])
    writer.writerow(["", "", "SOLDE", str(total_income - total_expense)])

    return output.getvalue()


def generate_budget_tracking_excel(fiscal_year):
    """Generate an Excel workbook comparing budget vs actual by category."""
    from django.db.models import Sum

    wb = Workbook()
    org = fiscal_year.organization
    categories = Category.objects.filter(organization=org).order_by("category_type", "name")

    # Income sheet
    ws_income = wb.active
    ws_income.title = "Recettes"
    ws_income.append(["Catégorie", "Budget", "Réalisé", "Écart", "%"])

    total_budget_income = Decimal("0")
    total_actual_income = Decimal("0")
    for cat in categories:
        if cat.category_type != CategoryType.INCOME:
            continue
        actual = Entry.objects.filter(fiscal_year=fiscal_year, category=cat).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        budget = Budget.objects.filter(fiscal_year=fiscal_year, category=cat).first()
        planned = budget.planned_amount if budget else Decimal("0")
        diff = actual - planned
        pct = float(actual / planned * 100) if planned else None
        ws_income.append([cat.name, float(planned), float(actual), float(diff), pct or ""])
        total_budget_income += planned
        total_actual_income += actual

    ws_income.append([])
    ws_income.append(["TOTAL", float(total_budget_income), float(total_actual_income), float(total_actual_income - total_budget_income)])

    # Expense sheet
    ws_expense = wb.create_sheet("Dépenses")
    ws_expense.append(["Catégorie", "Budget", "Réalisé", "Écart", "%"])

    total_budget_expense = Decimal("0")
    total_actual_expense = Decimal("0")
    for cat in categories:
        if cat.category_type != CategoryType.EXPENSE:
            continue
        actual = Entry.objects.filter(fiscal_year=fiscal_year, category=cat).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        budget = Budget.objects.filter(fiscal_year=fiscal_year, category=cat).first()
        planned = budget.planned_amount if budget else Decimal("0")
        diff = actual - planned
        pct = float(actual / planned * 100) if planned else None
        ws_expense.append([cat.name, float(planned), float(actual), float(diff), pct or ""])
        total_budget_expense += planned
        total_actual_expense += actual

    ws_expense.append([])
    ws_expense.append(["TOTAL", float(total_budget_expense), float(total_actual_expense), float(total_actual_expense - total_budget_expense)])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def generate_annual_accounts_excel(fiscal_year):
    """Generate an Excel workbook for the annual accounts (comptes annuels)."""
    from django.db.models import Sum

    wb = Workbook()
    org = fiscal_year.organization

    # Sheet 1: Summary by category
    ws_summary = wb.active
    ws_summary.title = "Résumé"
    ws_summary.append([f"Comptes annuels — {org.name}"])
    ws_summary.append([f"Exercice {fiscal_year.start_date} → {fiscal_year.end_date}"])
    ws_summary.append([])

    categories = Category.objects.filter(organization=org).order_by("category_type", "name")
    total_income = Decimal("0")
    total_expense = Decimal("0")

    ws_summary.append(["RECETTES"])
    ws_summary.append(["Catégorie", "Montant"])
    for cat in categories:
        if cat.category_type != CategoryType.INCOME:
            continue
        total = Entry.objects.filter(fiscal_year=fiscal_year, category=cat).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        if total > 0:
            ws_summary.append([cat.name, float(total)])
            total_income += total
    ws_summary.append(["TOTAL RECETTES", float(total_income)])
    ws_summary.append([])

    ws_summary.append(["DÉPENSES"])
    ws_summary.append(["Catégorie", "Montant"])
    for cat in categories:
        if cat.category_type != CategoryType.EXPENSE:
            continue
        total = Entry.objects.filter(fiscal_year=fiscal_year, category=cat).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        if total > 0:
            ws_summary.append([cat.name, float(total)])
            total_expense += total
    ws_summary.append(["TOTAL DÉPENSES", float(total_expense)])
    ws_summary.append([])
    ws_summary.append(["RÉSULTAT", float(total_income - total_expense)])

    # Sheet 2: Full journal
    ws_journal = wb.create_sheet("Journal")
    ws_journal.append(["Date", "Description", "Catégorie", "Recette", "Dépense"])
    entries = Entry.objects.filter(fiscal_year=fiscal_year).select_related("category").order_by("date", "pk")
    for entry in entries:
        income = float(entry.amount) if entry.entry_type == CategoryType.INCOME else ""
        expense = float(entry.amount) if entry.entry_type == CategoryType.EXPENSE else ""
        ws_journal.append([entry.date.isoformat(), entry.description, entry.category.name, income, expense])
    ws_journal.append([])
    ws_journal.append(["", "", "TOTAUX", float(total_income), float(total_expense)])
    ws_journal.append(["", "", "SOLDE", float(total_income - total_expense)])

    # Sheet 3: Patrimony
    ws_patrimony = wb.create_sheet("Patrimoine")
    ws_patrimony.append(["État du patrimoine"])
    snapshot = AssetSnapshot.objects.filter(fiscal_year=fiscal_year).order_by("-date").first()
    if snapshot:
        ws_patrimony.append([f"Relevé au {snapshot.date}"])
        ws_patrimony.append([])
        ws_patrimony.append(["Poste", "Montant"])
        ws_patrimony.append(["Caisse", float(snapshot.cash)])
        ws_patrimony.append(["Banque", float(snapshot.bank)])
        ws_patrimony.append(["Créances", float(snapshot.receivables)])
        ws_patrimony.append(["Dettes", float(snapshot.debts)])
        ws_patrimony.append([])
        ws_patrimony.append(["Valeur nette", float(snapshot.net_worth)])
    else:
        ws_patrimony.append(["Aucun relevé disponible"])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
