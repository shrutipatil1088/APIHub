from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.core.permissions import IsAdminRole
from apps.core.responses import success_response

from .serializers import (
    AdminDashboardSerializer,
    DeveloperDashboardSerializer,
)
from .services import DashboardService


# ============================================================================
# Admin Dashboard Analytics Endpoint
# Handles:
# GET -> Retrieve platform-wide system metrics (Admin only)
# ============================================================================
class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminRole]

    # Swagger documentation for Admin Dashboard.
    @extend_schema(
        summary="Retrieve Admin Dashboard Analytics",
        description="""
Retrieves platform-wide system analytics and metrics for Admin users.

Permissions:
- Admin Users only
""",
        responses={200: AdminDashboardSerializer},
        tags=["Dashboard"],
    )
    def get(self, request):
        analytics = DashboardService.get_admin_dashboard(request.user)
        serializer = AdminDashboardSerializer(analytics)
        return success_response(
            data=serializer.data,
            message="Admin dashboard analytics fetched successfully.",
        )


# ============================================================================
# Developer Dashboard Analytics Endpoint
# Handles:
# GET -> Retrieve developer project & request metrics (Developer only)
# ============================================================================
class DeveloperDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Developer Dashboard.
    @extend_schema(
        summary="Retrieve Developer Dashboard Analytics",
        description="""
Retrieves developer-specific analytics, active subscription metadata, and request limits for the authenticated developer.

Permissions:
- Authenticated Developer Users
""",
        responses={200: DeveloperDashboardSerializer},
        tags=["Dashboard"],
    )
    def get(self, request):
        analytics = DashboardService.get_developer_dashboard(request.user)
        serializer = DeveloperDashboardSerializer(analytics)
        return success_response(
            data=serializer.data,
            message="Developer dashboard analytics fetched successfully.",
        )
