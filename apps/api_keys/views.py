import time
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
from apps.usage_logs.services import UsageLogService

from .authentication import APIKeyAuthentication
from .serializers import (
    APIKeyBaseSerializer,
    APIKeySerializer,
    APIKeyUpdateSerializer,
    ProtectedSampleResponseSerializer,
)
from .services import APIKeyService


# ============================================================================
# APIKey List & Create
# Handles:
# GET  -> List all API keys (Owner-filtered for Developers, all for Admins)
# POST -> Generate a new API key (Developer only with active subscription)
# ============================================================================
class APIKeyListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for List API Keys.
    @extend_schema(
        summary="List API Keys",
        description="""
Returns a paginated list of API keys for developer projects.

Permissions:
- Admin: View all API keys.
- Developer: View only keys belonging to their own projects.

Supports:
- Search (by key name)
- Filtering
- Ordering (by name, created_at, updated_at, last_used_at)
- Pagination
""",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search API keys by name.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order results by field (e.g., name, -name, created_at, last_used_at).",
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
        responses={200: APIKeySerializer(many=True)},
        tags=["API Keys"],
    )
    def get(self, request):
        keys = APIKeyService.list_keys(
            request.user,
            request.query_params,
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(keys, request)
        serializer = APIKeySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Swagger documentation for Generate API Key.
    @extend_schema(
        summary="Generate API Key",
        description="""
Generates a new secure API key for a developer project. Returns plain text key ONCE.

Permissions:
- Developer role with active subscription

Validation rules:
- Project must belong to the developer.
- Requires active and unexpired developer subscription.
""",
        request=APIKeyBaseSerializer,
        responses={201: APIKeySerializer},
        tags=["API Keys"],
    )
    def post(self, request):
        if request.user.role != User.Role.DEVELOPER:
            raise PermissionDenied("Only developers can generate API keys.")

        serializer = APIKeyBaseSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        api_key, plain_key = APIKeyService.create_key(
            request.user,
            serializer.validated_data,
        )
        return success_response(
            data={
                "api_key": plain_key,
                "key": APIKeySerializer(api_key).data,
            },
            message="API key generated successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# APIKey Detail
# Handles:
# GET    -> Retrieve key metadata (Owner or Admin)
# PATCH  -> Rename key (Owner only)
# DELETE -> Deactivate key (Owner only)
# ============================================================================
class APIKeyDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Retrieve API Key Details.
    @extend_schema(
        summary="Retrieve API Key Details",
        description="""
Retrieves metadata for a specific API key by UUID.

Permissions:
- Admin: View any key metadata.
- Developer: View only their own key metadata.
""",
        responses={200: APIKeySerializer},
        tags=["API Keys"],
    )
    def get(self, request, uuid):
        key = APIKeyService.get_key(uuid)
        if (
            request.user.role != User.Role.ADMIN
            and key.project.developer != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this API key."
            )
        serializer = APIKeySerializer(key)
        return success_response(
            data=serializer.data,
            message="API key details fetched successfully.",
        )

    # Swagger documentation for Rename API Key.
    @extend_schema(
        summary="Rename API Key",
        description="""
Renames an existing API key by UUID.

Permissions:
- Key Owner only
""",
        request=APIKeyUpdateSerializer,
        responses={200: APIKeySerializer},
        tags=["API Keys"],
    )
    def patch(self, request, uuid):
        key = APIKeyService.get_key(uuid)
        if key.project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to modify this API key."
            )
        serializer = APIKeyUpdateSerializer(
            key,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        key = APIKeyService.update_key(
            key,
            serializer.validated_data,
        )
        return success_response(
            data=APIKeySerializer(key).data,
            message="API key updated successfully.",
        )

    # Swagger documentation for Deactivate API Key.
    @extend_schema(
        summary="Deactivate API Key",
        description="""
Deactivates an active API key by UUID.

Permissions:
- Key Owner only
""",
        responses={200: None},
        tags=["API Keys"],
    )
    def delete(self, request, uuid):
        key = APIKeyService.get_key(uuid)
        if key.project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to deactivate this API key."
            )
        APIKeyService.deactivate_key(key)
        return success_response(
            message="API key deactivated successfully.",
        )


# ============================================================================
# APIKey Regenerate
# Handles:
# POST -> Regenerate API key (Owner only)
# ============================================================================
class APIKeyRegenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Regenerate API Key.
    @extend_schema(
        summary="Regenerate API Key",
        description="""
Regenerates an API key by generating a new secret hash and returning the plain key ONCE.

Permissions:
- Key Owner only with active subscription
""",
        request=None,
        responses={200: APIKeySerializer},
        tags=["API Keys"],
    )
    def post(self, request, uuid):
        key = APIKeyService.get_key(uuid)
        if key.project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to regenerate this API key."
            )
        key, plain_key = APIKeyService.regenerate_key(key)
        return success_response(
            data={
                "api_key": plain_key,
                "key": APIKeySerializer(key).data,
            },
            message="API key regenerated successfully.",
        )


# ============================================================================
# Protected Sample Endpoint
# Handles:
# GET -> Sample protected endpoint authenticated exclusively using APIKeyAuthentication
# ============================================================================
class ProtectedSampleAPIView(APIView):
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Protected Sample Endpoint.
    @extend_schema(
        summary="Protected Sample Endpoint",
        description="""
Sample protected API endpoint authenticated exclusively using developer API Key. Validates subscription & monthly usage limit, and automatically records usage log.

Permissions:
- Valid API Key in X-API-Key header (Active & Unexpired Subscription required)
""",
        parameters=[
            OpenApiParameter(
                name="X-API-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Developer API Key (e.g., pk_live_...)",
            ),
        ],
        responses={200: ProtectedSampleResponseSerializer},
        tags=["API Keys"],
    )
    def get(self, request):
        start_time = time.perf_counter()

        developer = request.user
        api_key = request.auth

        data = {
            "developer_uuid": developer.uuid,
            "developer_email": developer.email,
            "api_key_uuid": api_key.uuid,
            "project_uuid": api_key.project.uuid,
            "project_name": api_key.project.name,
        }

        serializer = ProtectedSampleResponseSerializer(data)

        response = success_response(
            data=serializer.data,
            message="API Key authentication successful.",
        )

        UsageLogService.log_request(
            request=request,
            response=response,
            start_time=start_time,
        )

        return response
