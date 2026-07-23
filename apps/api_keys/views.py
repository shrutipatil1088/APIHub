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
                description=(
                    "Order results. "
                    "Available values: "
                    "name, -name, created_at, -created_at, updated_at, -updated_at, last_used_at, -last_used_at."
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
        responses={200: APIKeySerializer(many=True)},
        tags=["API Keys"],
        summary="List API keys.",
    )
    def get(self, request):
        # Fetch filtered/search/ordered queryset.
        keys = APIKeyService.list_keys(
            request.user,
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            keys,
            request,
        )

        # Convert queryset into JSON.
        serializer = APIKeySerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )

    # Swagger documentation for Generate API Key.
    @extend_schema(
        request=APIKeyBaseSerializer,
        responses={201: APIKeySerializer},
        tags=["API Keys"],
        summary="Generate a new API key.",
    )
    def post(self, request):
        # Verify developer role before serializer validation
        if request.user.role != User.Role.DEVELOPER:
            raise PermissionDenied(
                "Only developers can generate API keys."
            )

        # Validate request data.
        serializer = APIKeyBaseSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        # Generate new API key using service.
        api_key, plain_key = APIKeyService.create_key(
            request.user,
            serializer.validated_data,
        )

        # Return response containing plain key once and key metadata.
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

    # Swagger documentation for Retrieve API Key metadata.
    @extend_schema(
        responses={200: APIKeySerializer},
        tags=["API Keys"],
        summary="Retrieve API key details.",
    )
    def get(self, request, uuid):
        # Fetch API key by UUID.
        key = APIKeyService.get_key(uuid)

        # Check permission: Owner or Admin.
        if (
            request.user.role != User.Role.ADMIN
            and key.project.developer != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this API key."
            )

        # Convert model into JSON.
        serializer = APIKeySerializer(key)

        return success_response(
            data=serializer.data,
            message="API key details fetched successfully.",
        )

    # Swagger documentation for Rename API Key.
    @extend_schema(
        request=APIKeyUpdateSerializer,
        responses={200: APIKeySerializer},
        tags=["API Keys"],
        summary="Rename an API key (Owner only).",
    )
    def patch(self, request, uuid):
        # Fetch existing API key.
        key = APIKeyService.get_key(uuid)

        # Check permission: Owner only.
        if key.project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to modify this API key."
            )

        # Validate request data.
        serializer = APIKeyUpdateSerializer(
            key,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True,
        )

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
        responses={200: None},
        tags=["API Keys"],
        summary="Deactivate an API key (Owner only).",
    )
    def delete(self, request, uuid):
        # Fetch existing API key.
        key = APIKeyService.get_key(uuid)

        # Check permission: Owner only.
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
        request=None,
        responses={200: APIKeySerializer},
        tags=["API Keys"],
        summary="Regenerate an API key (Owner only).",
    )
    def post(self, request, uuid):
        # Fetch existing API key.
        key = APIKeyService.get_key(uuid)

        # Check permission: Owner only.
        if key.project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to regenerate this API key."
            )

        # Regenerate API key.
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

    # Swagger documentation for Protected Sample endpoint.
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="X-API-Key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="Developer API Key",
            ),
        ],
        responses={200: ProtectedSampleResponseSerializer},
        tags=["API Keys"],
        summary="Protected sample endpoint using API Key authentication.",
    )
    def get(self, request):
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

        return success_response(
            data=serializer.data,
            message="API Key authentication successful.",
        )

