from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model with common audit fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True