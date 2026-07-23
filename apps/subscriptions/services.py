from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.accounts.models import User
from .exceptions import UsageLimitExceeded
from .models import SubscriptionPlan, UserSubscription
from .filters import (
    SubscriptionPlanFilter,
    ALLOWED_ORDERING_FIELDS,
    UserSubscriptionFilter,
    ALLOWED_USER_SUBSCRIPTION_ORDERING_FIELDS,
)


# Contains business logic for the SubscriptionPlan module.
class SubscriptionPlanService:

    # Return SubscriptionPlan list with search, filter and ordering.
    @staticmethod
    def list_plans(query_params):
        ordering = query_params.get("ordering")

        if ordering and ordering not in ALLOWED_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        queryset = (
            SubscriptionPlan.objects
            .filter(is_deleted=False)
        )

        return SubscriptionPlanFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single plan by UUID.
    @staticmethod
    def get_plan(uuid):
        return get_object_or_404(
            SubscriptionPlan,
            uuid=uuid,
            is_deleted=False,
        )

    # Create a new subscription plan (restoring soft-deleted duplicate if exists).
    @staticmethod
    def create_plan(validated_data):
        name = validated_data.get("name")
        existing_plan = SubscriptionPlan.objects.filter(
            name=name,
        ).first()

        if existing_plan:
            existing_plan.restore()
            for field, value in validated_data.items():
                setattr(existing_plan, field, value)
            existing_plan.save()
            return existing_plan

        return SubscriptionPlan.objects.create(
            **validated_data,
        )

    # Update an existing subscription plan.
    @staticmethod
    def update_plan(plan, validated_data):
        for field, value in validated_data.items():
            setattr(
                plan,
                field,
                value,
            )

        plan.save(
            update_fields=[
                *validated_data.keys(),
                "updated_at",
            ]
        )

        return plan

    # Soft delete a subscription plan.
    @staticmethod
    def delete_plan(plan):
        plan.soft_delete()


# Contains business logic for the UserSubscription module.
class UserSubscriptionService:

    # Return UserSubscription list with search, filter and ordering.
    @staticmethod
    def list_subscriptions(query_params):
        ordering = query_params.get("ordering")

        if ordering and ordering not in ALLOWED_USER_SUBSCRIPTION_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_USER_SUBSCRIPTION_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        queryset = (
            UserSubscription.objects
            .filter(is_deleted=False)
            .select_related("user", "plan")
        )

        return UserSubscriptionFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single subscription by UUID.
    @staticmethod
    def get_subscription(uuid):
        return get_object_or_404(
            UserSubscription.objects.select_related("user", "plan"),
            uuid=uuid,
            is_deleted=False,
        )

    # Purchase/create a new subscription.
    @staticmethod
    def create_subscription(user, validated_data):
        # Validate that only DEVELOPER role users can purchase a plan.
        if user.role != User.Role.DEVELOPER:
            raise ValidationError(
                {"detail": "Only developers can purchase a subscription plan."}
            )

        plan = validated_data.get("plan")
        auto_renew = validated_data.get("auto_renew", True)

        # Check if the user already has an active subscription
        active_sub_exists = UserSubscription.objects.filter(
            user=user,
            status=UserSubscription.Status.ACTIVE,
            is_deleted=False,
        ).exists()

        if active_sub_exists:
            raise ValidationError(
                {"detail": "User already has an active subscription."}
            )

        # Calculate dates
        start_date = timezone.now()
        if plan.billing_cycle == SubscriptionPlan.BillingCycle.MONTHLY:
            end_date = start_date + timedelta(days=30)
        elif plan.billing_cycle == SubscriptionPlan.BillingCycle.YEARLY:
            end_date = start_date + timedelta(days=365)
        else:
            # Fallback/Safety
            end_date = start_date + timedelta(days=30)

        # Create user subscription
        return UserSubscription.objects.create(
            user=user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status=UserSubscription.Status.ACTIVE,
            auto_renew=auto_renew,
        )

    # Update subscription status and renewal options.
    @staticmethod
    def update_subscription(subscription, validated_data):
        for field, value in validated_data.items():
            setattr(
                subscription,
                field,
                value,
            )

        subscription.save(
            update_fields=[
                *validated_data.keys(),
                "updated_at",
            ]
        )

        return subscription

    # Soft delete a subscription.
    @staticmethod
    def delete_subscription(subscription):
        subscription.soft_delete()

    # Get subscriptions belonging to the user.
    @staticmethod
    def get_my_subscriptions(user):
        return (
            UserSubscription.objects
            .filter(
                user=user,
                is_deleted=False,
            )
            .select_related("user", "plan")
            .order_by("-created_at")
        )


class SubscriptionValidationService:
    """
    Contains validation logic for API Key Subscriptions and Usage Limits.
    """

    @staticmethod
    def validate_subscription(api_key):
        """
        Validates that the API key belongs to an active project and has an active, unexpired subscription.
        """
        # 1. Check DeveloperProject status
        if not api_key.project or api_key.project.is_deleted or not api_key.project.is_active:
            raise PermissionDenied("Developer project is inactive.")

        subscription = api_key.subscription

        # 2. Check UserSubscription presence and deletion
        if not subscription or subscription.is_deleted:
            raise PermissionDenied("Subscription is not active.")

        # 3. Check subscription status & expiry
        now = timezone.now()

        if (
            (api_key.expires_at and api_key.expires_at <= now)
            or (subscription.end_date and subscription.end_date <= now)
            or subscription.status == UserSubscription.Status.EXPIRED
        ):
            raise PermissionDenied("Subscription has expired.")

        if subscription.status == UserSubscription.Status.CANCELLED:
            raise PermissionDenied("Subscription has been cancelled.")

        if subscription.status != UserSubscription.Status.ACTIVE:
            raise PermissionDenied("Subscription is not active.")

        return True

    @staticmethod
    def validate_usage_limit(api_key):
        """
        Validates that the API key's current month usage does not exceed its subscription plan limit.
        """
        subscription = api_key.subscription
        if not subscription or not subscription.plan:
            return True

        plan = subscription.plan

        # Bypass limit validation for Unlimited / Enterprise plans
        if (
            plan.request_limit == 0
            or "enterprise" in plan.name.lower()
            or "unlimited" in plan.name.lower()
        ):
            return True

        # Calculate current month request count from UsageLog
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        from apps.usage_logs.models import UsageLog

        current_requests = UsageLog.objects.filter(
            api_key=api_key,
            is_deleted=False,
            requested_at__gte=start_of_month,
        ).count()

        if current_requests >= plan.request_limit:
            raise UsageLimitExceeded("Monthly API request limit exceeded.")

        return True

    @staticmethod
    def validate(api_key):
        """
        Performs full subscription and usage limit validation for an authenticated API key.
        """
        SubscriptionValidationService.validate_subscription(api_key)
        SubscriptionValidationService.validate_usage_limit(api_key)
        return True
