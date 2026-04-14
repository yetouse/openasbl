from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from accounting.models import FiscalYear

from .generators.excel import generate_journal_csv, generate_journal_excel
from .generators.pdf import (
    generate_journal_pdf,
    generate_monthly_ca_pdf,
    generate_patrimony_pdf,
)


@login_required
def report_select(request):
    fiscal_years = FiscalYear.objects.all()
    return render(request, "reports/report_select.html", {"fiscal_years": fiscal_years})


@login_required
def journal_pdf(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    pdf_bytes = generate_journal_pdf(fy)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="journal_{fy.pk}.pdf"'
    return response


@login_required
def journal_excel(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    excel_bytes = generate_journal_excel(fy)
    response = HttpResponse(
        excel_bytes,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="journal_{fy.pk}.xlsx"'
    return response


@login_required
def journal_csv(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    csv_string = generate_journal_csv(fy)
    response = HttpResponse(csv_string, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="journal_{fy.pk}.csv"'
    return response


@login_required
def patrimony_pdf(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    pdf_bytes = generate_patrimony_pdf(fy)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="patrimoine_{fy.pk}.pdf"'
    return response


@login_required
def monthly_ca_pdf(request):
    fy = get_object_or_404(FiscalYear, pk=request.GET.get("fiscal_year"))
    year = int(request.GET.get("year"))
    month = int(request.GET.get("month"))
    pdf_bytes = generate_monthly_ca_pdf(fy, year, month)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="rapport_ca_{year}_{month:02d}.pdf"'
    )
    return response
