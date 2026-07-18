# use path() = to create URL routes.
from django.urls import path

from .views import (
    APIListCreateAPIView,
    APIDetailAPIView,
    APIVersionListCreateAPIView,
    APIVersionDetailAPIView,
    EndpointListCreateAPIView,
    EndpointDetailAPIView,
    APIDocumentationAPIView,
)

urlpatterns = [

    # List all APIs and create a new API.
    path(
        "",
        APIListCreateAPIView.as_view(),
        name="api-list-create",
    ),

    # Retrieve, update, or delete a specific API by UUID.
    path(
        "<uuid:uuid>/",
        APIDetailAPIView.as_view(),
        name="api-detail",
    ),

    # List all versions for a specific API and create a new version.
    path(
        "<uuid:api_uuid>/versions/",
        APIVersionListCreateAPIView.as_view(),
        name="api-version-list-create",
    ),

    # Retrieve complete API documentation including versions and endpoints.
    path(
        "<uuid:api_uuid>/documentation/",
        APIDocumentationAPIView.as_view(),
        name="api-documentation",
    ),

    # Retrieve, update, or delete a specific version by UUID.
    path(
        "versions/<uuid:uuid>/",
        APIVersionDetailAPIView.as_view(),
        name="api-version-detail",
    ),

    # List all endpoints for a specific API version and create a new endpoint.
    path(
        "versions/<uuid:version_uuid>/endpoints/",
        EndpointListCreateAPIView.as_view(),
        name="endpoint-list-create",
    ),

    # Retrieve, update, or delete a specific endpoint by UUID.
    path(
        "endpoints/<uuid:uuid>/",
        EndpointDetailAPIView.as_view(),
        name="endpoint-detail",
    ),
]