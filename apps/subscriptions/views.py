from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)

from apps.core.permissions import IsAdminRole
from apps.core.responses import success_response
from apps.core.pagination import StandardResultsSetPagination

from .models import SubscriptionPlan
from .serializers import (
    CreateSubscriptionPlanSerializer,
    UpdateSubscriptionPlanSerializer,
    SubscriptionPlanListSerializer,
    SubscriptionPlanSerializer,
)
from .services import SubscriptionPlanService


# ============================================================================
# SubscriptionPlan List & Create
# Handles:
# GET  -> List all plans
# POST -> Create a new plan
# ============================================================================
class SubscriptionPlanListCreateAPIView(APIView):

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

    # Swagger documentation for List Subscription Plans.
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="billing_cycle",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter plans by billing cycle.",
                enum=SubscriptionPlan.BillingCycle.values,
            ),
            OpenApiParameter(
                name="is_active",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter plans by active status.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search plans by name.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Order results. "
                    "Available values: "
                    "name, -name, price, -price, created_at, -created_at, updated_at, -updated_at."
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
        responses={200: SubscriptionPlanListSerializer(many=True)},
        tags=["Subscription Plans"],
        summary="List all subscription plans.",
    )
    def get(self, request):
        # Get filtered/search/ordered queryset.
        plans = SubscriptionPlanService.list_plans(
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            plans,
            request,
        )

        # Convert queryset into JSON.
        serializer = SubscriptionPlanListSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )

    # Swagger documentation for Create Subscription Plan.
    @extend_schema(
        request=CreateSubscriptionPlanSerializer,
        responses={201: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
        summary="Create a new subscription plan.",
    )
    def post(self, request):
        # Validate request data.
        serializer = CreateSubscriptionPlanSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        # Create new subscription plan.
        plan = SubscriptionPlanService.create_plan(
            serializer.validated_data,
        )

        # Return created object.
        return success_response(
            data=SubscriptionPlanSerializer(plan).data,
            message="Subscription plan created successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# SubscriptionPlan Detail
# Handles:
# GET    -> Retrieve plan
# PUT    -> Full Update plan
# PATCH  -> Partial Update plan
# DELETE -> Soft Delete plan
# ============================================================================
class SubscriptionPlanDetailAPIView(APIView):

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

    # Swagger documentation for Retrieve Subscription Plan.
    @extend_schema(
        responses={200: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
        summary="Retrieve a subscription plan details.",
    )
    def get(self, request, uuid):
        # Fetch plan by UUID.
        plan = SubscriptionPlanService.get_plan(uuid)

        # Convert model into JSON.
        serializer = SubscriptionPlanSerializer(plan)

        return success_response(
            data=serializer.data,
            message="Subscription plan fetched successfully.",
        )

    # Swagger documentation for Full Update.
    @extend_schema(
        request=UpdateSubscriptionPlanSerializer,
        responses={200: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
        summary="Fully update a subscription plan.",
    )
    def put(self, request, uuid):
        # Fetch existing plan.
        plan = SubscriptionPlanService.get_plan(uuid)

        # Validate complete request data.
        serializer = UpdateSubscriptionPlanSerializer(
            plan,
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        plan = SubscriptionPlanService.update_plan(
            plan,
            serializer.validated_data,
        )

        return success_response(
            data=SubscriptionPlanSerializer(plan).data,
            message="Subscription plan updated successfully.",
        )

    # Swagger documentation for Partial Update.
    @extend_schema(
        request=UpdateSubscriptionPlanSerializer,
        responses={200: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
        summary="Partially update a subscription plan.",
    )
    def patch(self, request, uuid):
        # Fetch existing plan.
        plan = SubscriptionPlanService.get_plan(uuid)

        # Validate only provided fields.
        serializer = UpdateSubscriptionPlanSerializer(
            plan,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        plan = SubscriptionPlanService.update_plan(
            plan,
            serializer.validated_data,
        )

        return success_response(
            data=SubscriptionPlanSerializer(plan).data,
            message="Subscription plan updated successfully.",
        )

    # Swagger documentation for Delete Subscription Plan.
    @extend_schema(
        responses={200: None},
        tags=["Subscription Plans"],
        summary="Delete a subscription plan.",
    )
    def delete(self, request, uuid):
        # Fetch existing plan.
        plan = SubscriptionPlanService.get_plan(uuid)

        SubscriptionPlanService.delete_plan(plan)

        return success_response(
            message="Subscription plan deleted successfully.",
        )
