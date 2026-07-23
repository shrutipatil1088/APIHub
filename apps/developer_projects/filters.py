from django_filters import rest_framework as filters
from django.db.models import Q
from .models import DeveloperProject

# Allowed values for the "ordering" query parameter.
ALLOWED_ORDERING_FIELDS = {
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
}


class DeveloperProjectFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the DeveloperProject list endpoint.
    """

    # Search project name or description using a case-insensitive partial match.
    search = filters.CharFilter(
        method="filter_search",
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ),
    )

    class Meta:
        model = DeveloperProject
        fields = (
            "search",
        )

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )
