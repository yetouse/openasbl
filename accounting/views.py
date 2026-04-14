from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import require_permission
from accounts.models import PermissionLevel
from accounting.forms import AssetSnapshotForm, BudgetForm, CategoryForm, EntryForm, FiscalYearForm
from accounting.models import AssetSnapshot, Budget, Category, CategoryType, Entry, FiscalYear, FiscalYearStatus

@login_required
def dashboard(request):
    org = request.user.profile.organization
    fiscal_years = FiscalYear.objects.filter(organization=org)
    current_fy = fiscal_years.filter(status="open").first()
    summary = {}
    if current_fy:
        income = Entry.objects.filter(fiscal_year=current_fy, category__category_type=CategoryType.INCOME).aggregate(total=Sum("amount"))["total"] or 0
        expenses = Entry.objects.filter(fiscal_year=current_fy, category__category_type=CategoryType.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
        summary = {"income": income, "expenses": expenses, "balance": income - expenses, "entry_count": Entry.objects.filter(fiscal_year=current_fy).count()}
    return render(request, "accounting/dashboard.html", {"fiscal_years": fiscal_years, "current_fy": current_fy, "summary": summary})

@login_required
def entry_list(request):
    org = request.user.profile.organization
    fiscal_year_id = request.GET.get("fiscal_year")
    entries = Entry.objects.select_related("category", "created_by")
    if fiscal_year_id:
        entries = entries.filter(fiscal_year_id=fiscal_year_id)
    else:
        entries = entries.filter(fiscal_year__organization=org)
    fiscal_years = FiscalYear.objects.filter(organization=org)
    return render(request, "accounting/entry_list.html", {"entries": entries, "fiscal_years": fiscal_years, "selected_fy": fiscal_year_id})

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
            messages.success(request, "Ecriture enregistree.")
            return redirect("accounting:entry_list")
    else:
        form = EntryForm()
    form.fields["fiscal_year"].queryset = FiscalYear.objects.filter(organization=org, status="open")
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/entry_form.html", {"form": form, "title": "Nouvelle ecriture"})

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
    return render(request, "accounting/fiscal_year_list.html", {"fiscal_years": fiscal_years})

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
def budget_create(request, fiscal_year_pk):
    fy = get_object_or_404(FiscalYear, pk=fiscal_year_pk)
    org = request.user.profile.organization
    if request.method == "POST":
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.fiscal_year = fy
            budget.save()
            messages.success(request, "Budget enregistré.")
            return redirect("accounting:fiscal_year_list")
    else:
        form = BudgetForm()
    form.fields["category"].queryset = org.categories.all()
    return render(request, "accounting/budget_form.html", {"form": form, "fiscal_year": fy})

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
