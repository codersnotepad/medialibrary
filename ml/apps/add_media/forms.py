from django import forms
from django.conf import settings
from django.core.cache import cache
from . import models


class AddFilesForm(forms.ModelForm):
    class Meta:
        fields = ["tags"]
        model = models.Media_Fact


class AddProjectForm(forms.ModelForm):
    class Meta:
        fields = ["project", "tags"]
        model = models.Media_Fact

    _filepath_kw = dict(
        path=settings.UPLOAD_PROJECTS_DIR, allow_files=False, allow_folders=True
    )

    project = forms.FilePathField(**_filepath_kw)

    def __init__(self, **kwargs):
        key = "filepath-cache-key"
        choices = cache.get(key)
        if not choices:
            field = forms.FilePathField(**self._filepath_kw)
            choices = field.choices
            cache.set(key, choices, 5)
        super().__init__(**kwargs)
        self.base_fields["project"].choices = choices
        # print(self.base_fields['project'].choices)
