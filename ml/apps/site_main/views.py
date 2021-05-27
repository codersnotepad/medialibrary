from django.shortcuts import render
from ml.apps.add_media import models as am_models
from . import forms

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
    meida_file = am_models.Media_Fact.objects.get(pk=pk)
    show_update_msg = False

    if request.POST:
        f = forms.EditMediaForm(request.POST, instance=meida_file)
        if f.is_valid():
            meida_file = f.save()
            show_update_msg = True

    edit_meida_form = forms.EditMediaForm(instance=meida_file)
    context = {
        "m": meida_file,
        "edit_meida_form": edit_meida_form,
        "form_media": edit_meida_form.media,
        "form_action": "/edit_media/" + pk,
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
    print(project)
    project_instance = am_models.Project_Fact.objects.filter(name=project)[0]
    project_files = am_models.Media_Fact.objects.filter(project_fk=project_instance)
    context = {
        "project_files": project_files,
        "project_name": project,
        "file_count": project_files.count(),
    }
    return render(request, "project_view.html", context)
