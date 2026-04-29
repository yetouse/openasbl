import datetime
import json
import mimetypes
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from accounts.decorators import require_permission
from accounts.models import PermissionLevel
from accounting.forms import AssetSnapshotForm, CategoryForm, EntryForm, FiscalYearForm
from accounting.models import AssetSnapshot, Budget, Category, CategoryType, Entry, FiscalYear, FiscalYearStatus
from accounting.ocr import extract_from_image


_CATEGORY_KEYWORDS = {
    "cotisation": CategoryType.INCOME,
    "cotisations": CategoryType.INCOME,
    "adhésion": CategoryType.INCOME,
    "adhésions": CategoryType.INCOME,
    "don": CategoryType.INCOME,
    "dons": CategoryType.INCOME,
    "subside": CategoryType.INCOME,
    "subsides": CategoryType.INCOME,
    "subvention": CategoryType.INCOME,
    "subventions": CategoryType.INCOME,
    "recette": CategoryType.INCOME,
    "vente": CategoryType.INCOME,
    "facture": CategoryType.EXPENSE,
    "assurance": CategoryType.EXPENSE,
    "loyer": CategoryType.EXPENSE,
    "essence": CategoryType.EXPENSE,
    "carburant": CategoryType.EXPENSE,
    "fournitures": CategoryType.EXPENSE,
    "achat": CategoryType.EXPENSE,
    "achats": CategoryType.EXPENSE,
    "frais": CategoryType.EXPENSE,
    "électricité": CategoryType.EXPENSE,
    "eau": CategoryType.EXPENSE,
    "internet": CategoryType.EXPENSE,
    "téléphone": CategoryType.EXPENSE,
    "remboursement": CategoryType.EXPENSE,
}


def _suggest_category(description, org):
    """Return a Category pk based on description keywords, or None."""
    if not description:
        return None
    words = description.lower().split()
    for word in words:
        cat_type = _CATEGORY_KEYWORDS.get(word)
        if cat_type:
            cat = Category.objects.filter(organization=org, category_type=cat_type).first()
            if cat:
                return cat.pk
    return None


def _monthly_data(fiscal_year):
    """Build monthly income/expense totals for a fiscal year."""
    months = defaultdict(lambda: {"income": Decimal("0"), "expense": Decimal("0")})
    entries = Entry.objects.filter(fiscal_year=fiscal_year).values(
        "date__year", "date__month", "category__category_type"
    ).annotate(total=Sum("amount"))
    for row in entries:
        key = f"{row['date__year']}-{row['date__month']:02d}"
        if row["category__category_type"] == CategoryType.INCOME:
            months[key]["income"] = row["total"]
        else:
            months[key]["expense"] = row["total"]
    return dict(months)


@login_required
def dashboard(request):
    org = request.user.profile.organization
    can_edit = request.user.profile.can_edit
    fiscal_years = FiscalYear.objects.filter(organization=org)
    current_fy = fiscal_years.filter(status="open").first()
    summary = {}
    budget_summary = None
    dashboard_alerts = []
    latest_asset_snapshot = None
    recent_entries = []
    chart_data = None
    if current_fy:
        income = Entry.objects.filter(fiscal_year=current_fy, category__category_type=CategoryType.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        expenses = Entry.objects.filter(fiscal_year=current_fy, category__category_type=CategoryType.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
        summary = {"income": income, "expenses": expenses, "balance": income - expenses, "entry_count": Entry.objects.filter(fiscal_year=current_fy).count()}

        # Budget progress and treasurer alerts
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
            if budget_expense and expense_pct > 100:
                dashboard_alerts.append({
                    "level": "danger",
                    "title": "Dépenses au-dessus du budget",
                    "message": f"Les dépenses atteignent {expense_pct}% du budget prévu.",
                    "href": reverse("accounting:budget_tracking", args=[current_fy.pk]),
                    "requires_edit": False,
                    "action": "Voir le détail",
                })
            elif budget_expense and expense_pct >= 75:
                dashboard_alerts.append({
                    "level": "warning",
                    "title": "Budget dépenses à surveiller",
                    "message": f"Les dépenses atteignent {expense_pct}% du budget prévu.",
                    "href": reverse("accounting:budget_tracking", args=[current_fy.pk]),
                    "requires_edit": False,
                    "action": "Analyser",
                })
        else:
            dashboard_alerts.append({
                "level": "warning",
                "title": "Budget à préparer",
                "message": "Aucun budget n'est encore encodé pour l'exercice ouvert.",
                "href": reverse("accounting:budget_create", args=[current_fy.pk]),
                "requires_edit": True,
                "action": "Encoder le budget",
            })

        latest_asset_snapshot = AssetSnapshot.objects.filter(fiscal_year=current_fy).order_by("-date").first()
        if not latest_asset_snapshot:
            dashboard_alerts.append({
                "level": "info",
                "title": "Patrimoine non renseigné",
                "message": "Ajoutez un relevé caisse/banque pour suivre le patrimoine net.",
                "href": reverse("accounting:asset_snapshot_create", args=[current_fy.pk]),
                "requires_edit": True,
                "action": "Ajouter le patrimoine",
            })

        # Recent entries
        recent_entries = Entry.objects.filter(fiscal_year=current_fy).select_related("category").order_by("-date", "-created_at")[:5]

        # Chart data: monthly comparison with previous year
        previous_fy = FiscalYear.objects.filter(
            organization=org, start_date__lt=current_fy.start_date
        ).order_by("-start_date").first()

        current_monthly = _monthly_data(current_fy)
        previous_monthly = _monthly_data(previous_fy) if previous_fy else {}

        # Build ordered month labels from current fiscal year range
        from datetime import date
        labels = []
        d = current_fy.start_date.replace(day=1)
        end = current_fy.end_date
        while d <= end:
            labels.append(f"{d.year}-{d.month:02d}")
            if d.month == 12:
                d = d.replace(year=d.year + 1, month=1)
            else:
                d = d.replace(month=d.month + 1)

        # Previous year labels (offset by 1 year back)
        prev_labels = []
        if previous_fy:
            pd = previous_fy.start_date.replace(day=1)
            p_end = previous_fy.end_date
            while pd <= p_end:
                prev_labels.append(f"{pd.year}-{pd.month:02d}")
                if pd.month == 12:
                    pd = pd.replace(year=pd.year + 1, month=1)
                else:
                    pd = pd.replace(month=pd.month + 1)

        MONTH_NAMES = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

        display_labels = [MONTH_NAMES[int(l.split("-")[1])] for l in labels]

        cur_income = [float(current_monthly.get(l, {}).get("income", 0)) for l in labels]
        cur_expense = [float(current_monthly.get(l, {}).get("expense", 0)) for l in labels]
        prev_income = [float(previous_monthly.get(l, {}).get("income", 0)) for l in prev_labels] if prev_labels else []
        prev_expense = [float(previous_monthly.get(l, {}).get("expense", 0)) for l in prev_labels] if prev_labels else []

        # Pad previous year data to match current year length
        while len(prev_income) < len(labels):
            prev_income.append(0)
            prev_expense.append(0)
        prev_income = prev_income[:len(labels)]
        prev_expense = prev_expense[:len(labels)]

        # Cumulative balance
        cumul_current = []
        running = 0
        for i in range(len(labels)):
            running += cur_income[i] - cur_expense[i]
            cumul_current.append(round(running, 2))

        cumul_previous = []
        running = 0
        for i in range(len(labels)):
            running += prev_income[i] - prev_expense[i]
            cumul_previous.append(round(running, 2))

        # Expense breakdown by category (pie chart)
        expense_by_cat = Entry.objects.filter(
            fiscal_year=current_fy, category__category_type=CategoryType.EXPENSE
        ).values("category__name").annotate(total=Sum("amount")).order_by("-total")

        pie_labels = [row["category__name"] for row in expense_by_cat]
        pie_values = [float(row["total"]) for row in expense_by_cat]

        chart_data = json.dumps({
            "labels": display_labels,
            "current_income": cur_income,
            "current_expense": cur_expense,
            "previous_income": prev_income,
            "previous_expense": prev_expense,
            "cumul_current": cumul_current,
            "cumul_previous": cumul_previous,
            "has_previous": previous_fy is not None,
            "current_fy_label": str(current_fy),
            "previous_fy_label": str(previous_fy) if previous_fy else "",
            "pie_labels": pie_labels,
            "pie_values": pie_values,
        })

    return render(request, "accounting/dashboard.html", {
        "fiscal_years": fiscal_years, "current_fy": current_fy, "summary": summary,
        "can_edit": can_edit,
        "budget_summary": budget_summary, "dashboard_alerts": dashboard_alerts,
        "latest_asset_snapshot": latest_asset_snapshot, "recent_entries": recent_entries,
        "chart_data": chart_data,
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
    suggested_category = None

    if request.method == "POST":
        post_data = request.POST.copy()
        if not post_data.get("category") and post_data.get("description"):
            suggested_pk = _suggest_category(post_data["description"], org)
            if suggested_pk:
                post_data["category"] = suggested_pk
                suggested_category = Category.objects.filter(pk=suggested_pk).first()
        form = EntryForm(post_data, request.FILES)
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
        open_fy = FiscalYear.objects.filter(organization=org, status="open").first()
        entry_type = request.GET.get("type")
        description = request.GET.get("description", "")

        initial_category = None
        if entry_type in (CategoryType.INCOME, CategoryType.EXPENSE):
            cat = Category.objects.filter(organization=org, category_type=entry_type).first()
            if cat:
                initial_category = cat.pk
        elif description:
            suggested_pk = _suggest_category(description, org)
            if suggested_pk:
                initial_category = suggested_pk
                suggested_category = Category.objects.filter(pk=suggested_pk).first()

        if initial_category is None:
            last_entry = Entry.objects.filter(
                created_by=request.user,
                fiscal_year__organization=org,
            ).order_by("-created_at").first()
            if last_entry:
                initial_category = last_entry.category_id

        form = EntryForm(initial={
            "date": datetime.date.today(),
            "fiscal_year": open_fy.pk if open_fy else None,
            "category": initial_category,
        })

    form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(organization=org, status="open")
    category_qs = org.categories.all()
    if request.method == "GET":
        type_filter = request.GET.get("type")
        if type_filter in (CategoryType.INCOME, CategoryType.EXPENSE):
            category_qs = category_qs.filter(category_type=type_filter)
    form.fields["category"].queryset = category_qs

    entry_mode = None
    if request.method == "GET":
        raw_type = request.GET.get("type")
        if raw_type in (CategoryType.INCOME, CategoryType.EXPENSE):
            entry_mode = raw_type

    recent_cat_rows = (
        Entry.objects.filter(fiscal_year__organization=org)
        .values("category_id")
        .annotate(last_used=Max("created_at"))
        .order_by("-last_used")[:3]
    )
    ids = [row["category_id"] for row in recent_cat_rows]
    cats_by_id = {c.pk: c for c in Category.objects.filter(pk__in=ids)}
    recent_categories = [cats_by_id[pk] for pk in ids if pk in cats_by_id]

    return render(request, "accounting/entry_create_form.html", {
        "form": form,
        "title": "Nouvelle écriture",
        "save_and_new": True,
        "suggested_category": suggested_category,
        "entry_mode": entry_mode,
        "recent_categories": recent_categories,
    })

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
@require_permission(PermissionLevel.GESTION)
def entry_duplicate(request, pk):
    org = request.user.profile.organization
    source = get_object_or_404(Entry, pk=pk, fiscal_year__organization=org)
    open_fy = FiscalYear.objects.filter(organization=org, status="open").first()
    form = EntryForm(initial={
        "fiscal_year": open_fy.pk if open_fy else source.fiscal_year.pk,
        "category": source.category.pk,
        "amount": source.amount,
        "description": source.description,
        "date": datetime.date.today(),
    })
    form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(organization=org, status="open")
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/entry_create_form.html", {
        "form": form,
        "title": f"Dupliquer — {source.description}",
        "save_and_new": False,
    })


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

    actual_balance = total_actual_income - total_actual_expense
    budget_balance = total_budget_income - total_budget_expense

    return render(request, "accounting/budget_tracking.html", {
        "fiscal_year": fy,
        "income_rows": income_rows,
        "expense_rows": expense_rows,
        "total_budget_income": total_budget_income,
        "total_actual_income": total_actual_income,
        "total_budget_expense": total_budget_expense,
        "total_actual_expense": total_actual_expense,
        "total_diff_income": total_actual_income - total_budget_income,
        "total_diff_expense": total_actual_expense - total_budget_expense,
        "actual_balance": actual_balance,
        "budget_balance": budget_balance,
        "diff_balance": actual_balance - budget_balance,
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


@login_required
def document_list(request):
    """Browse all attachments organized by fiscal year and month."""
    org = request.user.profile.organization
    fiscal_years = FiscalYear.objects.filter(organization=org).order_by("-start_date")
    selected_fy_id = request.GET.get("fiscal_year")

    if selected_fy_id:
        selected_fy = get_object_or_404(FiscalYear, pk=selected_fy_id, organization=org)
    else:
        selected_fy = fiscal_years.filter(status="open").first() or fiscal_years.first()

    documents = []
    months = {}
    total_count = 0

    if selected_fy:
        entries_with_attachments = (
            Entry.objects.filter(fiscal_year=selected_fy)
            .exclude(attachment="")
            .select_related("category")
            .order_by("date")
        )
        for entry in entries_with_attachments:
            month_key = entry.date.strftime("%Y-%m")
            month_label = entry.date.strftime("%B %Y").capitalize()
            if month_key not in months:
                months[month_key] = {"label": month_label, "entries": [], "count": 0}
            filename = entry.attachment.name.split("/")[-1]
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            months[month_key]["entries"].append({
                "entry": entry,
                "filename": filename,
                "ext": ext,
                "size": _safe_file_size(entry.attachment),
            })
            months[month_key]["count"] += 1
            total_count += 1

        # Sort months chronologically
        documents = sorted(months.items())

    # Count total attachments across all fiscal years
    all_count = Entry.objects.filter(
        fiscal_year__organization=org
    ).exclude(attachment="").count()

    return render(request, "accounting/document_list.html", {
        "fiscal_years": fiscal_years,
        "selected_fy": selected_fy,
        "documents": documents,
        "total_count": total_count,
        "all_count": all_count,
    })


def _safe_file_size(field):
    """Return file size in human-readable format, or None if file missing."""
    try:
        size = field.size
        if size < 1024:
            return f"{size} o"
        elif size < 1024 * 1024:
            return f"{size / 1024:.0f} Ko"
        else:
            return f"{size / (1024 * 1024):.1f} Mo"
    except (FileNotFoundError, OSError):
        return None


@login_required
def attachment_download(request, pk):
    """Secure download of an entry's attachment."""
    entry = get_object_or_404(Entry, pk=pk, fiscal_year__organization=request.user.profile.organization)
    if not entry.attachment:
        raise Http404("Aucun justificatif pour cette écriture.")
    try:
        f = entry.attachment.open("rb")
    except FileNotFoundError:
        raise Http404("Fichier introuvable sur le serveur.")
    filename = entry.attachment.name.split("/")[-1]
    content_type, _ = mimetypes.guess_type(filename)
    return FileResponse(f, content_type=content_type or "application/octet-stream", filename=filename)


@login_required
@require_permission(PermissionLevel.GESTION)
def scan_ticket(request):
    """Scan a receipt/ticket image and create an entry from OCR data."""
    org = request.user.profile.organization
    open_fy = FiscalYear.objects.filter(organization=org, status="open").first()

    if not open_fy:
        messages.error(request, "Aucun exercice ouvert. Créez ou ouvrez un exercice avant de scanner un ticket.")
        return redirect("accounting:fiscal_year_list")

    if request.method == "POST":
        # Step 2: form submission — create entry
        if "amount" in request.POST:
            form = EntryForm(request.POST, request.FILES)
            form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(organization=org, status="open")
            form.fields["category"].queryset = org.categories.all()
            if form.is_valid():
                entry = form.save(commit=False)
                entry.created_by = request.user
                # Attach the scanned image if no new file was uploaded
                temp_path = request.POST.get("temp_image_path", "")
                if not entry.attachment and temp_path:
                    from django.core.files.storage import default_storage
                    if default_storage.exists(temp_path):
                        from django.core.files import File
                        filename = temp_path.split("/")[-1]
                        entry.attachment.save(filename, default_storage.open(temp_path), save=False)
                        default_storage.delete(temp_path)
                entry.full_clean()
                entry.save()
                messages.success(request, "Écriture créée à partir du ticket scanné.")
                if "scan_another" in request.POST:
                    return redirect("accounting:scan_ticket")
                return redirect("accounting:entry_list")
            return render(request, "accounting/scan_ticket.html", {
                "step": "verify",
                "form": form,
                "temp_image_path": request.POST.get("temp_image_path", ""),
            })

        # Step 1: image upload — run OCR
        image = request.FILES.get("ticket_image")
        if not image:
            messages.error(request, "Veuillez sélectionner une image.")
            return render(request, "accounting/scan_ticket.html", {"step": "upload"})

        # Validate image type
        if not image.content_type.startswith("image/"):
            messages.error(request, "Le fichier doit être une image (JPG, PNG, etc.).")
            return render(request, "accounting/scan_ticket.html", {"step": "upload"})

        try:
            data = extract_from_image(image)
        except RuntimeError as e:
            messages.error(request, str(e))
            return render(request, "accounting/scan_ticket.html", {"step": "upload"})

        # Store uploaded image in session temp path for later attachment
        image.seek(0)
        from django.core.files.storage import default_storage
        temp_path = default_storage.save(f"scan_temp/{image.name}", image)

        # Pre-fill the entry form with OCR data
        expense_cats = org.categories.filter(category_type=CategoryType.EXPENSE)
        initial = {
            "fiscal_year": open_fy.pk,
            "date": data["date"] or datetime.date.today(),
            "amount": data["amount"] or "",
            "description": data["description"] or "",
            "category": expense_cats.first().pk if expense_cats.exists() else None,
        }
        form = EntryForm(initial=initial)
        form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(organization=org, status="open")
        form.fields["category"].queryset = org.categories.all()

        ocr_warning = not data["amount"] or not data["date"]
        if not data["raw_text"] or len(data["raw_text"]) < 10:
            ocr_warning_message = (
                "Aucun texte n'a pu être extrait de l'image. "
                "Réessayez avec une photo plus nette, bien cadrée et bien éclairée."
            )
        else:
            ocr_warning_message = ""

        return render(request, "accounting/scan_ticket.html", {
            "step": "verify",
            "form": form,
            "raw_text": data["raw_text"],
            "ocr_warning": ocr_warning,
            "ocr_warning_message": ocr_warning_message,
            "temp_image_path": temp_path,
        })

    # GET: show upload form
    return render(request, "accounting/scan_ticket.html", {"step": "upload"})
