from django import forms
from . import models


class SettingsForm(forms.ModelForm):
    class Meta:
        fields = [
            "audio_ext",
            "video_comp_ext",
            "video_raw_ext",
            "image_comp_ext",
            "image_raw_ext",
            "other_ext",
            "ignore_files",
            "ignore_folders",
            "ignore_file_prefix",
        ]
        model = models.Settings
