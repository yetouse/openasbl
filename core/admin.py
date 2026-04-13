from django.contrib import admin
from core.models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "enterprise_number", "email")
