from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
import uuid

from apps.core.models.base import BaseModel

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom user model for APIHub.
    """

    # ==========================
    # Choices / Enums
    # ==========================

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        DEVELOPER = "DEVELOPER", "Developer"

    # ==========================
    # Authentication / Identity Fields
    # ==========================

    uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)


    email = models.EmailField(unique=True)

    # ==========================
    # Personal Information
    # ==========================

    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # ==========================
    # Business Fields
    # ==========================

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DEVELOPER,
    )

    # ==========================
    # Status Fields
    # ==========================
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # ==========================
    # Django Authentication
    # ==========================

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    # ==========================
    # Meta
    # ==========================

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    # ==========================
    # String Representation
    # ==========================

    def __str__(self):
        return self.email