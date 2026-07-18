from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import SubscriptionPlan
from .filters import SubscriptionPlanFilter, ALLOWED_ORDERING_FIELDS


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
