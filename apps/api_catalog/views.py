# Contains HTTP status codes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# Used only for Swagger documentation
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)

from .models import API

from apps.core.permissions import IsAdminRole
from apps.core.responses import success_response

from .serializers import (
    CreateAPISerializer,
    UpdateAPISerializer,
    APIListSerializer,
    APISerializer,
)
from .services import APIService

from apps.core.pagination import StandardResultsSetPagination


# ============================================================================
# API List & Create
# Handles:
# GET  -> List all APIs
# POST -> Create a new API
# ============================================================================
class APIListCreateAPIView(APIView):

    # Assign permissions based on request method.
    def get_permissions(self):
        if self.request.method == "POST":
            return [
                IsAuthenticated(),
                IsAdminRole(),
            ]

        return [
            IsAuthenticated(),
        ]
    
    # Swagger documentation for List API.
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter APIs by status.",
                enum=[
                    API.Status.DRAFT,
                    API.Status.PUBLISHED,
                ],
            ),

            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search APIs by name.",
            ),

            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter APIs by active status.",
            ),

            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Order results. "
                    "Available values: "
                    "name, -name, created_at, -created_at, "
                    "updated_at, -updated_at, status, -status."
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
        responses={200: APIListSerializer(many=True)},
        tags=["API Catalog"],
    )

    # GET  -> List all APIs
    def get(self, request):

        # Get filtered/search/ordered queryset.
        apis = APIService.list_apis(
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            apis,
            request,
        )

        # Convert queryset into JSON.
        serializer = APIListSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )

    # Swagger documentation for Create API.
    @extend_schema(
        request=CreateAPISerializer,
        responses={201: APISerializer},
        tags=["API Catalog"],
    )
    # POST -> Create a new API
    def post(self, request):
        # Validate request data.
        serializer = CreateAPISerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        # Create new API.
        api = APIService.create_api(
            serializer.validated_data,
            request.user,
        )


        # Return created object.
        return success_response(
            data=APISerializer(api).data,
            message="API created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# API Detail
# Handles:
# GET    -> Retrieve API
# PUT    -> Full Update
# PATCH  -> Partial Update
# DELETE -> Soft Delete
# ============================================================================
class APIDetailAPIView(APIView):

    # Assign permissions based on request method.
    def get_permissions(self):
        if self.request.method in (
            "PUT",
            "PATCH",
            "DELETE",
        ):
            return [
                IsAuthenticated(),
                IsAdminRole(),
            ]

        return [
            IsAuthenticated(),
        ]

    # Swagger documentation for Retrieve API.
    @extend_schema(
        responses={200: APISerializer},
        tags=["API Catalog"],
    )

    #1. Detail API
    def get(self, request, uuid):

        # Fetch API by UUID.
        api = APIService.get_api(uuid)

        # Convert model into JSON.
        serializer = APISerializer(api)

        return success_response(
            data=serializer.data,
            message="API fetched successfully.",
        )

    # Swagger documentation for Full Update.
    @extend_schema(
        request=UpdateAPISerializer,
        responses={200: APISerializer},
        tags=["API Catalog"],
    )

    #1. Update API
    def put(self, request, uuid):

        # Fetch existing API.
        api = APIService.get_api(uuid)

        # Validate complete request data.
        serializer = UpdateAPISerializer(
            api,
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        api = APIService.update_api(
            api,
            serializer.validated_data,
        )

        return success_response(
            data=APISerializer(api).data,
            message="API updated successfully.",
        )


    # Swagger documentation for Partial Update.
    @extend_schema(
        request=UpdateAPISerializer,
        responses={200: APISerializer},
        tags=["API Catalog"],
    )
    # 3. Partial Update API
    def patch(self, request, uuid):

        # Fetch existing API.
        api = APIService.get_api(uuid)

        # Validate only provided fields.
        serializer = UpdateAPISerializer(
            api,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        api = APIService.update_api(
            api,
            serializer.validated_data,
        )

        return success_response(
            data=APISerializer(api).data,
            message="API updated successfully.",
        )

    # Swagger documentation for Delete API.
    @extend_schema(
        responses={200: None},
        tags=["API Catalog"],
    )
    # 4. Delete API
    def delete(self, request, uuid):

        # Fetch existing API.
        api = APIService.get_api(uuid)

        APIService.delete_api(api)

        return success_response(
            message="API deleted successfully.",
        )