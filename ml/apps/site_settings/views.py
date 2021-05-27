from django.shortcuts import render
from . import models, forms

# Create your views here.
def site_settings(request):

    if models.Settings.objects.count() > 0:
        settings_data = models.Settings.objects.all().order_by("id")[0]
    else:
        settings_data = None

    if request.POST:
        settings_form = forms.SettingsForm(request.POST, instance=settings_data)
        if settings_form.is_valid():
            settings_data = settings_form.save()
            show_update_msg = True
    else:
        show_update_msg = False

    settings_form = forms.SettingsForm(instance=settings_data)
    context = {
        "settings_form": settings_form,
        "form_media": settings_form.media,
        "show_update_msg": show_update_msg,
    }
    return render(request, "settings.html", context)
