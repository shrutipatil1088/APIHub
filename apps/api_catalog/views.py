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

from .models import API, APIVersion, Endpoint

from apps.core.permissions import IsAdminRole
from apps.core.responses import success_response

from .serializers import (
    CreateAPISerializer,
    UpdateAPISerializer,
    APIListSerializer,
    APISerializer,
    CreateAPIVersionSerializer,
    UpdateAPIVersionSerializer,
    APIVersionListSerializer,
    APIVersionSerializer,
    CreateEndpointSerializer,
    UpdateEndpointSerializer,
    EndpointListSerializer,
    EndpointSerializer,
    APIDocumentationSerializer,
)
from .services import APIService, APIVersionService, EndpointService

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


# ============================================================================
# API Version List & Create
# Handles:
# GET  -> List all versions for a specific API
# POST -> Create a new version for a specific API
# ============================================================================
class APIVersionListCreateAPIView(APIView):

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

    # Swagger documentation for List API Versions.
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="is_latest",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by latest version.",
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by active status.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search versions by version string.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Order results. "
                    "Available values: "
                    "version, -version, created_at, -created_at, "
                    "updated_at, -updated_at, is_latest, -is_latest."
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
        responses={200: APIVersionListSerializer(many=True)},
        tags=["API Versions"],
    )
    # GET  -> List all versions for a specific API
    def get(self, request, api_uuid):
        # Get filtered/search/ordered queryset.
        versions = APIVersionService.list_versions(
            api_uuid,
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            versions,
            request,
        )

        # Convert queryset into JSON.
        serializer = APIVersionListSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )

    # Swagger documentation for Create API Version.
    @extend_schema(
        request=CreateAPIVersionSerializer,
        responses={201: APIVersionSerializer},
        tags=["API Versions"],
    )
    # POST -> Create a new version for a specific API
    def post(self, request, api_uuid):
        # Fetch parent API to assert existence.
        api = APIService.get_api(api_uuid)

        # Validate request data.
        serializer = CreateAPIVersionSerializer(
            data=request.data,
            context={"view": self},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        # Create new API Version.
        version = APIVersionService.create_version(
            api,
            serializer.validated_data,
        )

        # Return created object.
        return success_response(
            data=APIVersionSerializer(version).data,
            message="API Version created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# API Version Detail
# Handles:
# GET    -> Retrieve API Version
# PUT    -> Full Update API Version
# PATCH  -> Partial Update API Version
# DELETE -> Soft Delete API Version
# ============================================================================
class APIVersionDetailAPIView(APIView):

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

    # Swagger documentation for Retrieve API Version.
    @extend_schema(
        responses={200: APIVersionSerializer},
        tags=["API Versions"],
    )
    # 1. Detail API Version
    def get(self, request, uuid):
        # Fetch API Version by UUID.
        version = APIVersionService.get_version(uuid)

        # Convert model into JSON.
        serializer = APIVersionSerializer(version)

        return success_response(
            data=serializer.data,
            message="API Version fetched successfully.",
        )

    # Swagger documentation for Full Update.
    @extend_schema(
        request=UpdateAPIVersionSerializer,
        responses={200: APIVersionSerializer},
        tags=["API Versions"],
    )
    # 2. Update API Version
    def put(self, request, uuid):
        # Fetch existing API Version.
        version = APIVersionService.get_version(uuid)

        # Validate complete request data.
        serializer = UpdateAPIVersionSerializer(
            version,
            data=request.data,
            context={"view": self},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        version = APIVersionService.update_version(
            version,
            serializer.validated_data,
        )

        return success_response(
            data=APIVersionSerializer(version).data,
            message="API Version updated successfully.",
        )

    # Swagger documentation for Partial Update.
    @extend_schema(
        request=UpdateAPIVersionSerializer,
        responses={200: APIVersionSerializer},
        tags=["API Versions"],
    )
    # 3. Partial Update API Version
    def patch(self, request, uuid):
        # Fetch existing API Version.
        version = APIVersionService.get_version(uuid)

        # Validate only provided fields.
        serializer = UpdateAPIVersionSerializer(
            version,
            data=request.data,
            partial=True,
            context={"view": self},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        version = APIVersionService.update_version(
            version,
            serializer.validated_data,
        )

        return success_response(
            data=APIVersionSerializer(version).data,
            message="API Version updated successfully.",
        )

    # Swagger documentation for Delete API Version.
    @extend_schema(
        responses={200: None},
        tags=["API Versions"],
    )
    # 4. Delete API Version
    def delete(self, request, uuid):
        # Fetch existing API Version.
        version = APIVersionService.get_version(uuid)

        APIVersionService.delete_version(version)

        return success_response(
            message="API Version deleted successfully.",
        )


# ============================================================================
# API Endpoint List & Create
# Handles:
# GET  -> List all endpoints for a specific API version
# POST -> Create a new endpoint for a specific API version
# ============================================================================
class EndpointListCreateAPIView(APIView):

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

    # Swagger documentation for List Endpoints.
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="method",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by HTTP method.",
                enum=Endpoint.Method.choices,
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by active status.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search endpoints by path or summary.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Order results. "
                    "Available values: "
                    "path, -path, method, -method, created_at, -created_at, updated_at, -updated_at."
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
        responses={200: EndpointListSerializer(many=True)},
        tags=["API Endpoints"],
    )
    # GET  -> List all endpoints for a specific API version
    def get(self, request, version_uuid):
        # Get filtered/search/ordered queryset.
        endpoints = EndpointService.list_endpoints(
            version_uuid,
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            endpoints,
            request,
        )

        # Convert queryset into JSON.
        serializer = EndpointListSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )

    # Swagger documentation for Create Endpoint.
    @extend_schema(
        request=CreateEndpointSerializer,
        responses={201: EndpointSerializer},
        tags=["API Endpoints"],
    )
    # POST -> Create a new endpoint for a specific API version
    def post(self, request, version_uuid):
        # Fetch parent version to assert existence.
        version = APIVersionService.get_version(version_uuid)

        # Validate request data.
        serializer = CreateEndpointSerializer(
            data=request.data,
            context={"view": self},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        # Create new Endpoint.
        endpoint = EndpointService.create_endpoint(
            version,
            serializer.validated_data,
        )

        # Return created object.
        return success_response(
            data=EndpointSerializer(endpoint).data,
            message="Endpoint created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# API Endpoint Detail
# Handles:
# GET    -> Retrieve Endpoint
# PUT    -> Full Update Endpoint
# PATCH  -> Partial Update Endpoint
# DELETE -> Soft Delete Endpoint
# ============================================================================
class EndpointDetailAPIView(APIView):

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

    # Swagger documentation for Retrieve Endpoint.
    @extend_schema(
        responses={200: EndpointSerializer},
        tags=["API Endpoints"],
    )
    # 1. Detail Endpoint
    def get(self, request, uuid):
        # Fetch Endpoint by UUID.
        endpoint = EndpointService.get_endpoint(uuid)

        # Convert model into JSON.
        serializer = EndpointSerializer(endpoint)

        return success_response(
            data=serializer.data,
            message="Endpoint fetched successfully.",
        )

    # Swagger documentation for Full Update.
    @extend_schema(
        request=UpdateEndpointSerializer,
        responses={200: EndpointSerializer},
        tags=["API Endpoints"],
    )
    # 2. Update Endpoint
    def put(self, request, uuid):
        # Fetch existing Endpoint.
        endpoint = EndpointService.get_endpoint(uuid)

        # Validate complete request data.
        serializer = UpdateEndpointSerializer(
            endpoint,
            data=request.data,
            context={"view": self},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        endpoint = EndpointService.update_endpoint(
            endpoint,
            serializer.validated_data,
        )

        return success_response(
            data=EndpointSerializer(endpoint).data,
            message="Endpoint updated successfully.",
        )

    # Swagger documentation for Partial Update.
    @extend_schema(
        request=UpdateEndpointSerializer,
        responses={200: EndpointSerializer},
        tags=["API Endpoints"],
    )
    # 3. Partial Update Endpoint
    def patch(self, request, uuid):
        # Fetch existing Endpoint.
        endpoint = EndpointService.get_endpoint(uuid)

        # Validate only provided fields.
        serializer = UpdateEndpointSerializer(
            endpoint,
            data=request.data,
            partial=True,
            context={"view": self},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        endpoint = EndpointService.update_endpoint(
            endpoint,
            serializer.validated_data,
        )

        return success_response(
            data=EndpointSerializer(endpoint).data,
            message="Endpoint updated successfully.",
        )

    # Swagger documentation for Delete Endpoint.
    @extend_schema(
        responses={200: None},
        tags=["API Endpoints"],
    )
    # 4. Delete Endpoint
    def delete(self, request, uuid):
        # Fetch existing Endpoint.
        endpoint = EndpointService.get_endpoint(uuid)

        EndpointService.delete_endpoint(endpoint)

        return success_response(
            message="Endpoint deleted successfully.",
        )


# ============================================================================
# API Documentation
# Handles:
# GET -> Retrieve complete API documentation including versions and endpoints.
# ============================================================================
class APIDocumentationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Retrieve API Documentation.
    @extend_schema(
        responses={200: APIDocumentationSerializer},
        tags=["API Documentation"],
        summary="Retrieve complete API documentation including versions and endpoints.",
    )
    def get(self, request, api_uuid):
        api = APIService.get_api_documentation(api_uuid)

        # Convert nested structure to JSON.
        serializer = APIDocumentationSerializer(api)

        return success_response(
            data=serializer.data,
            message="API documentation fetched successfully.",
        )