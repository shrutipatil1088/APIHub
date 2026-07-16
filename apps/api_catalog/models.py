from django.db import models

# Create your models here.
import uuid

from django.conf import settings
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