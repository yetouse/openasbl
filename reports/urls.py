from django.urls import path

from . import views

app_name = "reports"
urlpatterns = [
    path("", views.report_select, name="report_select"),
    path("journal/pdf/", views.journal_pdf, name="journal_pdf"),
    path("journal/excel/", views.journal_excel, name="journal_excel"),
    path("journal/csv/", views.journal_csv, name="journal_csv"),
    path("patrimony/pdf/", views.patrimony_pdf, name="patrimony_pdf"),
    path("monthly-ca/pdf/", views.monthly_ca_pdf, name="monthly_ca_pdf"),
]
