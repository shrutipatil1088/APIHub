from django.urls import path

from .views import (
    SubscriptionPlanListCreateAPIView,
    SubscriptionPlanDetailAPIView,
    UserSubscriptionListCreateAPIView,
    UserSubscriptionDetailAPIView,
    MySubscriptionListAPIView,
)

urlpatterns = [
    # ============================================================================
    # SubscriptionPlan URL Patterns
    # ============================================================================

    # List all subscription plans and create a new plan.
    path(
        "subscription-plans/",
        SubscriptionPlanListCreateAPIView.as_view(),
        name="subscription-plan-list-create",
    ),

    # Retrieve, update, or delete a specific subscription plan by UUID.
    path(
        "subscription-plans/<uuid:uuid>/",
        SubscriptionPlanDetailAPIView.as_view(),
        name="subscription-plan-detail",
    ),

    # ============================================================================
    # UserSubscription URL Patterns
    # ============================================================================

    # List all user subscriptions and purchase a new subscription.
    path(
        "subscriptions/",
        UserSubscriptionListCreateAPIView.as_view(),
        name="user-subscription-list-create",
    ),

    # List subscriptions of the current authenticated user.
    path(
        "subscriptions/me/",
        MySubscriptionListAPIView.as_view(),
        name="user-subscription-me",
    ),

    # Retrieve, update, or delete a specific user subscription by UUID.
    path(
        "subscriptions/<uuid:uuid>/",
        UserSubscriptionDetailAPIView.as_view(),
        name="user-subscription-detail",
    ),
]
