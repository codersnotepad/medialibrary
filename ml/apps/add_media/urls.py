from django.urls import path
from . import views

app_name = "am"
urlpatterns = [
    path("/files", views.add_files, name="add_files"),
    path("/project", views.add_project, name="add_project"),
]
