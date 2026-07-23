from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from .models import DeveloperProject
from .filters import DeveloperProjectFilter, ALLOWED_ORDERING_FIELDS


class DeveloperProjectService:
    """
    Contains business logic for the DeveloperProject module.
    """

    # Return DeveloperProject list with search, filter and ordering.
    @staticmethod
    def list_projects(user, query_params):
        ordering = query_params.get("ordering")

        if ordering and ordering not in ALLOWED_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        # Admin can see all, developer sees only their own
        if user.role == User.Role.ADMIN:
            queryset = (
                DeveloperProject.objects
                .filter(is_deleted=False)
                .select_related("developer")
            )
        else:
            queryset = (
                DeveloperProject.objects
                .filter(
                    developer=user,
                    is_deleted=False,
                )
                .select_related("developer")
            )

        return DeveloperProjectFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single project by UUID.
    @staticmethod
    def get_project(uuid):
        return get_object_or_404(
            DeveloperProject.objects.select_related("developer"),
            uuid=uuid,
            is_deleted=False,
        )

    # Create a new developer project.
    @staticmethod
    def create_project(user, validated_data):
        # Validate that only DEVELOPER role users can create a project.
        if user.role != User.Role.DEVELOPER:
            raise ValidationError(
                {"detail": "Only developers can create projects."}
            )

        return DeveloperProject.objects.create(
            developer=user,
            **validated_data,
        )

    # Update an existing project.
    @staticmethod
    def update_project(project, validated_data):
        for field, value in validated_data.items():
            setattr(
                project,
                field,
                value,
            )

        project.save(
            update_fields=[
                *validated_data.keys(),
                "updated_at",
            ]
        )

        return project

    # Soft delete a project.
    @staticmethod
    def delete_project(project):
        project.soft_delete()
