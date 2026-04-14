import csv
import io
from decimal import Decimal

from openpyxl import Workbook

from accounting.models import CategoryType, Entry


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
