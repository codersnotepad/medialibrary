from django.urls import path
from . import views

app_name = "sm"
urlpatterns = [
    path("", views.index, name="index"),
    path("error_redirect", views.error_redirect, name="error_redirect"),
    path("edit_media/<pk>", views.edit_meida, name="edit_meida"),
    path("tag_view/<tag>", views.tag_view, name="tag_view"),
    path("project_view/<project>", views.project_view, name="project_view"),
]
