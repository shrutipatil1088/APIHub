from django.urls import path

from .views import (
    DeveloperProjectListCreateAPIView,
    DeveloperProjectDetailAPIView,
)

urlpatterns = [
    # List all developer projects and create a new project.
    path(
        "projects/",
        DeveloperProjectListCreateAPIView.as_view(),
        name="developer-project-list-create",
    ),

    # Retrieve, update, or delete a specific developer project by UUID.
    path(
        "projects/<uuid:uuid>/",
        DeveloperProjectDetailAPIView.as_view(),
        name="developer-project-detail",
    ),
]
