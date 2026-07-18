from django_filters import rest_framework as filters
from django.db.models import Q
from .models import SubscriptionPlan, UserSubscription

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


# Allowed values for the "ordering" query parameter for UserSubscription.
# Used in services.py to validate user input.
ALLOWED_USER_SUBSCRIPTION_ORDERING_FIELDS = {
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "start_date",
    "-start_date",
    "end_date",
    "-end_date",
}


class UserSubscriptionFilter(filters.FilterSet):
    """
    Handles filtering, searching and ordering for the UserSubscription list endpoint.
    """

    # Filter by subscription status.
    status = filters.ChoiceFilter(
        choices=UserSubscription.Status.choices,
    )

    # Filter by auto renew.
    auto_renew = filters.BooleanFilter()

    # Search user email or plan name using a case-insensitive partial match.
    search = filters.CharFilter(
        method="filter_search",
    )

    # Sort the results.
    ordering = filters.OrderingFilter(
        fields=(
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("start_date", "start_date"),
            ("end_date", "end_date"),
        ),
    )

    class Meta:
        model = UserSubscription
        fields = (
            "status",
            "auto_renew",
            "search",
        )

    def filter_search(self, queryset, name, value):
        value = value.strip()
        if not value:
            return queryset
        return queryset.filter(
            Q(user__email__icontains=value) | Q(plan__name__icontains=value)
        )
