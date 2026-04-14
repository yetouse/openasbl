from django.urls import path
from accounting import views

app_name = "accounting"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("entries/", views.entry_list, name="entry_list"),
    path("entries/create/", views.entry_create, name="entry_create"),
    path("entries/<int:pk>/edit/", views.entry_edit, name="entry_edit"),
    path("entries/<int:pk>/delete/", views.entry_delete, name="entry_delete"),
]
