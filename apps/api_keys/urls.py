from django.urls import path

from .views import (
    APIKeyListCreateAPIView,
    APIKeyDetailAPIView,
    APIKeyRegenerateAPIView,
    ProtectedSampleAPIView,
)

urlpatterns = [
    # List all API keys and generate a new API key.
    path(
        "api-keys/",
        APIKeyListCreateAPIView.as_view(),
        name="api-key-list-create",
    ),

    # Protected sample endpoint using API Key authentication.
    path(
        "api-keys/protected-sample/",
        ProtectedSampleAPIView.as_view(),
        name="api-key-protected-sample",
    ),

    # Retrieve, rename, or deactivate a specific API key by UUID.
    path(
        "api-keys/<uuid:uuid>/",
        APIKeyDetailAPIView.as_view(),
        name="api-key-detail",
    ),

    # Regenerate a specific API key by UUID.
    path(
        "api-keys/<uuid:uuid>/regenerate/",
        APIKeyRegenerateAPIView.as_view(),
        name="api-key-regenerate",
    ),
]
