from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError


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

    def check_active_dependencies(self):
        """
        Dynamically check if there are any active (non-deleted) related objects.
        Returns a list of tuples containing (verbose_model_name, count) if dependencies exist.
        """
        dependencies = []
        for relation in self._meta.related_objects:
            accessor_name = relation.get_accessor_name()
            if not accessor_name:
                continue

            try:
                related_manager = getattr(self, accessor_name, None)
            except models.ObjectDoesNotExist:
                # For OneToOneField relationships that do not exist
                continue

            if related_manager is None:
                continue

            related_model = relation.related_model
            has_is_deleted = any(f.name == "is_deleted" for f in related_model._meta.fields)

            # Check if it is a plural relationship manager (OneToMany)
            if hasattr(related_manager, "filter"):
                if has_is_deleted:
                    active_count = related_manager.filter(is_deleted=False).count()
                else:
                    active_count = related_manager.count()
            else:
                # Single relationship (OneToOne)
                if has_is_deleted:
                    active_count = 1 if not related_manager.is_deleted else 0
                else:
                    active_count = 1

            if active_count > 0:
                verbose_name = related_model._meta.verbose_name or related_model.__name__
                dependencies.append((verbose_name.title(), active_count))

        return dependencies

    def soft_delete(self):
        """
        Soft delete the object, preventing it if there are active dependencies.
        """
        dependencies = self.check_active_dependencies()
        if dependencies:
            dep_msg = ", ".join([f"{name} ({count})" for name, count in dependencies])
            raise ValidationError(
                {"detail": f"Cannot delete {self._meta.verbose_name.title()} because it is used in: {dep_msg}."}
            )

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