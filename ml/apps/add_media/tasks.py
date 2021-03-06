# library imports
import logging
import os
import shutil
import re
from django.conf import settings
from django.shortcuts import render


def add_project(request, ht):
    logging.info("")
    logging.info("")
    logging.info("")
    logging.info(
        "----------------------------------------------------------------------------------------"
    )
    logging.info("Run function add_project()")
    logging.info(
        "----------------------------------------------------------------------------------------"
    )
    logging.info("")
    """
    inputs:
        ht = HelperTools() instance
    """

    # inst setup from helper tools
    s = ht.Setup()

    # define varaibles
    s.post("taks_name", "add_project")
    s.post("tags", request.POST.get("tags"))
    s.post(
        "project_name",
        re.sub(
            "[^A-Za-z]+",
            "",
            os.path.basename(os.path.normpath(request.POST.get("project"))).title(),
        ),
    )
    s.post("project_dir", request.POST.get("project"))

    # define output root directory
    out_root_dir = os.path.join(
        settings.CONTENT_DIR,
        s.get("yyyy"),
        s.get("mm"),
        s.get("project_name"),
    )
    s.post("out_root_dir", out_root_dir)

    # get project project_type
    s.post("project_type", ht.get_project_type(s.get("project_dir"), s))

    # create uploads
    if s.get("project_type").startswith("video-"):
        uploads = ht.create_uploads_video_project(s.get("project_dir"), s)
        try:
            test_run = ht.upload(uploads, s, test_run=True)
            continue_run = True
            logging.info("test_run completed.")
        except:
            continue_run = False
            context = {
                "error_msg": "Error processng files. Please see command output.",
            }
            return render(request, "error_redirect.html", context)

    if continue_run:
        # upload files to database
        results = ht.upload(uploads, s)

        # update premissions on source files then move to content
        ht.change_permissions_recursive(s.get("project_dir"), 0o777)
        shutil.move(s.get("project_dir"), s.get("out_root_dir"))


def add_files(request, ht):
    logging.info("")
    logging.info("")
    logging.info("")
    logging.info(
        "----------------------------------------------------------------------------------------"
    )
    logging.info("Run function add_files()")
    logging.info(
        "----------------------------------------------------------------------------------------"
    )
    logging.info("")
    """
    inputs:
        ht = HelperTools() instance
    """

    # inst setup from helper tools
    s = ht.Setup()

    # define output root directory
    out_root_dir = os.path.join(
        settings.CONTENT_DIR,
        s.get("yyyy"),
        s.get("mm"),
        "Files" + s.get("datetime_suffix"),
    )
    s.post("out_root_dir", out_root_dir)

    # define varaibles
    s.post("taks_name", "add_files")
    s.post("tags", request.POST.get("tags"))
    s.post("project_name", None)
    s.post("project_type", None)
    s.post("project_dir", settings.UPLOAD_FILES_DIR)

    # get files list from settings.UPLOAD_FILES_DIR
    files_contents = ht.list_directory_contents(settings.UPLOAD_FILES_DIR, s)
    proxies_contents = ht.list_directory_contents(settings.UPLOAD_FILES_PROXIES_DIR, s)
    cdng_contents = ht.list_directory_contents(settings.UPLOAD_FILES_CDNG_DIR, s)

    # for each file match to proxies or cdng creating uploads list
    uploads = ht.create_uploads_files(
        files_contents, proxies_contents, cdng_contents, s
    )
    try:
        test_run = ht.upload(uploads, s, test_run=True)
        continue_run = True
        logging.info("test_run completed.")
    except:
        context = {
            "error_msg": "Error processng files. Please see command output.",
        }
        return render(request, "error_redirect.html", context)
        continue_run = False

    logging.info("continue_run")

    if continue_run:
        # upload files to database
        results = ht.upload(uploads, s, test_run=False)

        # update premissions on source files then move to content
        ht.change_permissions_recursive(settings.UPLOAD_FILES_DIR, 0o777)
        shutil.move(settings.UPLOAD_FILES_DIR, s.get("out_root_dir"))

        # create files dirs
        os.makedirs(settings.UPLOAD_FILES_PROXIES_DIR, exist_ok=True)
        os.makedirs(settings.UPLOAD_FILES_CDNG_DIR, exist_ok=True)
