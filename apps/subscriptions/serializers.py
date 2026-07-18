from rest_framework import serializers
from apps.accounts.models import User
from .models import SubscriptionPlan, UserSubscription


class SubscriptionPlanBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer containing shared validation for SubscriptionPlan create/update.
    """
    name = serializers.CharField(validators=[])

    class Meta:
        model = SubscriptionPlan
        fields = (
            "name",
            "description",
            "price",
            "billing_cycle",
            "request_limit",
            "is_active",
        )

    # Validate subscription plan name.
    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Subscription plan name must contain at least 3 characters."
            )

        # Unique check:
        # During creation (no self.instance), we check only for active duplicates (is_deleted=False).
        # This allows the serializer validation to pass so the service can restore it.
        # During update (self.instance is not None), we check for any duplicates (active or soft-deleted)
        # to prevent update collisions.
        if self.instance:
            queryset = SubscriptionPlan.objects.filter(
                name=value,
            ).exclude(pk=self.instance.pk)
        else:
            queryset = SubscriptionPlan.objects.filter(
                name=value,
                is_deleted=False,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A subscription plan with this name already exists."
            )

        return value

    # Validate description.
    def validate_description(self, value):
        value = value.strip()

        if len(value) < 20:
            raise serializers.ValidationError(
                "Description must contain at least 20 characters."
            )

        return value

    # Validate price.
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Price must be greater than or equal to 0."
            )
        return value

    # Validate request limit.
    def validate_request_limit(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Request limit must be greater than 0."
            )
        return value

    def validate(self, attrs):
        name = attrs.get("name", self.instance.name if self.instance else "")
        price = attrs.get("price", self.instance.price if self.instance else None)

        if name and price is not None:
            name_stripped = name.strip().lower()
            is_named_free = (
                name_stripped == "free" or
                name_stripped.startswith("free ") or
                "free" in name_stripped
            )

            if is_named_free:
                if price != 0:
                    raise serializers.ValidationError(
                        {"price": "Free plan must have a price of 0."}
                    )
            else:
                if price <= 0:
                    raise serializers.ValidationError(
                        {"price": "Price must be greater than 0."}
                    )
        return attrs


class CreateSubscriptionPlanSerializer(SubscriptionPlanBaseSerializer):
    """
    Serializer used while creating a subscription plan.
    """

    class Meta(SubscriptionPlanBaseSerializer.Meta):
        fields = SubscriptionPlanBaseSerializer.Meta.fields


class UpdateSubscriptionPlanSerializer(SubscriptionPlanBaseSerializer):
    """
    Serializer used while updating a subscription plan.
    """

    class Meta(SubscriptionPlanBaseSerializer.Meta):
        fields = SubscriptionPlanBaseSerializer.Meta.fields


class SubscriptionPlanListSerializer(serializers.ModelSerializer):
    """
    Serializer used for listing subscription plans.
    """

    class Meta:
        model = SubscriptionPlan
        fields = (
            "uuid",
            "name",
            "price",
            "billing_cycle",
            "is_active",
        )


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Serializer used for subscription plan detail responses.
    """

    class Meta:
        model = SubscriptionPlan
        fields = (
            "uuid",
            "name",
            "description",
            "price",
            "billing_cycle",
            "request_limit",
            "is_active",
            "created_at",
            "updated_at",
        )


# ============================================================================
# UserSubscription Serializers
# ============================================================================

class CreateUserSubscriptionSerializer(serializers.Serializer):
    """
    Serializer used while purchasing a subscription.
    """
    plan = serializers.UUIDField(required=True)
    auto_renew = serializers.BooleanField(default=True)

    def validate_plan(self, value):
        try:
            plan = SubscriptionPlan.objects.get(
                uuid=value,
                is_deleted=False,
            )
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError(
                "Subscription plan does not exist."
            )

        if not plan.is_active:
            raise serializers.ValidationError(
                "Subscription plan is not active."
            )

        return plan


class UpdateUserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer used while updating a subscription.
    """
    class Meta:
        model = UserSubscription
        fields = (
            "status",
            "auto_renew",
        )


class UserSubscriptionListSerializer(serializers.ModelSerializer):
    """
    Serializer used for listing user subscriptions.
    """
    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )
    plan_name = serializers.CharField(
        source="plan.name",
        read_only=True,
    )

    class Meta:
        model = UserSubscription
        fields = (
            "uuid",
            "user_email",
            "plan_name",
            "status",
            "start_date",
            "end_date",
            "auto_renew",
        )


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for User detail in nested response.
    """
    class Meta:
        model = User
        fields = (
            "uuid",
            "email",
            "full_name",
        )


class PlanDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for SubscriptionPlan detail in nested response.
    """
    class Meta:
        model = SubscriptionPlan
        fields = (
            "uuid",
            "name",
            "price",
            "billing_cycle",
            "request_limit",
        )


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer used for user subscription detail responses.
    """
    user = UserDetailSerializer(read_only=True)
    plan = PlanDetailSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = (
            "uuid",
            "user",
            "plan",
            "status",
            "auto_renew",
            "start_date",
            "end_date",
            "created_at",
            "updated_at",
        )
