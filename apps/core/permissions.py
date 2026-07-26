# apps/core/permissions.py

from rest_framework.permissions import BasePermission

from apps.accounts.models import User


class IsAdminRole(BasePermission):
    """
    Allows access only to users with ADMIN role.
    """

    message = "Only admins can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )


class IsDeveloperRole(BasePermission):
    """
    Allows access only to users with DEVELOPER role.
    """

    message = "Only developers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.DEVELOPER
        )