from django.urls import path
from core import views

app_name = "core"
urlpatterns = [
    path("setup/", views.setup_wizard, name="setup_wizard"),
    path("settings/", views.organization_settings, name="organization_settings"),
]
