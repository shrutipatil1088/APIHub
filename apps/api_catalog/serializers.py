# serializers do 3 major jobs:
#1. Convert Model → JSON
#2. Convert JSON → Python
#3. Validate data

#used for = Automatic validation + Custom validation

from rest_framework import serializers

from .models import API, APIVersion


class APIBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer containing shared validation for create/update.
    # Shared serializer for Create and Update APIs.
    """
    # This serializer works with API model.
    class Meta:
        model = API
        fields = (
            "name",
            "description",
            "status",
            "is_active",
        )

    # # Validate API name.
    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "API name must contain at least 3 characters."
            )

        queryset = API.objects.filter(
            name=value,
            is_deleted=False,
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "An API with this name already exists."
            )

        return value

    # Validate API description.
    def validate_description(self, value):
        value = value.strip()

        if len(value) < 20:
            raise serializers.ValidationError(
                "Description must contain at least 20 characters."
            )

        return value

    # Validate multiple fields together.
    def validate(self, attrs):
        status = attrs.get(
            "status",
            self.instance.status if self.instance else API.Status.DRAFT,
        )

        description = attrs.get(
            "description",
            self.instance.description if self.instance else "",
        )

        if (
            status == API.Status.PUBLISHED
            and not description.strip()
        ):
            raise serializers.ValidationError(
                {
                    "description": (
                        "Description is required when publishing an API."
                    )
                }
            )

        return attrs

# Serializer used for creating APIs.
class CreateAPISerializer(APIBaseSerializer):
    """
    Serializer used while creating an API.
    """

    class Meta(APIBaseSerializer.Meta):
        fields = APIBaseSerializer.Meta.fields

# Serializer used for updating APIs.
class UpdateAPISerializer(APIBaseSerializer):
    """
    Serializer used while updating an API.
    """

    class Meta(APIBaseSerializer.Meta):
        fields = APIBaseSerializer.Meta.fields

# Serializer used in API listing.
class APIListSerializer(serializers.ModelSerializer):
    """
    Serializer used for listing APIs.
    """

    class Meta:
        model = API
        fields = (
            "uuid",
            "name",
            "slug",
            "status",
            "is_active",
        )

# Serializer used for API detail response.
class APISerializer(serializers.ModelSerializer):
    """
    Serializer used for API detail responses.
    """

    created_by = serializers.CharField(
        source="created_by.email",
        read_only=True,
    )

    class Meta:
        model = API
        fields = (
            "uuid",
            "name",
            "slug",
            "description",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "is_active",
        )


# ============================================================================
# API Version Serializers
# ============================================================================

class APIVersionBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer containing shared validation for API version create/update.
    """

    class Meta:
        model = APIVersion
        fields = (
            "version",
            "release_notes",
            "is_latest",
            "is_active",
        )

    def validate_version(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Version cannot be empty."
            )

        # Retrieve view from context to find parent API
        view = self.context.get("view")
        api = None

        if view and "api_uuid" in view.kwargs:
            api_uuid = view.kwargs["api_uuid"]
            try:
                api = API.objects.get(uuid=api_uuid, is_deleted=False)
            except API.DoesNotExist:
                raise serializers.ValidationError(
                    "Parent API does not exist."
                )
        elif self.instance:
            api = self.instance.api

        if api:
            queryset = APIVersion.objects.filter(
                api=api,
                version=value,
                is_deleted=False,
            )

            if self.instance:
                queryset = queryset.exclude(
                    pk=self.instance.pk,
                )

            if queryset.exists():
                raise serializers.ValidationError(
                    "A version with this name already exists for this API."
                )

        return value


class CreateAPIVersionSerializer(APIVersionBaseSerializer):
    """
    Serializer used while creating an API version.
    """

    class Meta(APIVersionBaseSerializer.Meta):
        fields = APIVersionBaseSerializer.Meta.fields


class UpdateAPIVersionSerializer(APIVersionBaseSerializer):
    """
    Serializer used while updating an API version.
    """

    class Meta(APIVersionBaseSerializer.Meta):
        fields = APIVersionBaseSerializer.Meta.fields


class APIVersionListSerializer(serializers.ModelSerializer):
    """
    Serializer used for listing API versions.
    """

    class Meta:
        model = APIVersion
        fields = (
            "uuid",
            "version",
            "is_latest",
            "is_active",
            "created_at",
        )


class APIVersionSerializer(serializers.ModelSerializer):
    """
    Serializer used for API version detail responses.
    """

    api_uuid = serializers.UUIDField(
        source="api.uuid",
        read_only=True,
    )
    api_name = serializers.CharField(
        source="api.name",
        read_only=True,
    )

    class Meta:
        model = APIVersion
        fields = (
            "uuid",
            "api_uuid",
            "api_name",
            "version",
            "release_notes",
            "is_latest",
            "is_active",
            "created_at",
            "updated_at",
        )