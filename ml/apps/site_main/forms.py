from django import forms
from ml.apps.add_media import models as am_models


class EditMediaForm(forms.ModelForm):
    class Meta:
        fields = ["name", "tags"]
        model = am_models.Media_Fact
