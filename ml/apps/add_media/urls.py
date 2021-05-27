from django.urls import path
from . import views

app_name = "am"
urlpatterns = [
    path("", views.add_media, name="add_media"),
]
