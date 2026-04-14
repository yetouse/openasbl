from django.contrib import admin
from accounting.models import AssetSnapshot, Budget, Category, Entry, FiscalYear


@admin.register(FiscalYear)
class FiscalYearAdmin(admin.ModelAdmin):
    list_display = ("__str__", "status", "organization")
    list_filter = ("status",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category_type", "organization")
    list_filter = ("category_type",)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("date", "description", "amount", "category", "created_by")
    list_filter = ("category__category_type", "fiscal_year")
    date_hierarchy = "date"


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("category", "planned_amount", "fiscal_year")


@admin.register(AssetSnapshot)
class AssetSnapshotAdmin(admin.ModelAdmin):
    list_display = ("date", "cash", "bank", "receivables", "debts", "net_worth")
