# library imports
import os
import logging
import datetime
import pathlib
import cv2
import rawpy
import shutil
import ntpath
import pathlib
from canon_cr3 import Image as Image_cr3
from PIL import Image as Image_pil
import io
from ml.apps.site_settings import models as ss_models
from ml.apps.add_media import models as am_models
from django.conf import settings
import tagulous
import audio_metadata

settings_data = ss_models.Settings.objects.all().order_by("id")


class HelperTools:
    def __init__(self):
        self.setup = self.Setup
        logging.info("HelperTools instance defined.")

    class Setup:
        def __init__(self):
            self.get = self.get
            self.data = {
                "yyyy": datetime.datetime.today().strftime("%Y"),
                "mm": datetime.datetime.today().strftime("%m"),
                "dd": datetime.datetime.today().strftime("%d"),
                "datetime_suffix": "_"
                + datetime.datetime.today().strftime("%Y%m%d%H%M%S"),
                "video_comp_ext": settings_data[0].video_comp_ext.get_tag_list(),
                "video_raw_ext": settings_data[0].video_raw_ext.get_tag_list(),
                "audio_ext": settings_data[0].audio_ext.get_tag_list(),
                "image_comp_ext": settings_data[0].image_comp_ext.get_tag_list(),
                "image_raw_ext": settings_data[0].image_raw_ext.get_tag_list(),
                "other_ext": settings_data[0].other_ext.get_tag_list(),
                "all_ext_list": settings_data[0].video_comp_ext.get_tag_list()
                + settings_data[0].video_raw_ext.get_tag_list()
                + settings_data[0].audio_ext.get_tag_list()
                + settings_data[0].image_comp_ext.get_tag_list()
                + settings_data[0].image_raw_ext.get_tag_list()
                + settings_data[0].other_ext.get_tag_list(),
                "ignore_files": settings_data[0].ignore_files.get_tag_list(),
                "ignore_folders": settings_data[0].ignore_folders.get_tag_list(),
            }
            logging.info("HelperTools.Setup instance defined.")

        def get(self, var):
            return self.data[var]

        def post(self, name, var):
            self.data[name] = var

    # ----------------------------------------------------------------------------------------
    # functions to get required info pre upload
    # ----------------------------------------------------------------------------------------
    def list_directory_contents(self, path, s):
        logging.info("HelperTools.list_directory_contents running with vars:")
        logging.info("   path:" + path + "\n")
        """
        inputs:
            path - string of path to search in NOT resursive
        outputs:
            {
                path: <str>(/path/to/dir),
                files: [
                    {
                        filename: <str>(test_file.TXT),
                        name: <str>(test_file),
                        extension: <str>(.TXT),
                        extension_filtered: <str>(txt),
                    },
                    ...
                ],
                directories: [
                    <str>(text_files),
                    ...
                ]
            }
        """

        for (dirpath, dirnames, filenames) in os.walk(path):
            break

        # ignore the "ignore_files" files
        for ignore_file in s.get("ignore_files"):
            if ignore_file in filenames:
                filenames.remove(ignore_file)

        # ignore all files in folder if Path ends in an ignore_folders
        for ignore_folder in s.get("ignore_folders"):
            if dirpath.find(ignore_folder) >= 0:
                filenames = list()
                break

        files = list()

        for filename in filenames:
            # double check it is a file
            if os.path.isfile(os.path.join(dirpath, filename)):
                name, extension = os.path.splitext(filename)

                files.append(
                    {
                        "filename": filename,
                        "name": name,
                        "extension": extension,
                        "extension_filtered": extension.lower()[1:],
                    }
                )

        dirs = list()

        for dirname in dirnames:
            # double check it is a folder
            if os.path.isdir(os.path.join(dirpath, dirname)):
                dirs.append(dirname)

        # CDNG files
        if (
            os.path.basename(dirpath) == settings.UPLOAD_PROJECT_FULLRES_NAME
            and len(dirs) > 0
            and len(files) == 0
        ):
            # we assume the folders are cdng movies
            for dirname in dirnames:
                files.append(
                    {
                        "filename": dirname,
                        "name": dirname,
                        "extension": ".DNG",
                        "extension_filtered": "cdng",
                    }
                )

        data = {
            "path": dirpath,
            "files": files,
            "directories": dirs,
        }

        return data

    def get_project_type(self, path, s):
        logging.info("HelperTools.get_project_type running with vars:")
        logging.info("   path:" + path + "\n")
        """
        inputs:
            path - <str>(/path/to/folder) NOT resursive
        outputs:
            <str>(video-dls, audio-als)
        """

        # get dir contents
        data = self.list_directory_contents(path, s)

        # define vars
        proxies_dir = False
        fullres_dir = False
        drp_file = False
        als_file = False

        # collect info on dir contents
        for file in data["files"]:
            if file["extension_filtered"] == "drp":
                drp_file = True
            elif file["extension_filtered"] == "als":
                als_file = True

        for folder in data["directories"]:
            if folder == "FullRes":
                fullres_dir = True
            elif folder == "Proxies":
                proxies_dir = True

        print("proxies_dir", proxies_dir)
        print("fullres_dir", fullres_dir)
        print("drp_file", drp_file)
        print("als_file", als_file)

        # decide what project type we have
        if proxies_dir and fullres_dir and drp_file:
            return "video-drp"
        elif not proxies_dir and not fullres_dir and als_file:
            return "audio-als"

    # ----------------------------------------------------------------------------------------
    # functions upload data into db
    # ----------------------------------------------------------------------------------------
    def create_uploads_files(self, files_contents, proxies_contents, cdng_contents, s):
        logging.info("HelperTools.create_uploads running.")
        """
        inputs:
            files_contents - files and dirs in settings.UPLOAD_FILES_DIR
            proxies_contents - files and dirs in settings.UPLOAD_FILES_DIR
            cdng_contents - files and dirs in settings.UPLOAD_FILES_DIR
            s - HelperTools.Setup()
        outputs:
            {
                "name": <str>(test_file),
                "file_name": <str>(test_file.TXT),
                "file_location": <str>(/path/to/file),
                "file_location_out" <str>(/path/to/file),
                "extension": <str>(TXT),
                "extension_filtered": <str>(txt),
                "proxy_file_name": <str>(test_file_prx.TXT),
                "proxy_file_location": <str>(/path/to/file),
                "proxy_file_location_out" <str>(/path/to/file),
            }
        """

        data = list()

        # look through files_contents for proxies
        for f in files_contents["files"]:
            for p in proxies_contents["files"]:
                if f["name"] == p["name"]:
                    data.append(
                        {
                            "name": f["name"],
                            "file_name": f["filename"],
                            "file_location": files_contents["path"],
                            "file_location_out": s.get("out_root_dir"),
                            "extension": f["extension"],
                            "extension_filtered": f["extension_filtered"],
                            "proxy_file_name": p["filename"],
                            "proxy_file_location": proxies_contents["path"],
                            "proxy_file_location_out": os.path.join(
                                s.get("out_root_dir"), settings.UPLOAD_PROXIES_NAME
                            ),
                        }
                    )

        # look through cdng_contents for proxies
        for c in cdng_contents["directories"]:
            for p in proxies_contents["files"]:
                if p["name"].startswith(c):
                    data.append(
                        {
                            "name": c,
                            "file_name": c,
                            "file_location": cdng_contents["path"],
                            "file_location_out": os.path.join(
                                s.get("out_root_dir"), settings.UPLOAD_CDNG_NAME
                            ),
                            "extension": ".DNG",
                            "extension_filtered": "cdng",
                            "proxy_file_name": p["filename"],
                            "proxy_file_location": proxies_contents["path"],
                            "proxy_file_location_out": os.path.join(
                                s.get("out_root_dir"), settings.UPLOAD_PROXIES_NAME
                            ),
                        }
                    )

        # look through files_contents files without proxies
        for f in files_contents["files"]:
            found = False
            for fs in data:
                if f["filename"] == fs["file_name"]:
                    found = True
                    break
            if not found and f["filename"][0] != ".":
                if f["extension_filtered"] in s.get("video_comp_ext"):
                    data.append(
                        {
                            "name": f["name"],
                            "file_name": f["filename"],
                            "file_location": files_contents["path"],
                            "file_location_out": s.get("out_root_dir"),
                            "extension": f["extension"],
                            "extension_filtered": f["extension_filtered"],
                            "proxy_file_name": f["filename"],
                            "proxy_file_location": files_contents["path"],
                            "proxy_file_location_out": s.get("out_root_dir"),
                        }
                    )
                else:
                    data.append(
                        {
                            "name": f["name"],
                            "file_name": f["filename"],
                            "file_location": files_contents["path"],
                            "file_location_out": s.get("out_root_dir"),
                            "extension": f["extension"],
                            "extension_filtered": f["extension_filtered"],
                            "proxy_file_name": None,
                            "proxy_file_location": None,
                            "proxy_file_location_out": None,
                        }
                    )

        return data

    def create_uploads_video_project(self, path, s):

        # get fullres and proxy files
        proxies_contents = self.list_directory_contents(
            os.path.join(path, settings.UPLOAD_PROXIES_NAME), s
        )
        fullress_contents = self.list_directory_contents(
            os.path.join(path, settings.UPLOAD_PROJECT_FULLRES_NAME), s
        )

        # match proxy to fullres
        data = list()

        for f in fullress_contents["files"]:
            for p in proxies_contents["files"]:
                if f["name"] == p["name"] or p["name"].startswith(f["name"]):
                    data.append(
                        {
                            "name": f["name"],
                            "file_name": f["filename"],
                            "file_location": fullress_contents["path"],
                            "file_location_out": os.path.join(
                                s.get("out_root_dir"),
                                os.path.relpath(
                                    fullress_contents["path"], s.get("project_dir")
                                ),
                            ),
                            "extension": f["extension"],
                            "extension_filtered": f["extension_filtered"],
                            "proxy_file_name": p["filename"],
                            "proxy_file_location": proxies_contents["path"],
                            "proxy_file_location_out": os.path.join(
                                s.get("out_root_dir"),
                                os.path.relpath(
                                    proxies_contents["path"], s.get("project_dir")
                                ),
                            ),
                        }
                    )

        # list all files in project folder
        all_files = list()
        for l in os.walk(path):
            if (
                os.path.basename(l[0]) == settings.UPLOAD_PROJECT_FULLRES_NAME
                or os.path.basename(l[0]) in s.get("ignore_folders")
                or l[0].find(settings.UPLOAD_PROJECT_FULLRES_NAME) > 0
            ):
                pass
            else:
                for filename in l[2]:
                    add_file = True
                    for d in data:
                        if filename == d["file_name"]:
                            add_file = False
                    for d in data:
                        if filename == d["proxy_file_name"]:
                            add_file = False
                    for ignore_file in s.get("ignore_files"):
                        if filename == ignore_file:
                            add_file = False
                    if add_file:

                        # define vars
                        name, extension = os.path.splitext(filename)

                        # add to data list
                        data.append(
                            {
                                "name": name,
                                "file_name": filename,
                                "file_location": l[0],
                                "file_location_out": os.path.join(
                                    s.get("out_root_dir"),
                                    os.path.relpath(
                                        fullress_contents["path"], s.get("project_dir")
                                    ),
                                ),
                                "extension": extension,
                                "extension_filtered": extension.lower()[1:],
                                "proxy_file_name": filename,
                                "proxy_file_location": l[0],
                                "proxy_file_location_out": os.path.join(
                                    s.get("out_root_dir"),
                                    os.path.relpath(l[0], s.get("project_dir")),
                                ),
                            }
                        )
        return data

    def upload(self, uploads, s, test_run=False):
        logging.info("HelperTools.upload running.")
        """
        inputs:
            [{
                "name": <str>(test_file),
                "file_name": <str>(test_file.TXT),
                "file_location": <str>(/path/to/file),
                "extension": <str>(TXT),
                "extension_filtered": <str>(txt),
                "proxy_file_name": <str>(test_file_prx.TXT),
                "proxy_file_location": <str>(/path/to/file),
            }]
            s - HelperTools.Setup()
        outputs:
        """

        if test_run == True:
            print(
                "----------------------------------------------------------------------------------------"
            )
            print("start test_run")
            print(
                "----------------------------------------------------------------------------------------"
            )

        for u in uploads:
            # upload video files
            print("##################")
            print(u["file_name"])
            print("##################")
            print()
            print(u)
            print()
            print()
            print()
            if u["extension_filtered"] in s.get("video_comp_ext"):
                self.upload_video_comp_file(u, s, test_run)
            elif u["extension_filtered"] == "cdng":
                self.upload_video_cdng_file(u, s, test_run)
            elif u["extension_filtered"] in s.get("image_raw_ext"):
                self.upload_image_raw_file(u, s, test_run)
            elif u["extension_filtered"] in s.get("image_comp_ext"):
                self.upload_image_comp_file(u, s, test_run)
            elif u["extension_filtered"] in s.get("audio_ext"):
                self.upload_audio_file(u, s, test_run)
            elif u["extension_filtered"] in s.get("other_ext"):
                self.upload_other_file(u, s, test_run)
        return True

    def upload_video_comp_file(self, data, s, test_run):
        logging.info("HelperTools.upload_video_comp_file running.")
        """
        inputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                file_location_out:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: <str>(test_file_prx.TXT),
                proxy_file_location: <str>(/path/to/file),
                proxy_file_location_out: <str>(/path/to/file),
             }
        outputs:
        """

        # get metadata for file
        metadata = self.get_video_metadata(
            os.path.join(data["file_location"], data["file_name"])
        )

        # check variables exist in db and extract instances
        mt = self.check_media_type_exists("video")
        # check file location out exists, create if not, make path relative when saving
        flo = self.check_location_exists(
            os.path.relpath(data["file_location_out"], settings.BASE_DIR)
        )
        # check proxy file location out exists, create if not, make path relative when saving
        pflo = self.check_location_exists(
            os.path.relpath(data["proxy_file_location_out"], settings.BASE_DIR)
        )
        if s.get("taks_name") == "add_project":
            # check project type exists, create if not
            pt = self.check_project_type_exists(s.get("project_type"))
            # check project exists, create if not
            p = self.check_project_exists(
                s.get("project_name"), s.get("out_root_dir"), pt
            )
        else:
            pt = None
            p = None

        if test_run == False:
            # write to db
            mf = am_models.Media_Fact(
                name=data["name"],
                extension_filtered=data["extension_filtered"],
                file_name=data["file_name"],
                file_extension=data["extension"],
                proxy_file_name=data["proxy_file_name"],
                height=metadata["height"],
                width=metadata["width"],
                fps=metadata["fps"],
                frame_count=metadata["fps"],
                duration_sec=metadata["duration"],
                file_location_fk=flo,
                file_type_fk=mt,
                proxy_file_location_fk=pflo,
                project_fk=p,
                tags=tagulous.utils.parse_tags(s.get("tags")),
                datetime_created=metadata["date_created"],
            )
            mf.save()

    def upload_video_cdng_file(self, data, s, test_run):
        logging.info("HelperTools.upload_video_cdng_file running.")
        """
        inputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                file_location_out:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: <str>(test_file_prx.TXT),
                proxy_file_location: <str>(/path/to/file),
                proxy_file_location_out: <str>(/path/to/file),
             }
        outputs:
        """

        # get metadata for file
        metadata = self.get_cdng_metadata(data)

        # check variables exist in db and extract instances
        mt = self.check_media_type_exists("video")
        # check file location out exists, create if not, make path relative when saving
        flo = self.check_location_exists(
            os.path.relpath(data["file_location_out"], settings.BASE_DIR)
        )
        # check proxy file location out exists, create if not, make path relative when saving
        pflo = self.check_location_exists(
            os.path.relpath(data["proxy_file_location_out"], settings.BASE_DIR)
        )
        if s.get("taks_name") == "add_project":
            # check project type exists, create if not
            pt = self.check_project_type_exists(s.get("project_type"))
            # check project exists, create if not
            p = self.check_project_exists(
                s.get("project_name"), s.get("out_root_dir"), pt
            )
        else:
            pt = None
            p = None

        if test_run == False:
            # compress folder and tidy up
            path = os.path.join(data["file_location"], data["file_name"])
            zip_file = shutil.make_archive(path, "zip", path)
            shutil.rmtree(path)

            # write to db
            mf = am_models.Media_Fact(
                name=data["name"],
                extension_filtered=data["extension_filtered"],
                file_name=ntpath.basename(zip_file),
                file_extension=data["extension"],
                proxy_file_name=data["proxy_file_name"],
                height=metadata["height"],
                width=metadata["width"],
                fps=metadata["fps"],
                frame_count=metadata["fps"],
                duration_sec=metadata["duration"],
                file_location_fk=flo,
                file_type_fk=mt,
                proxy_file_location_fk=pflo,
                project_fk=p,
                tags=tagulous.utils.parse_tags(s.get("tags")),
                datetime_created=metadata["date_created"],
            )
            mf.save()

    def upload_image_raw_file(self, data, s, test_run):
        logging.info("HelperTools.upload_image_raw_file running.")
        """
        inputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                file_location_out:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: None,
                proxy_file_location: None,
                proxy_file_location_out: None,
             }
             s - HelperTools.Setup
        outputs:
        """

        # get metadata for file
        metadata = self.get_image_raw_metadata(
            os.path.join(data["file_location"], data["file_name"]),
            data["extension_filtered"],
        )

        # create proxy image
        data = self.create_proxy_image(data, s)

        # check variables exist in db and extract instances
        mt = self.check_media_type_exists("image raw")
        # check file location out exists, create if not, make path relative when saving
        flo = self.check_location_exists(
            os.path.relpath(data["file_location_out"], settings.BASE_DIR)
        )
        # check proxy file location out exists, create if not, make path relative when saving
        pflo = self.check_location_exists(
            os.path.relpath(data["proxy_file_location_out"], settings.BASE_DIR)
        )
        if s.get("taks_name") == "add_project":
            # check project type exists, create if not
            pt = self.check_project_type_exists(s.get("project_type"))
            # check project exists, create if not
            p = self.check_project_exists(
                s.get("project_name"), s.get("out_root_dir"), pt
            )
        else:
            pt = None
            p = None

        if test_run == False:
            # write to db
            mf = am_models.Media_Fact(
                name=data["name"],
                extension_filtered=data["extension_filtered"],
                file_name=data["file_name"],
                file_extension=data["extension"],
                proxy_file_name=data["proxy_file_name"],
                height=metadata["height"],
                width=metadata["width"],
                channels=metadata["channels"],
                file_location_fk=flo,
                file_type_fk=mt,
                proxy_file_location_fk=pflo,
                project_fk=p,
                tags=tagulous.utils.parse_tags(s.get("tags")),
                datetime_created=metadata["date_created"],
            )
            mf.save()

    def upload_image_comp_file(self, data, s, test_run):
        logging.info("HelperTools.upload_image_comp_file running.")
        """
        inputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: <str>(test_file_prx.TXT),
                proxy_file_location: <str>(/path/to/file),
             }
             s - HelperTools.Setup
        outputs:
        """

        # get metadata for file
        metadata = self.get_image_comp_metadata(
            os.path.join(data["file_location"], data["file_name"])
        )

        # create proxy image
        data = self.create_proxy_image(data, s, test_run)

        # check variables exist in db and extract instances
        mt = self.check_media_type_exists("image")
        # check file location out exists, create if not, make path relative when saving
        flo = self.check_location_exists(
            os.path.relpath(data["file_location_out"], settings.BASE_DIR)
        )
        # check proxy file location out exists, create if not, make path relative when saving
        pflo = self.check_location_exists(
            os.path.relpath(data["proxy_file_location_out"], settings.BASE_DIR)
        )
        if s.get("taks_name") == "add_project":
            # check project type exists, create if not
            pt = self.check_project_type_exists(s.get("project_type"))
            # check project exists, create if not
            p = self.check_project_exists(
                s.get("project_name"), s.get("out_root_dir"), pt
            )
        else:
            pt = None
            p = None

        if test_run == False:
            # write to db
            mf = am_models.Media_Fact(
                name=data["name"],
                extension_filtered=data["extension_filtered"],
                file_name=data["file_name"],
                file_extension=data["extension"],
                proxy_file_name=data["proxy_file_name"],
                height=metadata["height"],
                width=metadata["width"],
                channels=metadata["channels"],
                file_location_fk=flo,
                file_type_fk=mt,
                proxy_file_location_fk=pflo,
                project_fk=p,
                tags=tagulous.utils.parse_tags(s.get("tags")),
                datetime_created=metadata["date_created"],
            )
            mf.save()

    def upload_audio_file(self, data, s, test_run):
        logging.info("HelperTools.upload_audio_file running.")
        """
        inputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: <str>(test_file_prx.TXT),
                proxy_file_location: <str>(/path/to/file),
             }
             s - HelperTools.Setup
        outputs:
        """

        # get metadata for file
        metadata = self.get_audio_metadata(
            os.path.join(data["file_location"], data["file_name"])
        )

        # check variables exist in db and extract instances
        mt = self.check_media_type_exists("audio")
        # check file location out exists, create if not, make path relative when saving
        flo = self.check_location_exists(
            os.path.relpath(data["file_location_out"], settings.BASE_DIR)
        )
        # check proxy file location out exists, create if not, make path relative when saving
        pflo = self.check_location_exists(
            os.path.relpath(data["proxy_file_location_out"], settings.BASE_DIR)
        )
        if s.get("taks_name") == "add_project":
            # check project type exists, create if not
            pt = self.check_project_type_exists(s.get("project_type"))
            # check project exists, create if not
            p = self.check_project_exists(
                s.get("project_name"), s.get("out_root_dir"), pt
            )
        else:
            pt = None
            p = None

        if test_run == False:
            # write to db
            mf = am_models.Media_Fact(
                name=data["name"],
                extension_filtered=data["extension_filtered"],
                file_name=data["file_name"],
                file_extension=data["extension"],
                proxy_file_name=data["proxy_file_name"],
                duration_sec=metadata["duration_sec"],
                bitrate=metadata["bitrate"],
                channels=metadata["channels"],
                sample_rate_hz=metadata["sample_rate_hz"],
                file_location_fk=flo,
                file_type_fk=mt,
                proxy_file_location_fk=pflo,
                project_fk=p,
                tags=tagulous.utils.parse_tags(s.get("tags")),
                datetime_created=metadata["date_created"],
            )
            mf.save()

    def upload_other_file(self, data, s, test_run):
        logging.info("HelperTools.upload_other_file running.")
        """
        inputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: <str>(test_file_prx.TXT),
                proxy_file_location: <str>(/path/to/file),
             }
             s - HelperTools.Setup
        outputs:
        """

        # check variables exist in db and extract instances
        mt = self.check_media_type_exists("other")
        # check file location out exists, create if not, make path relative when saving
        flo = self.check_location_exists(
            os.path.relpath(data["file_location_out"], settings.BASE_DIR)
        )
        # check proxy file location out exists, create if not, make path relative when saving
        pflo = self.check_location_exists(
            os.path.relpath(data["proxy_file_location_out"], settings.BASE_DIR)
        )
        if s.get("taks_name") == "add_project":
            # check project type exists, create if not
            pt = self.check_project_type_exists(s.get("project_type"))
            # check project exists, create if not
            p = self.check_project_exists(
                s.get("project_name"), s.get("out_root_dir"), pt
            )
        else:
            pt = None
            p = None

        fname = pathlib.Path(os.path.join(data["file_location"], data["file_name"]))
        dc_str = datetime.datetime.fromtimestamp(fname.stat().st_ctime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        if test_run == False:
            # write to db
            mf = am_models.Media_Fact(
                name=data["name"],
                extension_filtered=data["extension_filtered"],
                file_name=data["file_name"],
                file_extension=data["extension"],
                proxy_file_name=data["proxy_file_name"],
                file_location_fk=flo,
                file_type_fk=mt,
                proxy_file_location_fk=pflo,
                project_fk=p,
                tags=tagulous.utils.parse_tags(s.get("tags")),
                datetime_created=dc_str,
            )
            mf.save()

    # ----------------------------------------------------------------------------------------
    # functions to pull metadata from files
    # ----------------------------------------------------------------------------------------
    def get_video_metadata(self, in_file):
        logging.info("HelperTools.get_video_metadata running.")
        logging.info("   in_file:" + in_file + "\n")
        """
        inputs:
            file_path - <str>(/path/to/file/test_file.mp4)
        outputs:
            {
                fps: <double>(23.98),
                frame_count: <int>(144),
                duration: <double>(6.01) seconds,
                height: <int>(1080),
                width: <int>(1920),
                date_created: <datetime>(),
            }
        """
        height = 0
        width = 0
        cap = cv2.VideoCapture(in_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        frame_count = round(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        fname = pathlib.Path(in_file)
        dc_str = datetime.datetime.fromtimestamp(fname.stat().st_ctime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        data = {
            "fps": round(fps, 2),
            "frame_count": frame_count,
            "duration": round(duration, 2),
            "height": round(height),
            "width": round(width),
            "date_created": dc_str,
        }

        return data

    def get_cdng_metadata(self, data):
        logging.info("HelperTools.get_cdng_metadata running.")
        """
        inputs:
            {
                name: <str>(A001_004),
                file_name: <str>(A001_004),
                file_location:  <str>(/path/to/CDNG),
                extension: <str>(.DNG),
                extension_filtered: <str>(cdng),
                proxy_file_name: <str>(test_file_prx.TXT),
                proxy_file_location: <str>(/path/to/Proxies),
             }
        outputs:
            {
                fps: <double>(23.98),
                frame_count: <int>(144),
                duration: <double>(6.01) seconds,
                height: <int>(1080),
                width: <int>(1920),
                date_created: <datetime>(),
            }
        """
        path = os.path.join(data["file_location"], data["file_name"])
        height = 0
        width = 0

        # find 1 of the data['extension'] (.DNG) files
        for f in os.listdir(path):
            fn, ext = os.path.splitext(os.path.join(path, f))
            if ext.upper() == data["extension"]:
                break
        image_fn = os.path.join(path, f)

        # get dimensions from file
        with rawpy.imread(image_fn) as raw:
            rgb = raw.postprocess()
        height = rgb.shape[0]
        width = rgb.shape[1]

        # get date time created
        fname = pathlib.Path(image_fn)
        dc_str = datetime.datetime.fromtimestamp(fname.stat().st_ctime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # get durations from proxy file
        prx_file = os.path.join(data["proxy_file_location"], data["proxy_file_name"])
        cap = cv2.VideoCapture(prx_file)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = round(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps

        data = {
            "fps": round(fps, 2),
            "frame_count": frame_count,
            "duration": round(duration, 2),
            "height": round(height),
            "width": round(width),
            "date_created": dc_str,
        }

        return data

    def get_image_raw_metadata(self, in_file, extension_filtered):
        logging.info("HelperTools.get_image_raw_metadata running.")
        logging.info("   in_file:" + in_file + "\n")
        """
        inputs:
                file_path - <str>(/path/to/file/test_file.cr3)
        outputs:
            metadata {
                height: <int>(1080),
                width: <int>(1920),
                channels: <int>(3),
                date_created: <datetime>(),
            }
        """

        if extension_filtered == "cr3":
            im = Image_cr3(os.path.join(in_file))
            im = Image_pil.open(io.BytesIO(im.jpeg_image))
            width = im.size[0]
            height = im.size[1]
            channels = len(im.getbands())
        else:
            raw = rawpy.imread(os.path.join(in_file))
            rgb = raw.postprocess(use_camera_wb=True)
            height = rgb.shape[0]
            width = rgb.shape[1]
            channels = rgb.shape[2]

        fname = pathlib.Path(in_file)
        dc_str = datetime.datetime.fromtimestamp(fname.stat().st_ctime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        data = {
            "height": height,
            "width": width,
            "channels": channels,
            "date_created": dc_str,
        }

        return data

    def get_image_comp_metadata(self, in_file):
        logging.info("HelperTools.get_image_comp_metadata running.")
        logging.info("   in_file:" + in_file + "\n")
        """
        inputs:
                file_path - <str>(/path/to/file/test_file.jpg)
        outputs:
            metadata {
                height: <int>(1080),
                width: <int>(1920),
                channels: <int>(3),
                date_created: <datetime>(),
            }
        """
        img = cv2.imread(in_file, cv2.IMREAD_UNCHANGED)
        dim = img.shape
        height = dim[0]
        width = dim[1]
        channels = dim[2]

        fname = pathlib.Path(in_file)
        dc_str = datetime.datetime.fromtimestamp(fname.stat().st_ctime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        data = {
            "height": height,
            "width": width,
            "channels": channels,
            "date_created": dc_str,
        }

        return data

    def get_audio_metadata(self, in_file):
        logging.info("HelperTools.get_audio_metadata running.")
        logging.info("   in_file:" + in_file + "\n")
        """
        inputs:
                in_file - <str>(/path/to/file/test_file.mp3)
        outputs:
            metadata {
                duration_sec: <int>(120),
                bitrate:
                channels:
                sample_rate_hz:
                date_created: <datetime>(),
            }
        """

        metadata = audio_metadata.load(in_file)
        fname = pathlib.Path(in_file)
        dc_str = datetime.datetime.fromtimestamp(fname.stat().st_ctime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        data = {
            "duration_sec": round(metadata["streaminfo"]["duration"]),
            "bitrate": metadata["streaminfo"]["bitrate"],
            "channels": metadata["streaminfo"]["channels"],
            "sample_rate_hz": metadata["streaminfo"]["sample_rate"],
            "date_created": dc_str,
        }

        return data

    # ----------------------------------------------------------------------------------------
    # db functions
    # ----------------------------------------------------------------------------------------
    def check_media_type_exists(self, type):
        # check media type video exists, create if not
        mtd = am_models.Media_Type_Dim.objects.filter(name=type.lower())
        if mtd.count() <= 0:
            mtd = am_models.Media_Type_Dim(name=type.lower())
            mtd.save()
        else:
            mtd = am_models.Media_Type_Dim.objects.get(name=type.lower())

        return mtd

    def check_project_type_exists(self, in_pt):
        logging.info("HelperTools.check_project_type_exists running.")
        """
        inputs:
            in_pt = <str>(video)
        outputs:
            ml.apps.add_media.models.Project_Type_Dim instance
        """
        # check media location exists, create if not, make path relative when saving
        l = am_models.Project_Type_Dim.objects.filter(name=in_pt)
        if l.count() <= 0:
            l = am_models.Project_Type_Dim(name=in_pt)
            l.save()
        else:
            l = am_models.Project_Type_Dim.objects.get(name=in_pt)

        return l

    def check_project_exists(self, in_name, in_dir, in_pt):
        logging.info("HelperTools.check_project_exists running.")
        """
        inputs:
            in_name = <str>(project_name)
            in_path = <str>(/path/to/file)>
            in_pt = ml.apps.add_media.models.Project_Fact instance
        outputs:
            ml.apps.add_media.models.Project_Type_Dim instance
        """
        l = self.check_location_exists(os.path.relpath(in_dir, settings.BASE_DIR))
        p = am_models.Project_Fact.objects.filter(name=in_name)
        if p.count() <= 0:
            p = am_models.Project_Fact(
                name=in_name,
                project_type_fk=in_pt,
                project_location_fk=l,
            )
            p.save()
        else:
            p = am_models.Project_Fact.objects.get(name=in_name)

        return p

    def check_location_exists(self, path):
        logging.info("HelperTools.check_location_exists running.")
        logging.info("   path:" + path + "\n")
        """
        inputs:
            path = <str(/path/to/file)>
        outputs:
            ml.apps.add_media.models.Location_Fact instance
        """
        p = pathlib.PureWindowsPath(path)
        # check media location exists, create if not, make path relative when saving
        l = am_models.Location_Fact.objects.filter(path=p.as_posix())
        if l.count() <= 0:
            l = am_models.Location_Fact(path=p.as_posix())
            l.save()
        else:
            l = am_models.Location_Fact.objects.get(path=p.as_posix())

        return l

    # ----------------------------------------------------------------------------------------
    # other functions
    # ----------------------------------------------------------------------------------------
    def create_proxy_image(self, data, s, test_run):
        logging.info("HelperTools.create_proxy_image running.")
        """
        inputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                file_location_out:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: None,
                proxy_file_location: None,
                proxy_file_location_out: None,
             }
             s - HelperTools.Setup
        outputs:
            {
                name: <str>(test_file),
                file_name: <str>(test_file.TXT),
                file_location:  <str>(/path/to/file),
                file_location_out:  <str>(/path/to/file),
                extension: <str>(.TXT),
                extension_filtered: <str>(txt),
                proxy_file_name: <str>(test_file_prx.TXT),
                proxy_file_location: <str>(/path/to/file),
                proxy_file_location_out: <str>(/path/to/file),
             }
        """

        # variables
        in_file = os.path.join(data["file_location"], data["file_name"])
        prx_file = os.path.join(
            data["file_location"],
            data["name"]
            + s.get("datetime_suffix")
            + "_"
            + data["extension_filtered"]
            + "_prx.jpg",
        )

        # check for raw image file type
        if data["extension_filtered"] in s.get("image_raw_ext") and not test_run:

            # create proxy for cr3 files
            if data["extension_filtered"] == "cr3":
                im = Image_cr3(in_file)
                im = Image_pil.open(io.BytesIO(im.jpeg_image))
                ratio_ds = im.size[0] / 700
                width_ds = int(im.size[0] / ratio_ds)
                height_ds = int(im.size[1] / ratio_ds)
                im = im.resize(
                    (
                        width_ds,
                        height_ds,
                    )
                )
                im.save(prx_file, quality=70, optimize=True)
            # create prox for other raw file types
            else:
                raw = rawpy.imread(in_file)
                rgb = raw.postprocess(use_camera_wb=True)
                im = Image_pil.fromarray(rgb)
                ratio_ds = im.size[0] / 700
                width_ds = int(im.size[0] / ratio_ds)
                height_ds = int(im.size[1] / ratio_ds)
                im = im.resize(
                    (
                        width_ds,
                        height_ds,
                    )
                )
                im.save(prx_file, quality=70, optimize=True)
                raw.close()

        # check for comp image files type
        elif data["extension_filtered"] in s.get("image_comp_ext") and not test_run:
            im = Image_pil.open(in_file)
            ratio_ds = im.size[0] / 700
            width_ds = int(im.size[0] / ratio_ds)
            height_ds = int(im.size[1] / ratio_ds)
            im = im.resize(
                (
                    width_ds,
                    height_ds,
                )
            )
            im.save(prx_file, quality=70, optimize=True)

        data["proxy_file_name"] = data["name"] + s.get("datetime_suffix") + "_prx.jpg"
        data["proxy_file_location"] = data["file_location"]
        data["proxy_file_location_out"] = os.path.join(
            s.get("out_root_dir"),
            os.path.relpath(data["file_location"], s.get("project_dir")),
        )

        return data

    def change_permissions_recursive(self, path, mode):
        logging.info("HelperTools.get_image_comp_metadata running.")
        """
        inputs:
                path - <str>(/path/to/folder)
                mode - <>(0o777)
        outputs:
            metadata {
                height: <int>(1080),
                width: <int>(1920),
                channels: <int>(3)
            }
        """
        for root, dirs, files in os.walk(path, topdown=False):
            for dir in [os.path.join(root, d) for d in dirs]:
                os.chmod(dir, mode)
        for file in [os.path.join(root, f) for f in files]:
            os.chmod(file, mode)
