from django.urls import path
from accounting import views

app_name = "accounting"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("entries/", views.entry_list, name="entry_list"),
    path("entries/create/", views.entry_create, name="entry_create"),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
    path("fiscal-years/", views.fiscal_year_list, name="fiscal_year_list"),
    path("fiscal-years/create/", views.fiscal_year_create, name="fiscal_year_create"),
    path("fiscal-years/<int:pk>/close/", views.fiscal_year_close, name="fiscal_year_close"),
    path("fiscal-years/<int:fiscal_year_pk>/budget/create/", views.budget_create, name="budget_create"),
    path("fiscal-years/<int:fiscal_year_pk>/asset-snapshot/create/", views.asset_snapshot_create, name="asset_snapshot_create"),
    path("fiscal-years/<int:pk>/budget-tracking/", views.budget_tracking, name="budget_tracking"),
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("documents/", views.document_list, name="document_list"),
    path("entries/<int:pk>/attachment/", views.attachment_download, name="attachment_download"),
    path("scan/", views.scan_ticket, name="scan_ticket"),
]
