from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)

from apps.accounts.models import User
from apps.core.responses import success_response
from apps.core.pagination import StandardResultsSetPagination

from .serializers import (
    DeveloperProjectBaseSerializer,
    DeveloperProjectSerializer,
)
from .services import DeveloperProjectService


# ============================================================================
# DeveloperProject List & Create
# Handles:
# GET  -> List all projects (Owner-filtered for Developers, all for Admins)
# POST -> Create a new project (Developer only)
# ============================================================================
class DeveloperProjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for List Developer Projects.
    @extend_schema(
        summary="List Developer Projects",
        description="""
Returns a paginated list of developer projects.

Permissions:
- Admin: View all projects.
- Developer: View only their own projects.

Supports:
- Search (by name, description)
- Filtering
- Ordering (by name, created_at, updated_at)
- Pagination
""",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search projects by name or description.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Order results by field (e.g., name, -name, created_at).",
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
        responses={200: DeveloperProjectSerializer(many=True)},
        tags=["Developer Projects"],
    )
    def get(self, request):
        projects = DeveloperProjectService.list_projects(
            request.user,
            request.query_params,
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(projects, request)
        serializer = DeveloperProjectSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Swagger documentation for Create Developer Project.
    @extend_schema(
        summary="Create Developer Project",
        description="""
Creates a new developer project for the authenticated developer user.

Permissions:
- Developer role only

Validation rules:
- Requires a valid project name and description.
- Developer cannot duplicate active project names.
""",
        request=DeveloperProjectBaseSerializer,
        responses={201: DeveloperProjectSerializer},
        tags=["Developer Projects"],
    )
    def post(self, request):
        serializer = DeveloperProjectBaseSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        project = DeveloperProjectService.create_project(
            request.user,
            serializer.validated_data,
        )
        return success_response(
            data=DeveloperProjectSerializer(project).data,
            message="Developer project created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# DeveloperProject Detail
# Handles:
# GET    -> Retrieve project (Owner or Admin)
# PUT    -> Full Update project (Owner only)
# PATCH  -> Partial Update project (Owner only)
# DELETE -> Soft Delete project (Owner only)
# ============================================================================
class DeveloperProjectDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for Retrieve Developer Project Details.
    @extend_schema(
        summary="Retrieve Developer Project Details",
        description="""
Retrieves details for a specific developer project by UUID.

Permissions:
- Admin: View any project.
- Developer: View only their own project.
""",
        responses={200: DeveloperProjectSerializer},
        tags=["Developer Projects"],
    )
    def get(self, request, uuid):
        project = DeveloperProjectService.get_project(uuid)
        if (
            request.user.role != User.Role.ADMIN
            and project.developer != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this project."
            )
        serializer = DeveloperProjectSerializer(project)
        return success_response(
            data=serializer.data,
            message="Developer project details fetched successfully.",
        )

    # Swagger documentation for Fully Update Developer Project.
    @extend_schema(
        summary="Fully Update Developer Project",
        description="""
Fully updates all fields of a developer project by UUID.

Permissions:
- Project Owner only
""",
        request=DeveloperProjectBaseSerializer,
        responses={200: DeveloperProjectSerializer},
        tags=["Developer Projects"],
    )
    def put(self, request, uuid):
        project = DeveloperProjectService.get_project(uuid)
        if project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to modify this project."
            )
        serializer = DeveloperProjectBaseSerializer(
            project,
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        project = DeveloperProjectService.update_project(
            project,
            serializer.validated_data,
        )
        return success_response(
            data=DeveloperProjectSerializer(project).data,
            message="Developer project updated successfully.",
        )

    # Swagger documentation for Partially Update Developer Project.
    @extend_schema(
        summary="Partially Update Developer Project",
        description="""
Partially updates specific fields of a developer project by UUID.

Permissions:
- Project Owner only
""",
        request=DeveloperProjectBaseSerializer,
        responses={200: DeveloperProjectSerializer},
        tags=["Developer Projects"],
    )
    def patch(self, request, uuid):
        project = DeveloperProjectService.get_project(uuid)
        if project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to modify this project."
            )
        serializer = DeveloperProjectBaseSerializer(
            project,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        project = DeveloperProjectService.update_project(
            project,
            serializer.validated_data,
        )
        return success_response(
            data=DeveloperProjectSerializer(project).data,
            message="Developer project updated successfully.",
        )

    # Swagger documentation for Delete Developer Project.
    @extend_schema(
        summary="Delete Developer Project",
        description="""
Soft-deletes a developer project by UUID.

Permissions:
- Project Owner only
""",
        responses={200: None},
        tags=["Developer Projects"],
    )
    def delete(self, request, uuid):
        project = DeveloperProjectService.get_project(uuid)
        if project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to delete this project."
            )
        DeveloperProjectService.delete_project(project)
        return success_response(
            message="Developer project deleted successfully.",
        )
