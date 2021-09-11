from django.apps import AppConfig
from django.conf import settings
import pathlib


class SiteSettingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ml.apps.site_settings"
    def ready(self):
        pathlib.Path(settings.UPLOAD_PROJECTS_DIR).mkdir(parents=True, exist_ok=True)
        pathlib.Path(settings.UPLOAD_FILES_PROXIES_DIR).mkdir(parents=True, exist_ok=True)
        pathlib.Path(settings.UPLOAD_FILES_CDNG_DIR).mkdir(parents=True, exist_ok=True)
