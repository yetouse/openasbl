from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import require_permission
from accounts.models import PermissionLevel
from accounting.forms import AssetSnapshotForm, CategoryForm, EntryForm, FiscalYearForm
from accounting.models import AssetSnapshot, Budget, Category, CategoryType, Entry, FiscalYear, FiscalYearStatus

@login_required
def dashboard(request):
    org = request.user.profile.organization
    fiscal_years = FiscalYear.objects.filter(organization=org)
    current_fy = fiscal_years.filter(status="open").first()
    summary = {}
    budget_summary = None
    recent_entries = []
    if current_fy:
        income = Entry.objects.filter(fiscal_year=current_fy, category__category_type=CategoryType.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        expenses = Entry.objects.filter(fiscal_year=current_fy, category__category_type=CategoryType.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
        summary = {"income": income, "expenses": expenses, "balance": income - expenses, "entry_count": Entry.objects.filter(fiscal_year=current_fy).count()}

        # Budget progress
        budgets = Budget.objects.filter(fiscal_year=current_fy).select_related("category")
        if budgets.exists():
            budget_income = sum(b.planned_amount for b in budgets if b.category.category_type == CategoryType.INCOME)
            budget_expense = sum(b.planned_amount for b in budgets if b.category.category_type == CategoryType.EXPENSE)
            income_pct = int(income / budget_income * 100) if budget_income else 0
            expense_pct = int(expenses / budget_expense * 100) if budget_expense else 0
            budget_summary = {
                "budget_income": budget_income, "actual_income": income, "income_pct": income_pct,
                "budget_expense": budget_expense, "actual_expense": expenses, "expense_pct": expense_pct,
            }

        # Recent entries
        recent_entries = Entry.objects.filter(fiscal_year=current_fy).select_related("category").order_by("-date", "-created_at")[:5]

    return render(request, "accounting/dashboard.html", {
        "fiscal_years": fiscal_years, "current_fy": current_fy, "summary": summary,
        "budget_summary": budget_summary, "recent_entries": recent_entries,
    })

@login_required
def entry_list(request):
    org = request.user.profile.organization
    fiscal_year_id = request.GET.get("fiscal_year")
    category_id = request.GET.get("category")
    entry_type = request.GET.get("type")
    search_query = request.GET.get("q", "").strip()

    entries = Entry.objects.select_related("category", "created_by").filter(fiscal_year__organization=org)
    if fiscal_year_id:
        entries = entries.filter(fiscal_year_id=fiscal_year_id)
    if category_id:
        entries = entries.filter(category_id=category_id)
    if entry_type:
        entries = entries.filter(category__category_type=entry_type)
    if search_query:
        entries = entries.filter(description__icontains=search_query)

    # Compute totals for filtered results
    income = entries.filter(category__category_type=CategoryType.INCOME).aggregate(total=Sum("amount"))["total"] or 0
    expenses = entries.filter(category__category_type=CategoryType.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
    totals = {"income": income, "expenses": expenses, "balance": income - expenses, "count": entries.count()}

    fiscal_years = FiscalYear.objects.filter(organization=org)
    categories = Category.objects.filter(organization=org).order_by("category_type", "name")
    return render(request, "accounting/entry_list.html", {
        "entries": entries, "fiscal_years": fiscal_years, "categories": categories,
        "selected_fy": fiscal_year_id, "selected_type": entry_type,
        "selected_category": category_id, "search_query": search_query, "totals": totals,
    })

@login_required
@require_permission(PermissionLevel.GESTION)
def entry_create(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.full_clean()
            entry.save()
            messages.success(request, "Écriture enregistrée.")
            if "save_and_new" in request.POST:
                return redirect("accounting:entry_create")
            return redirect("accounting:entry_list")
    else:
        import datetime
        open_fy = FiscalYear.objects.filter(organization=org, status="open").first()
        form = EntryForm(initial={
            "date": datetime.date.today(),
            "fiscal_year": open_fy.pk if open_fy else None,
        })
    form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(organization=org, status="open")
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/entry_create_form.html", {"form": form, "title": "Nouvelle écriture", "save_and_new": True})

@login_required
@require_permission(PermissionLevel.GESTION)
def entry_edit(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    org = request.user.profile.organization
    if request.method == "POST":
        form = EntryForm(request.POST, request.FILES, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.full_clean()
            entry.save()
            messages.success(request, "Ecriture modifiee.")
            return redirect("accounting:entry_list")
    else:
        form = EntryForm(instance=entry)
    form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(organization=org, status="open")
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Modifier l'ecriture"})

@login_required
@require_permission(PermissionLevel.GESTION)
def entry_delete(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Ecriture supprimee.")
    return redirect("accounting:entry_list")

@login_required
def fiscal_year_list(request):
    org = request.user.profile.organization
    fiscal_years = FiscalYear.objects.filter(organization=org)

    fy_data = []
    for fy in fiscal_years:
        income = Entry.objects.filter(fiscal_year=fy, category__category_type=CategoryType.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        expenses = Entry.objects.filter(fiscal_year=fy, category__category_type=CategoryType.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
        entry_count = Entry.objects.filter(fiscal_year=fy).count()
        fy_data.append({
            "fy": fy,
            "income": income,
            "expenses": expenses,
            "balance": income - expenses,
            "entry_count": entry_count,
        })

    return render(request, "accounting/fiscal_year_list.html", {"fy_data": fy_data})

@login_required
@require_permission(PermissionLevel.GESTION)
def fiscal_year_create(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = FiscalYearForm(request.POST)
        if form.is_valid():
            fy = form.save(commit=False)
            fy.organization = org
            fy.full_clean()
            fy.save()
            messages.success(request, "Exercice comptable créé.")
            return redirect("accounting:fiscal_year_list")
    else:
        form = FiscalYearForm()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Nouvel exercice"})

@login_required
@require_permission(PermissionLevel.VALIDATION)
def fiscal_year_close(request, pk):
    fy = get_object_or_404(FiscalYear, pk=pk)
    if request.method == "POST":
        fy.status = FiscalYearStatus.CLOSED
        fy.save()
        messages.success(request, f"Exercice {fy} clôturé.")
        return redirect("accounting:fiscal_year_list")
    return render(request, "accounting/fiscal_year_close.html", {"fiscal_year": fy})

@login_required
def category_list(request):
    org = request.user.profile.organization
    categories = Category.objects.filter(organization=org)
    return render(request, "accounting/category_list.html", {"categories": categories})

@login_required
@require_permission(PermissionLevel.GESTION)
def category_create(request):
    org = request.user.profile.organization
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.organization = org
            cat.save()
            messages.success(request, "Catégorie créée.")
            return redirect("accounting:category_list")
    else:
        form = CategoryForm()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Nouvelle catégorie"})


@login_required
@require_permission(PermissionLevel.GESTION)
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, "Catégorie modifiée.")
            return redirect("accounting:category_list")
    else:
        form = CategoryForm(instance=cat)
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Modifier la catégorie"})


@login_required
@require_permission(PermissionLevel.GESTION)
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        if cat.entries.exists():
            messages.error(request, "Impossible de supprimer une catégorie utilisée par des écritures.")
        else:
            cat.delete()
            messages.success(request, "Catégorie supprimée.")
    return redirect("accounting:category_list")

@login_required
@require_permission(PermissionLevel.GESTION)
def budget_create(request, fiscal_year_pk):
    fy = get_object_or_404(FiscalYear, pk=fiscal_year_pk)
    org = request.user.profile.organization
    categories = Category.objects.filter(organization=org).order_by("category_type", "name")

    if request.method == "POST":
        count = 0
        for cat in categories:
            amount_str = request.POST.get(f"budget_{cat.pk}", "").strip()
            if not amount_str:
                Budget.objects.filter(fiscal_year=fy, category=cat).delete()
                continue
            try:
                amount = Decimal(amount_str)
            except InvalidOperation:
                continue
            if amount <= 0:
                Budget.objects.filter(fiscal_year=fy, category=cat).delete()
                continue
            Budget.objects.update_or_create(
                fiscal_year=fy, category=cat,
                defaults={"planned_amount": amount},
            )
            count += 1
        messages.success(request, f"{count} budgets enregistrés.")
        return redirect("accounting:fiscal_year_list")

    # Build items with existing amounts (or copy from another fiscal year)
    existing = {b.category_id: b.planned_amount for b in Budget.objects.filter(fiscal_year=fy)}
    copy_from_pk = request.GET.get("copy_from")
    if copy_from_pk and not existing:
        existing = {b.category_id: b.planned_amount for b in Budget.objects.filter(fiscal_year_id=copy_from_pk)}

    income_items = [{"category": c, "amount": existing.get(c.pk)} for c in categories if c.category_type == CategoryType.INCOME]
    expense_items = [{"category": c, "amount": existing.get(c.pk)} for c in categories if c.category_type == CategoryType.EXPENSE]

    # Find previous fiscal year for copy button
    previous_fy = FiscalYear.objects.filter(
        organization=org, start_date__lt=fy.start_date
    ).order_by("-start_date").first()
    has_previous_budget = previous_fy and Budget.objects.filter(fiscal_year=previous_fy).exists()

    return render(request, "accounting/budget_bulk_form.html", {
        "fiscal_year": fy, "income_items": income_items, "expense_items": expense_items,
        "previous_fy": previous_fy if has_previous_budget else None,
    })

@login_required
def budget_tracking(request, pk):
    fy = get_object_or_404(FiscalYear, pk=pk)
    org = request.user.profile.organization
    categories = Category.objects.filter(organization=org).order_by("category_type", "name")

    income_rows = []
    expense_rows = []
    total_budget_income = total_actual_income = 0
    total_budget_expense = total_actual_expense = 0

    for cat in categories:
        actual = Entry.objects.filter(fiscal_year=fy, category=cat).aggregate(total=Sum("amount"))["total"] or 0
        budget = Budget.objects.filter(fiscal_year=fy, category=cat).first()
        planned = budget.planned_amount if budget else 0
        diff = actual - planned
        pct = int(actual / planned * 100) if planned else None

        row = {"category": cat, "planned": planned, "actual": actual, "diff": diff, "pct": pct}
        if cat.category_type == CategoryType.INCOME:
            income_rows.append(row)
            total_budget_income += planned
            total_actual_income += actual
        else:
            expense_rows.append(row)
            total_budget_expense += planned
            total_actual_expense += actual

    return render(request, "accounting/budget_tracking.html", {
        "fiscal_year": fy,
        "income_rows": income_rows,
        "expense_rows": expense_rows,
        "total_budget_income": total_budget_income,
        "total_actual_income": total_actual_income,
        "total_budget_expense": total_budget_expense,
        "total_actual_expense": total_actual_expense,
        "actual_balance": total_actual_income - total_actual_expense,
        "budget_balance": total_budget_income - total_budget_expense,
    })


@login_required
@require_permission(PermissionLevel.VALIDATION)
def asset_snapshot_create(request, fiscal_year_pk):
    fy = get_object_or_404(FiscalYear, pk=fiscal_year_pk)
    if request.method == "POST":
        form = AssetSnapshotForm(request.POST)
        if form.is_valid():
            snapshot = form.save(commit=False)
            snapshot.fiscal_year = fy
            snapshot.save()
            messages.success(request, "État du patrimoine enregistré.")
            return redirect("accounting:fiscal_year_list")
    else:
        form = AssetSnapshotForm()
    return render(request, "accounting/asset_snapshot_form.html", {"form": form, "fiscal_year": fy})
