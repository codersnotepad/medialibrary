from django.db import models
import tagulous.models

# Create your models here.


class Audio_Ext_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = True
        blank = True


class Video_Comp_Ext_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = True
        blank = True


class Video_RAW_Ext_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = True
        blank = True


class Image_Comp_Ext_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = True
        blank = True


class Image_RAW_Ext_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = True
        blank = True


class Other_Ext_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = True
        blank = True


class Ignore_Files_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = False
        blank = True


class Ignore_Folders_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = False
        blank = True


class Settings(models.Model):
    audio_ext = tagulous.models.TagField(
        Audio_Ext_Tags,
        help_text="List of audio file extensions that will be searched for",
    )
    video_comp_ext = tagulous.models.TagField(
        Video_Comp_Ext_Tags,
        help_text="List of video file extensions that will be searched for",
    )
    video_raw_ext = tagulous.models.TagField(
        Video_RAW_Ext_Tags,
        help_text="List of video file extensions that will be searched for",
    )
    image_comp_ext = tagulous.models.TagField(
        Image_Comp_Ext_Tags,
        help_text="List of non RAW image file extensions that will be searched for",
    )
    image_raw_ext = tagulous.models.TagField(
        Image_RAW_Ext_Tags,
        help_text="List of RAW image file extensions that will be searched for",
    )
    other_ext = tagulous.models.TagField(
        Other_Ext_Tags,
        help_text="List of other file extensions that will be searched for",
    )
    ignore_files = tagulous.models.TagField(
        Ignore_Files_Tags,
        help_text="List of files to ignore, case sensitive",
    )
    ignore_folders = tagulous.models.TagField(
        Ignore_Folders_Tags,
        help_text="List of folders to ignore, case sensitive",
    )
