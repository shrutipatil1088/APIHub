import uuid

from django.db import models

from apps.accounts.models import User
from apps.core.models.base import BaseModel


# DeveloperProject Model
class DeveloperProject(BaseModel):
    """
    Represents a project created by a developer on the platform.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    developer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.CharField(
        max_length=255,
    )

    description = models.TextField()

    class Meta:
        db_table = "developer_projects"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.developer.email})"
