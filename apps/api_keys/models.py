import uuid

from django.db import models

from apps.core.models.base import BaseModel
from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import UserSubscription


class APIKey(BaseModel):
    """
    Represents an API Key generated for a developer project.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    project = models.ForeignKey(
        DeveloperProject,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )

    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )

    name = models.CharField(
        max_length=255,
    )

    key_hash = models.CharField(
        max_length=64,
    )


    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "api_keys"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.name} - {self.name}"
