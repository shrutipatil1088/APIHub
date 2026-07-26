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

    # Swagger documentation for List APIs.
    @extend_schema(
        summary="List APIs",
        description="""
Returns a paginated list of all APIs in the catalog.

Permissions:
- Authenticated Users

Supports:
- Search (by API name)
- Filtering (by status, active flag)
- Ordering (by name, created_at, updated_at, status)
- Pagination
""",
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter APIs by status (DRAFT, PUBLISHED).",
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
                description="Order results by field (e.g., name, -name, created_at, -created_at).",
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
    def get(self, request):
        apis = APIService.list_apis(request.query_params)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(apis, request)
        serializer = APIListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Swagger documentation for Create API.
    @extend_schema(
        summary="Create API",
        description="""
Creates a new API in the catalog.

Permissions:
- Admin Users only

Validation rules:
- Unique API name required.
- Base path must be valid.
""",
        request=CreateAPISerializer,
        responses={201: APISerializer},
        tags=["API Catalog"],
    )
    def post(self, request):
        serializer = CreateAPISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api = APIService.create_api(serializer.validated_data, request.user)
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

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [
                IsAuthenticated(),
                IsAdminRole(),
            ]

        return [
            IsAuthenticated(),
        ]

    # Swagger documentation for Retrieve API Details.
    @extend_schema(
        summary="Retrieve API Details",
        description="""
Retrieves details for a specific API by UUID.

Permissions:
- Authenticated Users
""",
        responses={200: APISerializer},
        tags=["API Catalog"],
    )
    def get(self, request, uuid):
        api = APIService.get_api(uuid)
        serializer = APISerializer(api)
        return success_response(
            data=serializer.data,
            message="API fetched successfully.",
        )

    # Swagger documentation for Fully Update API.
    @extend_schema(
        summary="Fully Update API",
        description="""
Fully updates all fields of an existing API by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateAPISerializer,
        responses={200: APISerializer},
        tags=["API Catalog"],
    )
    def put(self, request, uuid):
        api = APIService.get_api(uuid)
        serializer = UpdateAPISerializer(api, data=request.data)
        serializer.is_valid(raise_exception=True)
        api = APIService.update_api(api, serializer.validated_data)
        return success_response(
            data=APISerializer(api).data,
            message="API updated successfully.",
        )

    # Swagger documentation for Partially Update API.
    @extend_schema(
        summary="Partially Update API",
        description="""
Partially updates specific fields of an existing API by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateAPISerializer,
        responses={200: APISerializer},
        tags=["API Catalog"],
    )
    def patch(self, request, uuid):
        api = APIService.get_api(uuid)
        serializer = UpdateAPISerializer(api, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        api = APIService.update_api(api, serializer.validated_data)
        return success_response(
            data=APISerializer(api).data,
            message="API updated successfully.",
        )

    # Swagger documentation for Delete API.
    @extend_schema(
        summary="Delete API",
        description="""
Soft-deletes an existing API by UUID.

Permissions:
- Admin Users only
""",
        responses={200: None},
        tags=["API Catalog"],
    )
    def delete(self, request, uuid):
        api = APIService.get_api(uuid)
        APIService.delete_api(api)
        return success_response(message="API deleted successfully.")


# ============================================================================
# API Version List & Create
# Handles:
# GET  -> List all versions for a specific API
# POST -> Create a new version for a specific API
# ============================================================================
class APIVersionListCreateAPIView(APIView):

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
        summary="List API Versions",
        description="""
Returns a paginated list of versions for a specific API.

Permissions:
- Authenticated Users

Supports:
- Search (by version string)
- Filtering (by is_latest, is_active)
- Ordering (by version, created_at, updated_at)
- Pagination
""",
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
                description="Order results by field (e.g., version, -version).",
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
    def get(self, request, api_uuid):
        versions = APIVersionService.list_versions(api_uuid, request.query_params)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(versions, request)
        serializer = APIVersionListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Swagger documentation for Create API Version.
    @extend_schema(
        summary="Create API Version",
        description="""
Creates a new version for a specific API.

Permissions:
- Admin Users only
""",
        request=CreateAPIVersionSerializer,
        responses={201: APIVersionSerializer},
        tags=["API Versions"],
    )
    def post(self, request, api_uuid):
        api = APIService.get_api(api_uuid)
        serializer = CreateAPIVersionSerializer(
            data=request.data,
            context={"view": self},
        )
        serializer.is_valid(raise_exception=True)
        version = APIVersionService.create_version(api, serializer.validated_data)
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

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [
                IsAuthenticated(),
                IsAdminRole(),
            ]

        return [
            IsAuthenticated(),
        ]

    # Swagger documentation for Retrieve API Version Details.
    @extend_schema(
        summary="Retrieve API Version Details",
        description="""
Retrieves details for a specific API version by UUID.

Permissions:
- Authenticated Users
""",
        responses={200: APIVersionSerializer},
        tags=["API Versions"],
    )
    def get(self, request, uuid):
        version = APIVersionService.get_version(uuid)
        serializer = APIVersionSerializer(version)
        return success_response(
            data=serializer.data,
            message="API Version fetched successfully.",
        )

    # Swagger documentation for Fully Update API Version.
    @extend_schema(
        summary="Fully Update API Version",
        description="""
Fully updates all fields of an API version by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateAPIVersionSerializer,
        responses={200: APIVersionSerializer},
        tags=["API Versions"],
    )
    def put(self, request, uuid):
        version = APIVersionService.get_version(uuid)
        serializer = UpdateAPIVersionSerializer(
            version,
            data=request.data,
            context={"view": self},
        )
        serializer.is_valid(raise_exception=True)
        version = APIVersionService.update_version(version, serializer.validated_data)
        return success_response(
            data=APIVersionSerializer(version).data,
            message="API Version updated successfully.",
        )

    # Swagger documentation for Partially Update API Version.
    @extend_schema(
        summary="Partially Update API Version",
        description="""
Partially updates specific fields of an API version by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateAPIVersionSerializer,
        responses={200: APIVersionSerializer},
        tags=["API Versions"],
    )
    def patch(self, request, uuid):
        version = APIVersionService.get_version(uuid)
        serializer = UpdateAPIVersionSerializer(
            version,
            data=request.data,
            partial=True,
            context={"view": self},
        )
        serializer.is_valid(raise_exception=True)
        version = APIVersionService.update_version(version, serializer.validated_data)
        return success_response(
            data=APIVersionSerializer(version).data,
            message="API Version updated successfully.",
        )

    # Swagger documentation for Delete API Version.
    @extend_schema(
        summary="Delete API Version",
        description="""
Soft-deletes an API version by UUID.

Permissions:
- Admin Users only
""",
        responses={200: None},
        tags=["API Versions"],
    )
    def delete(self, request, uuid):
        version = APIVersionService.get_version(uuid)
        APIVersionService.delete_version(version)
        return success_response(message="API Version deleted successfully.")


# ============================================================================
# API Endpoint List & Create
# Handles:
# GET  -> List all endpoints for a specific API version
# POST -> Create a new endpoint for a specific API version
# ============================================================================
class EndpointListCreateAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [
                IsAuthenticated(),
                IsAdminRole(),
            ]

        return [
            IsAuthenticated(),
        ]

    # Swagger documentation for List API Endpoints.
    @extend_schema(
        summary="List API Endpoints",
        description="""
Returns a paginated list of endpoints for a specific API version.

Permissions:
- Authenticated Users

Supports:
- Search (by path or summary)
- Filtering (by method, is_active)
- Ordering (by path, method, created_at, updated_at)
- Pagination
""",
        parameters=[
            OpenApiParameter(
                name="method",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by HTTP method (GET, POST, PUT, PATCH, DELETE).",
                enum=Endpoint.Method.values,
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
                description="Order results by field (e.g., path, -path, method).",
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
    def get(self, request, version_uuid):
        endpoints = EndpointService.list_endpoints(version_uuid, request.query_params)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(endpoints, request)
        serializer = EndpointListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Swagger documentation for Create API Endpoint.
    @extend_schema(
        summary="Create API Endpoint",
        description="""
Creates a new endpoint for a specific API version.

Permissions:
- Admin Users only
""",
        request=CreateEndpointSerializer,
        responses={201: EndpointSerializer},
        tags=["API Endpoints"],
    )
    def post(self, request, version_uuid):
        version = APIVersionService.get_version(version_uuid)
        serializer = CreateEndpointSerializer(
            data=request.data,
            context={"view": self},
        )
        serializer.is_valid(raise_exception=True)
        endpoint = EndpointService.create_endpoint(version, serializer.validated_data)
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

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [
                IsAuthenticated(),
                IsAdminRole(),
            ]

        return [
            IsAuthenticated(),
        ]

    # Swagger documentation for Retrieve API Endpoint Details.
    @extend_schema(
        summary="Retrieve API Endpoint Details",
        description="""
Retrieves details for a specific API endpoint by UUID.

Permissions:
- Authenticated Users
""",
        responses={200: EndpointSerializer},
        tags=["API Endpoints"],
    )
    def get(self, request, uuid):
        endpoint = EndpointService.get_endpoint(uuid)
        serializer = EndpointSerializer(endpoint)
        return success_response(
            data=serializer.data,
            message="Endpoint fetched successfully.",
        )

    # Swagger documentation for Fully Update API Endpoint.
    @extend_schema(
        summary="Fully Update API Endpoint",
        description="""
Fully updates all fields of an API endpoint by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateEndpointSerializer,
        responses={200: EndpointSerializer},
        tags=["API Endpoints"],
    )
    def put(self, request, uuid):
        endpoint = EndpointService.get_endpoint(uuid)
        serializer = UpdateEndpointSerializer(
            endpoint,
            data=request.data,
            context={"view": self},
        )
        serializer.is_valid(raise_exception=True)
        endpoint = EndpointService.update_endpoint(endpoint, serializer.validated_data)
        return success_response(
            data=EndpointSerializer(endpoint).data,
            message="Endpoint updated successfully.",
        )

    # Swagger documentation for Partially Update API Endpoint.
    @extend_schema(
        summary="Partially Update API Endpoint",
        description="""
Partially updates specific fields of an API endpoint by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateEndpointSerializer,
        responses={200: EndpointSerializer},
        tags=["API Endpoints"],
    )
    def patch(self, request, uuid):
        endpoint = EndpointService.get_endpoint(uuid)
        serializer = UpdateEndpointSerializer(
            endpoint,
            data=request.data,
            partial=True,
            context={"view": self},
        )
        serializer.is_valid(raise_exception=True)
        endpoint = EndpointService.update_endpoint(endpoint, serializer.validated_data)
        return success_response(
            data=EndpointSerializer(endpoint).data,
            message="Endpoint updated successfully.",
        )

    # Swagger documentation for Delete API Endpoint.
    @extend_schema(
        summary="Delete API Endpoint",
        description="""
Soft-deletes an API endpoint by UUID.

Permissions:
- Admin Users only
""",
        responses={200: None},
        tags=["API Endpoints"],
    )
    def delete(self, request, uuid):
        endpoint = EndpointService.get_endpoint(uuid)
        EndpointService.delete_endpoint(endpoint)
        return success_response(message="Endpoint deleted successfully.")


# ============================================================================
# API Documentation
# Handles:
# GET -> Retrieve complete API documentation including versions and endpoints.
# ============================================================================
class APIDocumentationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Retrieve API Documentation.
    @extend_schema(
        summary="Retrieve API Documentation",
        description="""
Retrieves complete aggregated API documentation including nested versions and endpoint specifications.

Permissions:
- Authenticated Users
""",
        responses={200: APIDocumentationSerializer},
        tags=["API Documentation"],
    )
    def get(self, request, api_uuid):
        api = APIService.get_api_documentation(api_uuid)
        serializer = APIDocumentationSerializer(api)
        return success_response(
            data=serializer.data,
            message="API documentation fetched successfully.",
        )