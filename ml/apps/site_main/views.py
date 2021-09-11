from django.shortcuts import render
from django.http import HttpResponseRedirect
from ml.apps.add_media import models as am_models
from . import forms
from django.conf import settings
import os, shutil

# Create your views here.
def index(request):
    most_recent = am_models.Media_Fact.objects.all().order_by("-id")[:10]
    context = {
        "most_recent": most_recent,
    }
    return render(request, "index.html", context)


def error_redirect(request):
    context = {
        "error_msg": "An error occured.",
        "redirect_url": "",
    }
    return render(request, "error_redirect.html", context)


def edit_meida(request, pk):
    media_file = am_models.Media_Fact.objects.get(pk=pk)
    show_update_msg = False

    if request.POST:
        f = forms.EditMediaForm(request.POST, instance=media_file)
        if f.is_valid():
            media_file = f.save()
            show_update_msg = True

    edit_meida_form = forms.EditMediaForm(instance=media_file)
    context = {
        "m": media_file,
        "edit_meida_form": edit_meida_form,
        "form_media": edit_meida_form.media,
        "form_action": "/edit_media/" + pk,
        "form_action_delete": "/confirm_file/" + pk,
        "show_update_msg": show_update_msg,
    }
    return render(request, "edit_meida.html", context)


def tag_view(request, tag):
    print(tag)
    tag_instance = am_models.Media_Tags.objects.filter(name=tag)[0]
    tag_files = am_models.Media_Fact.objects.filter(tags=tag_instance)
    context = {
        "tag_files": tag_files,
        "tag_name": tag,
        "file_count": tag_files.count(),
    }
    return render(request, "tag_view.html", context)


def project_view(request, project):
    project_instance = am_models.Project_Fact.objects.filter(name=project)[0]
    project_files = am_models.Media_Fact.objects.filter(project_fk=project_instance)
    context = {
        "project_files": project_files,
        "project_name": project,
        "file_count": project_files.count(),
        "form_action_delete": "/confirm_project/" + str(project_instance.id),
    }
    return render(request, "project_view.html", context)


def confirm_file(request, pk):
    media_file = am_models.Media_Fact.objects.get(pk=pk)

    context = {
        "m": media_file,
        "form_action": "/delete_file/" + pk,
    }
    return render(request, "confirm_file.html", context)


def confirm_project(request, pk):
    project = am_models.Project_Fact.objects.filter(pk=pk)[0]
    media_file = am_models.Media_Fact.objects.filter(project_fk=project.id)

    context = {
        "p": project,
        "m": media_file,
        "form_action": "/delete_project/" + pk,
    }
    return render(request, "confirm_project.html", context)


def delete_file(request, pk):
    meida_file = am_models.Media_Fact.objects.get(pk=pk)
    # delete from database
    meida_file.delete()
    # delete file
    file_name_path = os.path.join(settings.BASE_DIR, meida_file.file_location_fk.path, meida_file.file_name)
    os.remove(file_name_path)
    # delete proxy file
    proxy_file_name_path = os.path.join(settings.BASE_DIR, meida_file.proxy_file_location_fk.path, meida_file.proxy_file_name)
    if file_name_path != proxy_file_name_path:
        os.remove(proxy_file_name_path)

    return HttpResponseRedirect("/")


def delete_project(request, pk):
    project = am_models.Project_Fact.objects.filter(pk=pk)[0]
    media_file = am_models.Media_Fact.objects.filter(project_fk=project.id)
    project_path = os.path.join(settings.BASE_DIR, project.project_location_fk.path)

    location_pks = list()
    for m in media_file:
        location_pks.append(m.file_location_fk.id)
        location_pks.append(m.proxy_file_location_fk.id)

    location_pks = list(dict.fromkeys(location_pks))

    for location_pk in location_pks:
        try:
            location = am_models.Location_Fact.objects.filter(pk=location_pk)[0]
        except am_models.Location_Fact.DoesNotExist:
            location = None
        if location:
            location.delete()

    # delete file
    shutil.rmtree(project_path)
    # delete from database
    project.delete()

    return HttpResponseRedirect("/")
