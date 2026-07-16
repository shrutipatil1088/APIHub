# use path() = to create URL routes.
from django.urls import path

from .views import (
    APIListCreateAPIView,
    APIDetailAPIView,
    APIVersionListCreateAPIView,
    APIVersionDetailAPIView,
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

    # Retrieve, update, or delete a specific version by UUID.
    path(
        "versions/<uuid:uuid>/",
        APIVersionDetailAPIView.as_view(),
        name="api-version-detail",
    ),
]