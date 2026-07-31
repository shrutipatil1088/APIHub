import uuid
from django.db import models
from apps.accounts.models import User
from apps.core.models.base import BaseModel


class Notification(BaseModel):
    """
    Represents a real-time system or user notification in APIHub.
    Inherits from BaseModel (provides created_at, updated_at, is_deleted, deleted_at, is_active).
    """

    class NotificationType(models.TextChoices):
        API_PUBLISHED = "API_PUBLISHED", "API Published"
        DEVELOPER_REGISTERED = "DEVELOPER_REGISTERED", "Developer Registered"
        PROJECT_CREATED = "PROJECT_CREATED", "Project Created"
        API_KEY_CREATED = "API_KEY_CREATED", "API Key Created"
        SUBSCRIPTION_CREATED = "SUBSCRIPTION_CREATED", "Subscription Created"
        USAGE_LIMIT_REACHED = "USAGE_LIMIT_REACHED", "Usage Limit Reached"
        SYSTEM = "SYSTEM", "System Notification"

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )

    title = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )

    is_read = models.BooleanField(
        default=False,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        recipient_str = self.recipient.email if self.recipient else "Admin"
        return f"[{self.notification_type}] {self.title} -> {recipient_str}"
