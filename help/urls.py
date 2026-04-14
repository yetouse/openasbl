from django.urls import path
from help import views

app_name = "help"
urlpatterns = [
    path("panel/", views.help_panel, name="help_panel"),
]
