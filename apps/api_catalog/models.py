from django.db import models

# Create your models here.
import uuid

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import transaction
from apps.core.models.base import BaseModel

# API Model
class API(BaseModel):
    """
    Represents an API published by the platform.
    """

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    name = models.CharField(
        max_length=255,
    )

    slug = models.SlugField()

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="apis",
    )

    class Meta:
        db_table = "apis"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    

# APIVersion Model

class APIVersion(BaseModel):
    """
    Represents a version of an API.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    api = models.ForeignKey(
        API,
        on_delete=models.CASCADE,
        related_name="versions",
    )

    version = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^v\d+(\.\d+)*$",
                message="Version must be in a format like 'v1', 'v2', 'v1.0', or 'v1.0.1'."
            )
        ]
    )

    release_notes = models.TextField(
        blank=True,
    )

    is_latest = models.BooleanField(
        default=False,
    )

    class Meta:
        db_table = "api_versions"
        unique_together = ("api", "version")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.api.name} - {self.version}"

    def save(self, *args, **kwargs):
        if self.is_latest:
            with transaction.atomic():
                qs = APIVersion.objects.filter(api=self.api, is_latest=True)
                if self.pk:
                    qs = qs.exclude(pk=self.pk)
                qs.update(is_latest=False)
        super().save(*args, **kwargs)
    

# 3. Endpoint Model

class Endpoint(BaseModel):
    """
    Represents an endpoint belonging to an API version.
    """

    class Method(models.TextChoices):
        GET = "GET", "GET"
        POST = "POST", "POST"
        PUT = "PUT", "PUT"
        PATCH = "PATCH", "PATCH"
        DELETE = "DELETE", "DELETE"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    version = models.ForeignKey(
        APIVersion,
        on_delete=models.CASCADE,
        related_name="endpoints",
    )

    method = models.CharField(
        max_length=10,
        choices=Method.choices,
    )

    path = models.CharField(
        max_length=255,
    )

    summary = models.CharField(
        max_length=255,
    )

    description = models.TextField(
        blank=True,
    )

    request_schema = models.JSONField(
        blank=True,
        null=True,
    )

    response_schema = models.JSONField(
        blank=True,
        null=True,
    )

    class Meta:
        db_table = "api_endpoints"
        ordering = ["path"]
        unique_together = (
            "version",
            "method",
            "path",
        )

    def __str__(self):
        return f"{self.method} {self.path}"