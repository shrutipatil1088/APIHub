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
from apps.core.permissions import IsAdminRole
from apps.core.responses import success_response
from apps.core.pagination import StandardResultsSetPagination

from .models import SubscriptionPlan, UserSubscription
from .serializers import (
    CreateSubscriptionPlanSerializer,
    UpdateSubscriptionPlanSerializer,
    SubscriptionPlanListSerializer,
    SubscriptionPlanSerializer,
    CreateUserSubscriptionSerializer,
    UpdateUserSubscriptionSerializer,
    UserSubscriptionListSerializer,
    UserSubscriptionSerializer,
)
from .services import SubscriptionPlanService, UserSubscriptionService


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


# ============================================================================
# UserSubscription List & Create
# Handles:
# GET  -> List all subscriptions (Admin only)
# POST -> Purchase a new subscription (Authenticated)
# ============================================================================
class UserSubscriptionListCreateAPIView(APIView):

    # Assign permissions based on request method.
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]

    # Swagger documentation for List User Subscriptions.
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by subscription status.",
                enum=UserSubscription.Status.values,
            ),
            OpenApiParameter(
                name="auto_renew",
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description="Filter by auto renew option.",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Search user email or plan name.",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description=(
                    "Order results. "
                    "Available values: "
                    "created_at, -created_at, updated_at, -updated_at, start_date, -start_date, end_date, -end_date."
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
        responses={200: UserSubscriptionListSerializer(many=True)},
        tags=["User Subscriptions"],
        summary="List all user subscriptions (Admin only).",
    )
    def get(self, request):
        # Get filtered/search/ordered queryset.
        subscriptions = UserSubscriptionService.list_subscriptions(
            request.query_params,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            subscriptions,
            request,
        )

        # Convert queryset into JSON.
        serializer = UserSubscriptionListSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )

    # Swagger documentation for Purchase Subscription.
    @extend_schema(
        request=CreateUserSubscriptionSerializer,
        responses={201: UserSubscriptionSerializer},
        tags=["User Subscriptions"],
        summary="Purchase a subscription plan.",
    )
    def post(self, request):
        # Validate request data.
        serializer = CreateUserSubscriptionSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        # Create new subscription.
        subscription = UserSubscriptionService.create_subscription(
            request.user,
            serializer.validated_data,
        )

        # Return created object.
        return success_response(
            data=UserSubscriptionSerializer(subscription).data,
            message="Subscription purchased successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# UserSubscription Detail
# Handles:
# GET    -> Retrieve subscription (Admin or Owner)
# PATCH  -> Update subscription (Admin only)
# DELETE -> Soft Delete subscription (Admin only)
# ============================================================================
class UserSubscriptionDetailAPIView(APIView):

    # Assign permissions based on request method.
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]

    # Swagger documentation for Retrieve Subscription.
    @extend_schema(
        responses={200: UserSubscriptionSerializer},
        tags=["User Subscriptions"],
        summary="Retrieve user subscription details.",
    )
    def get(self, request, uuid):
        # Fetch subscription by UUID.
        subscription = UserSubscriptionService.get_subscription(uuid)

        # Check permissions: Admin or Owner.
        if (
            request.user.role != User.Role.ADMIN
            and subscription.user != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this subscription."
            )

        # Convert model into JSON.
        serializer = UserSubscriptionSerializer(subscription)

        return success_response(
            data=serializer.data,
            message="User subscription details fetched successfully.",
        )

    # Swagger documentation for Partial Update.
    @extend_schema(
        request=UpdateUserSubscriptionSerializer,
        responses={200: UserSubscriptionSerializer},
        tags=["User Subscriptions"],
        summary="Partially update a user subscription (Admin only).",
    )
    def patch(self, request, uuid):
        # Fetch existing subscription.
        subscription = UserSubscriptionService.get_subscription(uuid)

        # Validate provided fields.
        serializer = UpdateUserSubscriptionSerializer(
            subscription,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        subscription = UserSubscriptionService.update_subscription(
            subscription,
            serializer.validated_data,
        )

        return success_response(
            data=UserSubscriptionSerializer(subscription).data,
            message="User subscription updated successfully.",
        )

    # Swagger documentation for Delete User Subscription.
    @extend_schema(
        responses={200: None},
        tags=["User Subscriptions"],
        summary="Delete a user subscription (Admin only).",
    )
    def delete(self, request, uuid):
        # Fetch existing subscription.
        subscription = UserSubscriptionService.get_subscription(uuid)

        UserSubscriptionService.delete_subscription(subscription)

        return success_response(
            message="User subscription deleted successfully.",
        )


# ============================================================================
# My Subscriptions List
# Handles:
# GET -> List all subscriptions for request.user (Authenticated only)
# ============================================================================
class MySubscriptionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for List My Subscriptions.
    @extend_schema(
        parameters=[
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
        responses={200: UserSubscriptionListSerializer(many=True)},
        tags=["User Subscriptions"],
        summary="List my subscription history.",
    )
    def get(self, request):
        # Get current user's subscriptions.
        subscriptions = UserSubscriptionService.get_my_subscriptions(
            request.user,
        )

        # Apply pagination.
        paginator = StandardResultsSetPagination()

        page = paginator.paginate_queryset(
            subscriptions,
            request,
        )

        # Convert queryset into JSON.
        serializer = UserSubscriptionListSerializer(
            page,
            many=True,
        )

        # Return paginated response.
        return paginator.get_paginated_response(
            serializer.data,
        )
