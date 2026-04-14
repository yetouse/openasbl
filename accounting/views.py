from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import require_permission
from accounts.models import PermissionLevel
from accounting.forms import EntryForm
from accounting.models import CategoryType, Entry, FiscalYear

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
