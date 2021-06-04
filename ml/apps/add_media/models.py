from django.db import models
import tagulous.models

# Create your models here.
class Media_Tags(tagulous.models.TagTreeModel):
    class TagMeta:
        space_delimiter = False
        force_lowercase = True
        blank = True


class Media_Type_Dim(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Project_Type_Dim(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Location_Fact(models.Model):
    path = models.CharField(max_length=500, unique=True)


class Project_Fact(models.Model):
    name = models.CharField(max_length=100, unique=False, null=False)
    project_type_fk = models.ForeignKey(
        Project_Type_Dim, on_delete=models.CASCADE, null=False
    )
    project_location_fk = models.ForeignKey(
        Location_Fact, on_delete=models.CASCADE, null=False
    )


class Media_Fact(models.Model):
    name = models.CharField(max_length=100, unique=False, null=False)
    extension_filtered = models.CharField(max_length=20, unique=False, null=False)
    file_name = models.CharField(max_length=100, unique=False, null=False)
    file_extension = models.CharField(max_length=20, unique=False, null=False)
    proxy_file_name = models.CharField(max_length=200, unique=False, null=False)
    height = models.IntegerField(null=True)
    width = models.IntegerField(null=True)
    fps = models.DecimalField(null=True, max_digits=10, decimal_places=2)
    frame_count = models.IntegerField(null=True)
    duration_sec = models.IntegerField(null=True)
    bitrate = models.IntegerField(null=True)
    channels = models.IntegerField(null=True)
    sample_rate_hz = models.IntegerField(null=True)
    tags = tagulous.models.TagField(
        Media_Tags,
        help_text="This field splits on commas",
    )
    file_type_fk = models.ForeignKey(
        Media_Type_Dim, on_delete=models.CASCADE, null=False
    )
    file_location_fk = models.ForeignKey(
        Location_Fact,
        on_delete=models.CASCADE,
        null=False,
        related_name="file_location",
    )
    proxy_file_location_fk = models.ForeignKey(
        Location_Fact,
        on_delete=models.CASCADE,
        null=False,
        related_name="proxy_file_location",
    )
    project_fk = models.ForeignKey(Project_Fact, on_delete=models.CASCADE, null=True)
    datetime_created = models.DateTimeField(blank=True)
    datetime_added = models.DateTimeField(auto_now_add=True, blank=True)
