from django.urls import path

from .views import (
    AdminDashboardAPIView,
    DeveloperDashboardAPIView,
)

urlpatterns = [
    # Admin dashboard analytics endpoint
    path(
        "dashboard/admin/",
        AdminDashboardAPIView.as_view(),
        name="dashboard-admin",
    ),

    # Developer dashboard analytics endpoint
    path(
        "dashboard/developer/",
        DeveloperDashboardAPIView.as_view(),
        name="dashboard-developer",
    ),
]
