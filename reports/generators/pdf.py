from decimal import Decimal

from django.db.models import Sum
from django.template.loader import render_to_string
from weasyprint import HTML

from accounting.models import AssetSnapshot, Budget, Category, CategoryType, Entry

MONTH_NAMES_FR = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


def generate_journal_pdf(fiscal_year):
    """Generate a PDF of the journal for a given fiscal year."""
    entries = Entry.objects.filter(fiscal_year=fiscal_year).select_related("category").order_by("date", "pk")

    total_income = Decimal("0")
    total_expense = Decimal("0")
    rows = []
    for entry in entries:
        income = entry.amount if entry.entry_type == CategoryType.INCOME else None
        expense = entry.amount if entry.entry_type == CategoryType.EXPENSE else None
        if income:
            total_income += income
        if expense:
            total_expense += expense
        rows.append(
            {
                "date": entry.date,
                "description": entry.description,
                "category": entry.category.name,
                "income": income,
                "expense": expense,
            }
        )

    balance = total_income - total_expense
    context = {
        "fiscal_year": fiscal_year,
        "organization": fiscal_year.organization,
        "rows": rows,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
    }
    html_string = render_to_string("reports/journal_pdf.html", context)
    return HTML(string=html_string).write_pdf()


def generate_patrimony_pdf(fiscal_year):
    """Generate a PDF of the patrimony state for a given fiscal year."""
    snapshot = (
        AssetSnapshot.objects.filter(fiscal_year=fiscal_year).order_by("-date").first()
    )

    context = {
        "fiscal_year": fiscal_year,
        "organization": fiscal_year.organization,
        "snapshot": snapshot,
    }
    html_string = render_to_string("reports/patrimony_pdf.html", context)
    return HTML(string=html_string).write_pdf()


def generate_monthly_ca_pdf(fiscal_year, year, month):
    """Generate a PDF of the monthly board report."""
    entries = (
        Entry.objects.filter(fiscal_year=fiscal_year, date__year=year, date__month=month)
        .select_related("category")
        .order_by("date", "pk")
    )

    total_income = Decimal("0")
    total_expense = Decimal("0")
    for entry in entries:
        if entry.entry_type == CategoryType.INCOME:
            total_income += entry.amount
        else:
            total_expense += entry.amount

    # Category breakdown with budget comparison
    categories = Category.objects.filter(organization=fiscal_year.organization).order_by(
        "category_type", "name"
    )
    breakdown = []
    for cat in categories:
        actual = (
            entries.filter(category=cat).aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        budget = Budget.objects.filter(fiscal_year=fiscal_year, category=cat).first()
        planned = budget.planned_amount if budget else Decimal("0")
        diff = actual - planned
        breakdown.append(
            {
                "category": cat,
                "planned": planned,
                "actual": actual,
                "diff": diff,
            }
        )

    month_name = MONTH_NAMES_FR[month]
    context = {
        "fiscal_year": fiscal_year,
        "organization": fiscal_year.organization,
        "year": year,
        "month": month,
        "month_name": month_name,
        "entries": entries,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "breakdown": breakdown,
    }
    html_string = render_to_string("reports/monthly_ca_pdf.html", context)
    return HTML(string=html_string).write_pdf()
