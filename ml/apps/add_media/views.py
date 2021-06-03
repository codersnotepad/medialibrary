from django.shortcuts import render
from . import forms, tasks, helpertools
from ml.apps.site_settings import models
from ml.apps.site_settings import forms as ss_forms
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
import logging


def add_files(request):
    logging.info("Run function add_files()")

    # inst helper tools
    ht = helpertools.HelperTools()

    # get settings_data
    settings_data = models.Settings.objects.all().order_by("id")

    # did we submit from a form
    if request.POST:

        # do we have required settings and files form was submitted
        if len(settings_data) > 0 and request.POST.get("form_id") == "files":
            # run add_files and capture result
            result = tasks.add_files(request, ht)

        # if we do no have settings show error
        else:
            context = {
                "error_msg": "Please update settings before adding media.",
                "redirect_url": "settings",
            }
            return render(request, "error_redirect.html", context)

    add_files_form = forms.AddFilesForm()
    context = {
        "add_files_form": add_files_form,
        "form_media": add_files_form.media,
    }
    return render(request, "add_files.html", context)


# Create your views here.
def add_project(request):
    logging.info("Run function add_project()")

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
    context = {
        "add_project_form": add_project_form,
        "form_media": add_project_form.media,
    }
    return render(request, "add_project.html", context)
