from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model with common audit fields.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_deleted = models.BooleanField(
        default=False,
    )

    class Meta:
        abstract = True

    def soft_delete(self):
        """
        Soft delete the object.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )

    def restore(self):
        """
        Restore a soft deleted object.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(
            update_fields=[
                "is_deleted",
                "deleted_at",
            ]
        )