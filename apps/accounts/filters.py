from django.db.models import Q
from django_filters import rest_framework as filters

from .models import User

ALLOWED_DEVELOPER_ORDERING_FIELDS = {
    "email",
    "-email",
    "full_name",
    "-full_name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
}


class DeveloperFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the Developer list endpoint.
    """

    is_active = filters.BooleanFilter()
    search = filters.CharFilter(method="filter_search")
    ordering = filters.OrderingFilter(
        fields=(
            ("email", "email"),
            ("full_name", "full_name"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        )
    )

    class Meta:
        model = User
        fields = ("is_active", "search")

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(email__icontains=value) | Q(full_name__icontains=value)
        )
