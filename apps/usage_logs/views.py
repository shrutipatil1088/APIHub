from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)

from apps.accounts.models import User
from apps.core.pagination import StandardResultsSetPagination
from apps.core.responses import success_response

from .serializers import UsageLogSerializer
from .services import UsageLogService


# ============================================================================
# UsageLog List
# Handles:
# GET -> List usage logs (Owner-filtered for Developers, all for Admins)
# ============================================================================
class UsageLogListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for List Usage Logs.
    @extend_schema(
        summary="List Usage Logs",
        description="""
Returns a paginated list of API usage logs for tracking request execution metadata.

Permissions:
- Admin: View all usage logs.
- Developer: View only usage logs belonging to their own projects.

Supports:
- Search (by endpoint path)
- Filtering (by project UUID, api_key UUID, status_code, method, requested_at date ranges)
- Ordering (by requested_at, status_code, response_time_ms)
- Pagination
""",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search usage logs by endpoint.",
            ),
            OpenApiParameter(
                name="project",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filter by project UUID.",
            ),
            OpenApiParameter(
                name="api_key",
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description="Filter by API key UUID.",
            ),
            OpenApiParameter(
                name="status_code",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Filter by HTTP status code.",
            ),
            OpenApiParameter(
                name="method",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by HTTP method (GET, POST, etc.).",
            ),
            OpenApiParameter(
                name="requested_at_after",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description="Filter logs requested after datetime.",
            ),
            OpenApiParameter(
                name="requested_at_before",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description="Filter logs requested before datetime.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order results by field (e.g., requested_at, -requested_at, status_code, response_time_ms).",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Page number.",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Number of records per page (max 100).",
            ),
        ],
        responses={200: UsageLogSerializer(many=True)},
        tags=["Usage Logs"],
    )
    def get(self, request):
        logs = UsageLogService.list_logs(
            request.user,
            request.query_params,
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(logs, request)
        serializer = UsageLogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


# ============================================================================
# UsageLog Detail
# Handles:
# GET -> Retrieve single usage log details (Owner or Admin)
# ============================================================================
class UsageLogDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Retrieve Usage Log Details.
    @extend_schema(
        summary="Retrieve Usage Log Details",
        description="""
Retrieves metadata details for a specific API usage log entry by UUID.

Permissions:
- Admin: View any usage log details.
- Developer: View only usage logs belonging to their own projects.
""",
        responses={200: UsageLogSerializer},
        tags=["Usage Logs"],
    )
    def get(self, request, uuid):
        log = UsageLogService.get_log(uuid)
        if (
            request.user.role != User.Role.ADMIN
            and log.project.developer != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this usage log."
            )
        serializer = UsageLogSerializer(log)
        return success_response(
            data=serializer.data,
            message="Usage log details fetched successfully.",
        )
