from rest_framework import serializers

from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import UserSubscription
from .models import APIKey


class APIKeyBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer used for generating a new APIKey.
    """

    project = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=DeveloperProject.objects.filter(is_deleted=False),
        error_messages={
            "does_not_exist": "Project with this UUID does not exist.",
        },
    )

    class Meta:
        model = APIKey
        fields = (
            "name",
            "project",
        )

    # Validate key name.
    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "API key name must contain at least 3 characters."
            )

        return value

    # Validate project ownership and unique project + name.
    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        project = attrs.get("project")
        name = attrs.get("name")

        # Verify project belongs to authenticated user
        if project and user:
            if project.developer != user:
                raise serializers.ValidationError(
                    {"project": ["Project does not belong to the authenticated user."]}
                )

        # Unique project + name check
        if project and name:
            name = name.strip()
            queryset = APIKey.objects.filter(
                project=project,
                name__iexact=name,
                is_deleted=False,
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    {"name": ["An API key with this name already exists for this project."]}
                )

        return attrs


class ProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for nested DeveloperProject detail in APIKey responses.
    """

    class Meta:
        model = DeveloperProject
        fields = (
            "uuid",
            "name",
            "description",
        )


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for nested UserSubscription detail in APIKey responses.
    """

    plan_name = serializers.CharField(
        source="plan.name",
        read_only=True,
    )

    class Meta:
        model = UserSubscription
        fields = (
            "uuid",
            "plan_name",
            "status",
        )


class APIKeySerializer(serializers.ModelSerializer):
    """
    Response serializer for APIKey metadata.
    Excludes key_hash for security.
    """

    project = ProjectDetailSerializer(read_only=True)
    subscription = SubscriptionDetailSerializer(read_only=True)

    class Meta:
        model = APIKey
        fields = (
            "uuid",
            "project",
            "subscription",
            "name",
            "is_active",
            "last_used_at",
            "expires_at",
            "created_at",
            "updated_at",
        )


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating/renaming an APIKey (only name allowed).
    """

    class Meta:
        model = APIKey
        fields = (
            "name",
        )

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "API key name must contain at least 3 characters."
            )

        if self.instance:
            queryset = APIKey.objects.filter(
                project=self.instance.project,
                name__iexact=value,
                is_deleted=False,
            ).exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "An API key with this name already exists for this project."
                )

        return value
