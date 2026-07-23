import uuid

from django.db import models

from apps.core.models.base import BaseModel
from apps.developer_projects.models import DeveloperProject
from apps.api_keys.models import APIKey


class UsageLog(BaseModel):
    """
    Represents an API usage log entry for tracking request metadata.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    api_key = models.ForeignKey(
        APIKey,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_logs",
    )

    project = models.ForeignKey(
        DeveloperProject,
        on_delete=models.CASCADE,
        related_name="usage_logs",
    )

    endpoint = models.CharField(
        max_length=500,
    )

    method = models.CharField(
        max_length=10,
    )

    status_code = models.PositiveIntegerField()

    response_time_ms = models.PositiveIntegerField()

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
    )

    requested_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "usage_logs"
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.project.name} - {self.method} {self.endpoint} ({self.status_code})"
