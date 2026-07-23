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
                description=(
                    "Order results. "
                    "Available values: "
                    "requested_at, -requested_at, status_code, -status_code, response_time_ms, -response_time_ms."
                ),
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
        summary="List usage logs.",
    )
    def get(self, request):
        # Fetch filtered/search/ordered queryset.
        logs = UsageLogService.list_logs(
            request.user,
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            logs,
            request,
        )

        # Convert queryset into JSON.
        serializer = UsageLogSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )


# ============================================================================
# UsageLog Detail
# Handles:
# GET -> Retrieve single usage log details (Owner or Admin)
# ============================================================================
class UsageLogDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Retrieve Usage Log details.
    @extend_schema(
        responses={200: UsageLogSerializer},
        tags=["Usage Logs"],
        summary="Retrieve usage log details.",
    )
    def get(self, request, uuid):
        # Fetch UsageLog by UUID.
        log = UsageLogService.get_log(uuid)

        # Check permission: Owner or Admin.
        if (
            request.user.role != User.Role.ADMIN
            and log.project.developer != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this usage log."
            )

        # Convert model into JSON.
        serializer = UsageLogSerializer(log)

        return success_response(
            data=serializer.data,
            message="Usage log details fetched successfully.",
        )
