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

    # Swagger documentation for List Projects.
    @extend_schema(
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
                description=(
                    "Order results. "
                    "Available values: "
                    "name, -name, created_at, -created_at, updated_at, -updated_at."
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
        responses={200: DeveloperProjectSerializer(many=True)},
        tags=["Developer Projects"],
        summary="List developer projects.",
    )
    def get(self, request):
        # Fetch filtered/search/ordered queryset.
        projects = DeveloperProjectService.list_projects(
            request.user,
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            projects,
            request,
        )

        # Convert queryset into JSON.
        serializer = DeveloperProjectSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )

    # Swagger documentation for Create Project.
    @extend_schema(
        request=DeveloperProjectBaseSerializer,
        responses={201: DeveloperProjectSerializer},
        tags=["Developer Projects"],
        summary="Create a new developer project.",
    )
    def post(self, request):
        # Validate request data.
        serializer = DeveloperProjectBaseSerializer(
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        # Create new project.
        project = DeveloperProjectService.create_project(
            request.user,
            serializer.validated_data,
        )

        # Return created object.
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

    # Swagger documentation for Retrieve Project.
    @extend_schema(
        responses={200: DeveloperProjectSerializer},
        tags=["Developer Projects"],
        summary="Retrieve developer project details.",
    )
    def get(self, request, uuid):
        # Fetch project by UUID.
        project = DeveloperProjectService.get_project(uuid)

        # Check permission: Owner or Admin.
        if (
            request.user.role != User.Role.ADMIN
            and project.developer != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this project."
            )

        # Convert model into JSON.
        serializer = DeveloperProjectSerializer(project)

        return success_response(
            data=serializer.data,
            message="Developer project details fetched successfully.",
        )

    # Swagger documentation for Full Update.
    @extend_schema(
        request=DeveloperProjectBaseSerializer,
        responses={200: DeveloperProjectSerializer},
        tags=["Developer Projects"],
        summary="Fully update a developer project (Owner only).",
    )
    def put(self, request, uuid):
        # Fetch existing project.
        project = DeveloperProjectService.get_project(uuid)

        # Check permission: Owner only.
        if project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to modify this project."
            )

        # Validate request data.
        serializer = DeveloperProjectBaseSerializer(
            project,
            data=request.data,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        project = DeveloperProjectService.update_project(
            project,
            serializer.validated_data,
        )

        return success_response(
            data=DeveloperProjectSerializer(project).data,
            message="Developer project updated successfully.",
        )

    # Swagger documentation for Partial Update.
    @extend_schema(
        request=DeveloperProjectBaseSerializer,
        responses={200: DeveloperProjectSerializer},
        tags=["Developer Projects"],
        summary="Partially update a developer project (Owner only).",
    )
    def patch(self, request, uuid):
        # Fetch existing project.
        project = DeveloperProjectService.get_project(uuid)

        # Check permission: Owner only.
        if project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to modify this project."
            )

        # Validate request data.
        serializer = DeveloperProjectBaseSerializer(
            project,
            data=request.data,
            partial=True,
            context={"request": request},
        )

        serializer.is_valid(
            raise_exception=True,
        )

        project = DeveloperProjectService.update_project(
            project,
            serializer.validated_data,
        )

        return success_response(
            data=DeveloperProjectSerializer(project).data,
            message="Developer project updated successfully.",
        )

    # Swagger documentation for Delete Project.
    @extend_schema(
        responses={200: None},
        tags=["Developer Projects"],
        summary="Delete a developer project (Owner only).",
    )
    def delete(self, request, uuid):
        # Fetch existing project.
        project = DeveloperProjectService.get_project(uuid)

        # Check permission: Owner only.
        if project.developer != request.user:
            raise PermissionDenied(
                "You do not have permission to delete this project."
            )

        DeveloperProjectService.delete_project(project)

        return success_response(
            message="Developer project deleted successfully.",
        )
