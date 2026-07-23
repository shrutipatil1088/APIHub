from django_filters import rest_framework as filters
from .models import APIKey

# Allowed values for the "ordering" query parameter.
ALLOWED_ORDERING_FIELDS = {
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "last_used_at",
    "-last_used_at",
}


class APIKeyFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the APIKey list endpoint.
    """

    # Search APIKey name using a case-insensitive partial match.
    search = filters.CharFilter(
        method="filter_search",
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("last_used_at", "last_used_at"),
        ),
    )

    class Meta:
        model = APIKey
        fields = (
            "search",
        )

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            name__icontains=value,
        )
