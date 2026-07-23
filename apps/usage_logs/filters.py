from django_filters import rest_framework as filters
from .models import UsageLog

# Allowed values for the "ordering" query parameter.
ALLOWED_ORDERING_FIELDS = {
    "requested_at",
    "-requested_at",
    "status_code",
    "-status_code",
    "response_time_ms",
    "-response_time_ms",
}


class UsageLogFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the UsageLog list endpoint.
    """

    # Search endpoint using a case-insensitive partial match.
    search = filters.CharFilter(
        field_name="endpoint",
        lookup_expr="icontains",
    )

    # Filter by project UUID
    project = filters.UUIDFilter(
        field_name="project__uuid",
    )

    # Filter by API key UUID
    api_key = filters.UUIDFilter(
        field_name="api_key__uuid",
    )

    # Filter by HTTP status code
    status_code = filters.NumberFilter(
        field_name="status_code",
    )

    # Filter by HTTP method
    method = filters.CharFilter(
        field_name="method",
        lookup_expr="iexact",
    )

    # Date range filters for requested_at
    requested_at_after = filters.DateTimeFilter(
        field_name="requested_at",
        lookup_expr="gte",
    )

    requested_at_before = filters.DateTimeFilter(
        field_name="requested_at",
        lookup_expr="lte",
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("requested_at", "requested_at"),
            ("status_code", "status_code"),
            ("response_time_ms", "response_time_ms"),
        ),
    )

    class Meta:
        model = UsageLog
        fields = (
            "search",
            "project",
            "api_key",
            "status_code",
            "method",
            "requested_at_after",
            "requested_at_before",
        )
