import os
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.template.loader import render_to_string
from weasyprint import HTML


def _logo_path(organization):
    """Return the absolute file path to the organization's logo, or None."""
    if organization.logo:
        path = os.path.join(settings.MEDIA_ROOT, str(organization.logo))
        if os.path.exists(path):
            return path
    return None

from accounting.models import AssetSnapshot, Budget, Category, CategoryType, Entry, FiscalYear


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
    org = fiscal_year.organization
    context = {
        "fiscal_year": fiscal_year,
        "organization": org,
        "logo_path": _logo_path(org),
        "logo_path": _logo_path(org),
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

    org = fiscal_year.organization
    context = {
        "fiscal_year": fiscal_year,
        "organization": org,
        "logo_path": _logo_path(org),
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
    org = fiscal_year.organization
    context = {
        "fiscal_year": fiscal_year,
        "organization": org,
        "logo_path": _logo_path(org),
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


def generate_budget_tracking_pdf(fiscal_year):
    """Generate a PDF comparing budget vs actual by category."""
    org = fiscal_year.organization
    categories = Category.objects.filter(organization=org).order_by("category_type", "name")

    income_rows = []
    expense_rows = []
    total_budget_income = Decimal("0")
    total_actual_income = Decimal("0")
    total_budget_expense = Decimal("0")
    total_actual_expense = Decimal("0")

    for cat in categories:
        actual = (
            Entry.objects.filter(fiscal_year=fiscal_year, category=cat)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        budget = Budget.objects.filter(fiscal_year=fiscal_year, category=cat).first()
        planned = budget.planned_amount if budget else Decimal("0")
        diff = actual - planned
        pct = (actual / planned * 100) if planned else None

        row = {
            "category": cat,
            "planned": planned,
            "actual": actual,
            "diff": diff,
            "pct": pct,
        }

        if cat.category_type == CategoryType.INCOME:
            income_rows.append(row)
            total_budget_income += planned
            total_actual_income += actual
        else:
            expense_rows.append(row)
            total_budget_expense += planned
            total_actual_expense += actual

    actual_balance = total_actual_income - total_actual_expense
    budget_balance = total_budget_income - total_budget_expense

    context = {
        "fiscal_year": fiscal_year,
        "organization": org,
        "logo_path": _logo_path(org),
        "income_rows": income_rows,
        "expense_rows": expense_rows,
        "total_budget_income": total_budget_income,
        "total_actual_income": total_actual_income,
        "total_diff_income": total_actual_income - total_budget_income,
        "total_budget_expense": total_budget_expense,
        "total_actual_expense": total_actual_expense,
        "total_diff_expense": total_actual_expense - total_budget_expense,
        "budget_balance": budget_balance,
        "actual_balance": actual_balance,
        "diff_balance": actual_balance - budget_balance,
    }
    html_string = render_to_string("reports/budget_tracking_pdf.html", context)
    return HTML(string=html_string).write_pdf()


def generate_annual_accounts_pdf(fiscal_year):
    """Generate the annual accounts PDF (comptes annuels) — legal requirement for Belgian ASBLs."""
    org = fiscal_year.organization

    # Journal data
    entries = (
        Entry.objects.filter(fiscal_year=fiscal_year)
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

    # Category summaries
    categories = Category.objects.filter(organization=org).order_by("category_type", "name")
    income_summary = []
    expense_summary = []
    for cat in categories:
        total = (
            Entry.objects.filter(fiscal_year=fiscal_year, category=cat)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )
        if total == Decimal("0"):
            continue
        row = {"name": cat.name, "total": total}
        if cat.category_type == CategoryType.INCOME:
            income_summary.append(row)
        else:
            expense_summary.append(row)

    # Patrimony snapshots (opening and closing)
    snapshots = AssetSnapshot.objects.filter(fiscal_year=fiscal_year).order_by("date")
    opening_snapshot = snapshots.first()
    closing_snapshot = snapshots.last()
    if opening_snapshot and closing_snapshot and opening_snapshot.pk == closing_snapshot.pk:
        opening_snapshot = None  # Only one snapshot, treat as closing

    context = {
        "fiscal_year": fiscal_year,
        "organization": org,
        "logo_path": _logo_path(org),
        "entries": entries,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "income_summary": income_summary,
        "expense_summary": expense_summary,
        "opening_snapshot": opening_snapshot,
        "closing_snapshot": closing_snapshot,
    }
    html_string = render_to_string("reports/annual_accounts_pdf.html", context)
    return HTML(string=html_string).write_pdf()


def generate_year_comparison_pdf(fiscal_years):
    """Generate a PDF comparing income/expenses across multiple fiscal years."""
    categories = set()
    fy_data = []

    for fy in fiscal_years:
        org = fy.organization
        cats = Category.objects.filter(organization=org)
        income_by_cat = {}
        expense_by_cat = {}
        total_income = Decimal("0")
        total_expense = Decimal("0")

        for cat in cats:
            total = (
                Entry.objects.filter(fiscal_year=fy, category=cat)
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
            )
            if cat.category_type == CategoryType.INCOME:
                income_by_cat[cat.name] = total
                total_income += total
            else:
                expense_by_cat[cat.name] = total
                total_expense += total
            if total > 0:
                categories.add((cat.category_type, cat.name))

        fy_data.append({
            "fiscal_year": fy,
            "income_by_cat": income_by_cat,
            "expense_by_cat": expense_by_cat,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
        })

    # Build row-based data for easy template rendering
    income_cats = sorted(name for ct, name in categories if ct == CategoryType.INCOME)
    expense_cats = sorted(name for ct, name in categories if ct == CategoryType.EXPENSE)

    income_rows = []
    for cat_name in income_cats:
        row = {"name": cat_name, "amounts": [fd["income_by_cat"].get(cat_name, Decimal("0")) for fd in fy_data]}
        income_rows.append(row)

    expense_rows = []
    for cat_name in expense_cats:
        row = {"name": cat_name, "amounts": [fd["expense_by_cat"].get(cat_name, Decimal("0")) for fd in fy_data]}
        expense_rows.append(row)

    context = {
        "organization": fiscal_years[0].organization if fiscal_years else None,
        "logo_path": _logo_path(fiscal_years[0].organization) if fiscal_years else None,
        "fy_data": fy_data,
        "income_rows": income_rows,
        "expense_rows": expense_rows,
    }
    html_string = render_to_string("reports/year_comparison_pdf.html", context)
    return HTML(string=html_string).write_pdf()
