
# This imports the django-filter library.
# It provides ready-made filter classes
from django_filters import rest_framework as filters

from django.db.models import Q
from .models import API, APIVersion, Endpoint

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


# Allowed values for the "ordering" query parameter for API versions.
# Used in services.py to validate user input.
ALLOWED_VERSION_ORDERING_FIELDS = {
    "version",
    "-version",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "is_latest",
    "-is_latest",
}



class APIVersionFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the API Version list endpoint.
    """

    # Filter by latest version.
    is_latest = filters.BooleanFilter()

    # Filter by active status.
    is_active = filters.BooleanFilter()

    # Search version using a case-insensitive partial match.
    search = filters.CharFilter(
        field_name="version",
        lookup_expr="icontains",
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("version", "version"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("is_latest", "is_latest"),
        ),
    )

    class Meta:
        model = APIVersion
        fields = (
            "is_latest",
            "is_active",
            "search",
        )


# Allowed values for the "ordering" query parameter for Endpoints.
# Used in services.py to validate user input.
ALLOWED_ENDPOINT_ORDERING_FIELDS = {
    "path",
    "-path",
    "method",
    "-method",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
}


class EndpointFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the API Endpoint list endpoint.
    """

    # Filter by endpoint HTTP method.
    method = filters.ChoiceFilter(
        choices=Endpoint.Method.choices,
    )

    # Filter by active status.
    is_active = filters.BooleanFilter()

    # Search path or summary using a case-insensitive partial match.
    search = filters.CharFilter(
        method="filter_search",
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("path", "path"),
            ("method", "method"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ),
    )

    class Meta:
        model = Endpoint
        fields = (
            "method",
            "is_active",
            "search",
        )

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(path__icontains=value) | Q(summary__icontains=value)
        )