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
        summary="List Subscription Plans",
        description="""
Returns a paginated list of all subscription plans offered to developers.

Permissions:
- Authenticated Users

Supports:
- Search (by plan name)
- Filtering (by billing_cycle, is_active)
- Ordering (by name, price, created_at, updated_at)
- Pagination
""",
        parameters=[
            OpenApiParameter(
                name="billing_cycle",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter plans by billing cycle (MONTHLY, YEARLY).",
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
                description="Order results by field (e.g., price, -price, name).",
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
    )
    def get(self, request):
        plans = SubscriptionPlanService.list_plans(request.query_params)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(plans, request)
        serializer = SubscriptionPlanListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Swagger documentation for Create Subscription Plan.
    @extend_schema(
        summary="Create Subscription Plan",
        description="""
Creates a new subscription plan for developers.

Permissions:
- Admin Users only

Validation rules:
- Unique plan name required.
- Non-negative price and valid request limit.
""",
        request=CreateSubscriptionPlanSerializer,
        responses={201: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
    )
    def post(self, request):
        serializer = CreateSubscriptionPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = SubscriptionPlanService.create_plan(serializer.validated_data)
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

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [
                IsAuthenticated(),
                IsAdminRole(),
            ]

        return [
            IsAuthenticated(),
        ]

    # Swagger documentation for Retrieve Subscription Plan Details.
    @extend_schema(
        summary="Retrieve Subscription Plan Details",
        description="""
Retrieves details for a specific subscription plan by UUID.

Permissions:
- Authenticated Users
""",
        responses={200: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
    )
    def get(self, request, uuid):
        plan = SubscriptionPlanService.get_plan(uuid)
        serializer = SubscriptionPlanSerializer(plan)
        return success_response(
            data=serializer.data,
            message="Subscription plan fetched successfully.",
        )

    # Swagger documentation for Fully Update Subscription Plan.
    @extend_schema(
        summary="Fully Update Subscription Plan",
        description="""
Fully updates all fields of a subscription plan by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateSubscriptionPlanSerializer,
        responses={200: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
    )
    def put(self, request, uuid):
        plan = SubscriptionPlanService.get_plan(uuid)
        serializer = UpdateSubscriptionPlanSerializer(plan, data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = SubscriptionPlanService.update_plan(plan, serializer.validated_data)
        return success_response(
            data=SubscriptionPlanSerializer(plan).data,
            message="Subscription plan updated successfully.",
        )

    # Swagger documentation for Partially Update Subscription Plan.
    @extend_schema(
        summary="Partially Update Subscription Plan",
        description="""
Partially updates specific fields of a subscription plan by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateSubscriptionPlanSerializer,
        responses={200: SubscriptionPlanSerializer},
        tags=["Subscription Plans"],
    )
    def patch(self, request, uuid):
        plan = SubscriptionPlanService.get_plan(uuid)
        serializer = UpdateSubscriptionPlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        plan = SubscriptionPlanService.update_plan(plan, serializer.validated_data)
        return success_response(
            data=SubscriptionPlanSerializer(plan).data,
            message="Subscription plan updated successfully.",
        )

    # Swagger documentation for Delete Subscription Plan.
    @extend_schema(
        summary="Delete Subscription Plan",
        description="""
Soft-deletes a subscription plan by UUID.

Permissions:
- Admin Users only
""",
        responses={200: None},
        tags=["Subscription Plans"],
    )
    def delete(self, request, uuid):
        plan = SubscriptionPlanService.get_plan(uuid)
        SubscriptionPlanService.delete_plan(plan)
        return success_response(message="Subscription plan deleted successfully.")


# ============================================================================
# UserSubscription List & Create
# Handles:
# GET  -> List all subscriptions (Admin only)
# POST -> Purchase a new subscription (Developer only)
# ============================================================================
class UserSubscriptionListCreateAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]

    # Swagger documentation for List User Subscriptions.
    @extend_schema(
        summary="List User Subscriptions",
        description="""
Returns a paginated list of all developer user subscriptions across the platform.

Permissions:
- Admin Users only

Supports:
- Search (by user email, plan name)
- Filtering (by status, auto_renew)
- Ordering (by created_at, start_date, end_date)
- Pagination
""",
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by subscription status (ACTIVE, EXPIRED, CANCELLED, PENDING).",
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
                description="Order results by field (e.g., created_at, -created_at).",
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
    )
    def get(self, request):
        subscriptions = UserSubscriptionService.list_subscriptions(request.query_params)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(subscriptions, request)
        serializer = UserSubscriptionListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    # Swagger documentation for Purchase Subscription.
    @extend_schema(
        summary="Purchase Subscription",
        description="""
Purchases a subscription plan for the authenticated developer account.

Permissions:
- Developer role only

Validation rules:
- Requires a valid active subscription plan UUID.
- Developer cannot purchase duplicate active subscriptions simultaneously.
""",
        request=CreateUserSubscriptionSerializer,
        responses={201: UserSubscriptionSerializer},
        tags=["User Subscriptions"],
    )
    def post(self, request):
        serializer = CreateUserSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = UserSubscriptionService.create_subscription(
            request.user,
            serializer.validated_data,
        )
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

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminRole()]

    # Swagger documentation for Retrieve User Subscription Details.
    @extend_schema(
        summary="Retrieve User Subscription Details",
        description="""
Retrieves details for a specific user subscription by UUID.

Permissions:
- Admin: View any subscription.
- Developer: View only their own subscription.
""",
        responses={200: UserSubscriptionSerializer},
        tags=["User Subscriptions"],
    )
    def get(self, request, uuid):
        subscription = UserSubscriptionService.get_subscription(uuid)
        if (
            request.user.role != User.Role.ADMIN
            and subscription.user != request.user
        ):
            raise PermissionDenied(
                "You do not have permission to access this subscription."
            )
        serializer = UserSubscriptionSerializer(subscription)
        return success_response(
            data=serializer.data,
            message="User subscription details fetched successfully.",
        )

    # Swagger documentation for Partially Update User Subscription.
    @extend_schema(
        summary="Partially Update User Subscription",
        description="""
Partially updates user subscription status or renewal preferences by UUID.

Permissions:
- Admin Users only
""",
        request=UpdateUserSubscriptionSerializer,
        responses={200: UserSubscriptionSerializer},
        tags=["User Subscriptions"],
    )
    def patch(self, request, uuid):
        subscription = UserSubscriptionService.get_subscription(uuid)
        serializer = UpdateUserSubscriptionSerializer(
            subscription,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
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
        summary="Delete User Subscription",
        description="""
Soft-deletes a user subscription by UUID.

Permissions:
- Admin Users only
""",
        responses={200: None},
        tags=["User Subscriptions"],
    )
    def delete(self, request, uuid):
        subscription = UserSubscriptionService.get_subscription(uuid)
        UserSubscriptionService.delete_subscription(subscription)
        return success_response(message="User subscription deleted successfully.")


# ============================================================================
# My Subscriptions List
# Handles:
# GET -> List all subscriptions for request.user (Authenticated only)
# ============================================================================
class MySubscriptionListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # Swagger documentation for List My Subscription History.
    @extend_schema(
        summary="List My Subscription History",
        description="""
Returns a paginated subscription history for the currently authenticated developer.

Permissions:
- Authenticated Users

Supports:
- Pagination
""",
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
    )
    def get(self, request):
        subscriptions = UserSubscriptionService.get_my_subscriptions(request.user)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(subscriptions, request)
        serializer = UserSubscriptionListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
