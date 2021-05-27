from django.shortcuts import render
from . import forms, tasks, helpertools
from ml.apps.site_settings import models
from ml.apps.site_settings import forms as ss_forms
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
import logging


# Create your views here.
def add_media(request):
    logging.info("Run function add_media()")

    # inst helper tools
    ht = helpertools.HelperTools()

    # get settings_data
    settings_data = models.Settings.objects.all().order_by("id")

    # did we submit from a form
    if request.POST:

        # do we have required settings and project form was submitted
        if len(settings_data) > 0 and request.POST.get("form_id") == "project":
            # run add_project and capture result
            result = tasks.add_project(request, ht)

        # do we have required settings and files form was submitted
        elif len(settings_data) > 0 and request.POST.get("form_id") == "files":
            # run add_files and capture result
            result = tasks.add_files(request, ht)

        # if we do no have settings show error
        else:
            context = {
                "error_msg": "Please update settings before adding media.",
                "redirect_url": "settings",
            }
            return render(request, "error_redirect.html", context)

    add_project_form = forms.AddProjectForm()
    add_media_form = forms.AddMediaForm()
    context = {
        "add_project_form": add_project_form,
        "add_media_form": add_media_form,
        "form_media": add_project_form.media,
    }
    return render(request, "add_media.html", context)
