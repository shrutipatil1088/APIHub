from django.urls import path

from .views import (
    UsageLogListAPIView,
    UsageLogDetailAPIView,
)

urlpatterns = [
    # List all usage logs.
    path(
        "usage-logs/",
        UsageLogListAPIView.as_view(),
        name="usage-log-list",
    ),

    # Retrieve a specific usage log by UUID.
    path(
        "usage-logs/<uuid:uuid>/",
        UsageLogDetailAPIView.as_view(),
        name="usage-log-detail",
    ),
]
