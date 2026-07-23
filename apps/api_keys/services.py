import hashlib
import secrets

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.subscriptions.models import UserSubscription
from .filters import APIKeyFilter, ALLOWED_ORDERING_FIELDS
from .models import APIKey


class APIKeyService:
    """
    Contains business logic for the APIKey module.
    """

    # Return APIKey list with search, filter and ordering.
    @staticmethod
    def list_keys(user, query_params):
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

        # Admin can see all, developer sees only keys for their own projects
        if user.role == User.Role.ADMIN:
            queryset = (
                APIKey.objects
                .filter(is_deleted=False)
                .select_related("project", "subscription", "subscription__plan")
            )
        else:
            queryset = (
                APIKey.objects
                .filter(
                    project__developer=user,
                    is_deleted=False,
                )
                .select_related("project", "subscription", "subscription__plan")
            )

        return APIKeyFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single API key by UUID.
    @staticmethod
    def get_key(uuid):
        return get_object_or_404(
            APIKey.objects.select_related(
                "project",
                "subscription",
                "subscription__plan",
            ),
            uuid=uuid,
            is_deleted=False,
        )

    # Create a new API key.
    @staticmethod
    def create_key(user, validated_data):
        # 1. Verify developer role
        if user.role != User.Role.DEVELOPER:
            raise ValidationError(
                {"detail": "Only developers can generate API keys."}
            )

        project = validated_data["project"]

        # 2. Verify project ownership
        if project.developer != user:
            raise ValidationError(
                {"project": ["Project does not belong to the authenticated user."]}
            )

        # 3. Find ACTIVE & non-expired UserSubscription
        subscription = UserSubscription.objects.filter(
            user=user,
            status=UserSubscription.Status.ACTIVE,
            end_date__gt=timezone.now(),
            is_deleted=False,
        ).order_by("-created_at").first()

        # 4. If there is no active/unexpired subscription, return a ValidationError
        if not subscription:
            raise ValidationError(
                {"subscription": ["Active subscription required to generate API keys."]}
            )

        # 5. Generate secure random key (pk_live_...)
        plain_key = f"pk_live_{secrets.token_urlsafe(32)}"

        # 6. Hash using SHA256
        key_hash = hashlib.sha256(plain_key.encode("utf-8")).hexdigest()

        # 7. Save only hash with subscription expiration
        api_key = APIKey.objects.create(
            project=project,
            subscription=subscription,
            name=validated_data["name"].strip(),
            key_hash=key_hash,
            expires_at=subscription.end_date,
            is_active=True,
        )

        # 8. Return both saved object and plain key
        return api_key, plain_key

    # Update an existing API key (only allow name).
    @staticmethod
    def update_key(key, validated_data):
        name = validated_data.get("name")
        if name:
            key.name = name.strip()
            key.save(
                update_fields=[
                    "name",
                    "updated_at",
                ]
            )
        return key

    # Deactivate an API key.
    @staticmethod
    def deactivate_key(key):
        key.is_active = False
        key.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )
        return key

    # Regenerate key (generate completely new key, replace hash, return plain key once).
    @staticmethod
    def regenerate_key(key):
        # Verify active non-expired subscription before regeneration
        if (
            not key.subscription
            or key.subscription.is_deleted
            or key.subscription.status != UserSubscription.Status.ACTIVE
            or key.subscription.end_date <= timezone.now()
        ):
            raise ValidationError(
                {"subscription": ["Active subscription required to regenerate API keys."]}
            )

        # Generate new plain key
        plain_key = f"pk_live_{secrets.token_urlsafe(32)}"

        # Hash using SHA256
        key_hash = hashlib.sha256(plain_key.encode("utf-8")).hexdigest()

        # Replace hash, update expiration & set active
        key.key_hash = key_hash
        key.expires_at = key.subscription.end_date
        key.is_active = True
        key.save(
            update_fields=[
                "key_hash",
                "expires_at",
                "is_active",
                "updated_at",
            ]
        )

        return key, plain_key

    # Authenticate and validate a plain API key string during API request processing.
    @staticmethod
    def authenticate_key(plain_key):
        from rest_framework.exceptions import AuthenticationFailed
        from apps.subscriptions.services import SubscriptionValidationService

        if not plain_key or not isinstance(plain_key, str):
            raise AuthenticationFailed("Invalid API Key.")

        key_hash = hashlib.sha256(plain_key.encode("utf-8")).hexdigest()

        key = (
            APIKey.objects
            .select_related(
                "project",
                "subscription",
                "subscription__plan",
                "project__developer",
            )
            .filter(
                key_hash=key_hash,
                is_deleted=False,
            )
            .first()
        )

        if not key:
            raise AuthenticationFailed("Invalid API Key.")

        if not key.is_active:
            raise AuthenticationFailed("API Key is inactive.")

        # Validate subscription status & monthly usage limit via SubscriptionValidationService
        SubscriptionValidationService.validate(key)

        # Update last_used_at timestamp
        now = timezone.now()
        key.last_used_at = now
        key.save(update_fields=["last_used_at", "updated_at"])

        return key.project.developer, key
