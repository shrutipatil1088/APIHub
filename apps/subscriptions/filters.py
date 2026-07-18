from django_filters import rest_framework as filters
from .models import SubscriptionPlan

# Allowed values for the "ordering" query parameter.
# Used in services.py to validate user input.
ALLOWED_ORDERING_FIELDS = {
    "name",
    "-name",
    "price",
    "-price",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
}


class SubscriptionPlanFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the SubscriptionPlan list endpoint.
    """

    # Filter by billing cycle.
    billing_cycle = filters.ChoiceFilter(
        choices=SubscriptionPlan.BillingCycle.choices,
    )

    # Filter by active status.
    is_active = filters.BooleanFilter()

    # Search subscription plan name using a case-insensitive partial match.
    search = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("name", "name"),
            ("price", "price"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
        ),
    )

    class Meta:
        model = SubscriptionPlan
        fields = (
            "billing_cycle",
            "is_active",
            "search",
        )
