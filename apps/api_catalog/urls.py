# use path() = to create URL routes.
from django.urls import path

from .views import (
    APIListCreateAPIView,
    APIDetailAPIView,
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
]