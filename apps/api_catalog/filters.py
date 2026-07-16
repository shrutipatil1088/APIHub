
# This imports the django-filter library.
# It provides ready-made filter classes
from django_filters import rest_framework as filters

from .models import API

# Allowed values for the "ordering" query parameter.
# Used in services.py to validate user input.
ALLOWED_ORDERING_FIELDS = {
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "status",
    "-status",
}



class APIFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the API list endpoint.
    """

    # Filter by API status.
    status = filters.ChoiceFilter(
        choices=API.Status.choices,
    )

    # Search API name using a case-insensitive partial match.
    search = filters.CharFilter(
        field_name="name",
         lookup_expr="icontains",   # icontains:Case-insensitive partial matching
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("status", "status"),
        ),
    )

    # This filter set works for the API model, and these are the fields it exposes
    class Meta:
        model = API
        fields = (
            "status",
            "search",
            "is_active",
        )