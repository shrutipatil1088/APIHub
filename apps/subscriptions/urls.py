from django.urls import path

from .views import (
    SubscriptionPlanListCreateAPIView,
    SubscriptionPlanDetailAPIView,
)

urlpatterns = [
    # List all subscription plans and create a new plan.
    path(
        "",
        SubscriptionPlanListCreateAPIView.as_view(),
        name="subscription-plan-list-create",
    ),

    # Retrieve, update, or delete a specific subscription plan by UUID.
    path(
        "<uuid:uuid>/",
        SubscriptionPlanDetailAPIView.as_view(),
        name="subscription-plan-detail",
    ),
]
