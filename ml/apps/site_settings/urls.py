from django.urls import path
from . import views

app_name = "ss"
urlpatterns = [
    path("", views.site_settings, name="settings"),
]
