# serializers do 3 major jobs:
#1. Convert Model → JSON
#2. Convert JSON → Python
#3. Validate data

#used for = Automatic validation + Custom validation

from rest_framework import serializers

from .models import API, APIVersion, Endpoint


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

        import re
        if not re.match(r"^v\d+(\.\d+)*$", value):
            raise serializers.ValidationError(
                "Version must be in a format like 'v1', 'v2', 'v1.0', or 'v1.0.1'."
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
            if self.instance:
                queryset = APIVersion.objects.filter(
                    api=api,
                    version=value,
                ).exclude(
                    pk=self.instance.pk,
                )
            else:
                queryset = APIVersion.objects.filter(
                    api=api,
                    version=value,
                    is_deleted=False,
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


# ============================================================================
# API Endpoint Serializers
# ============================================================================

class EndpointBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer containing shared validation for Endpoint create/update.
    """

    class Meta:
        model = Endpoint
        fields = (
            "method",
            "path",
            "summary",
            "description",
            "request_schema",
            "response_schema",
            "is_active",
        )

    def validate_path(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Path cannot be empty."
            )
        if not value.startswith("/"):
            raise serializers.ValidationError(
                "Path must start with '/'."
            )

        return value

    def validate_summary(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Summary cannot be empty."
            )

        return value

    def validate(self, attrs):
        # Retrieve view from context to check uniqueness under parent APIVersion
        view = self.context.get("view")
        version = None

        if view and "version_uuid" in view.kwargs:
            version_uuid = view.kwargs["version_uuid"]
            try:
                version = APIVersion.objects.get(uuid=version_uuid, is_deleted=False)
            except APIVersion.DoesNotExist:
                raise serializers.ValidationError(
                    {"version": "Parent API version does not exist."}
                )
        elif self.instance:
            version = self.instance.version

        if version:
            method = attrs.get("method", self.instance.method if self.instance else None)
            path = attrs.get("path", self.instance.path if self.instance else None)

            if method and path:
                path = path.strip()
                if self.instance:
                    queryset = Endpoint.objects.filter(
                        version=version,
                        method=method,
                        path=path,
                    ).exclude(
                        pk=self.instance.pk,
                    )
                else:
                    queryset = Endpoint.objects.filter(
                        version=version,
                        method=method,
                        path=path,
                        is_deleted=False,
                    )

                if queryset.exists():
                    raise serializers.ValidationError(
                        "An endpoint with this method and path already exists for this API version."
                    )

        return attrs


class CreateEndpointSerializer(EndpointBaseSerializer):
    """
    Serializer used while creating an Endpoint.
    """

    class Meta(EndpointBaseSerializer.Meta):
        fields = EndpointBaseSerializer.Meta.fields


class UpdateEndpointSerializer(EndpointBaseSerializer):
    """
    Serializer used while updating an Endpoint.
    """

    class Meta(EndpointBaseSerializer.Meta):
        fields = EndpointBaseSerializer.Meta.fields


class EndpointListSerializer(serializers.ModelSerializer):
    """
    Serializer used for listing Endpoints.
    """

    class Meta:
        model = Endpoint
        fields = (
            "uuid",
            "method",
            "path",
            "summary",
            "is_active",
            "created_at",
        )


class EndpointSerializer(serializers.ModelSerializer):
    """
    Serializer used for Endpoint detail responses.
    """

    version_uuid = serializers.UUIDField(
        source="version.uuid",
        read_only=True,
    )
    version_name = serializers.CharField(
        source="version.version",
        read_only=True,
    )
    api_name = serializers.CharField(
        source="version.api.name",
        read_only=True,
    )

    class Meta:
        model = Endpoint
        fields = (
            "uuid",
            "version_uuid",
            "version_name",
            "api_name",
            "method",
            "path",
            "summary",
            "description",
            "request_schema",
            "response_schema",
            "is_active",
            "created_at",
            "updated_at",
        )


# ============================================================================
# API Documentation Serializers
# ============================================================================

class EndpointDocumentationSerializer(serializers.ModelSerializer):
    """
    Serializer for nested endpoint documentation.
    """
    class Meta:
        model = Endpoint
        fields = (
            "uuid",
            "method",
            "path",
            "summary",
            "description",
            "request_schema",
            "response_schema",
        )


class APIVersionDocumentationSerializer(serializers.ModelSerializer):
    """
    Serializer for nested API version documentation.
    """
    endpoints = EndpointDocumentationSerializer(many=True, read_only=True)

    class Meta:
        model = APIVersion
        fields = (
            "uuid",
            "version",
            "is_latest",
            "release_notes",
            "endpoints",
        )


class APIDocumentationSerializer(serializers.ModelSerializer):
    """
    Serializer for complete nested API documentation.
    """
    created_by = serializers.CharField(
        source="created_by.email",
        read_only=True,
    )
    versions = APIVersionDocumentationSerializer(many=True, read_only=True)

    class Meta:
        model = API
        fields = (
            "uuid",
            "name",
            "slug",
            "description",
            "status",
            "created_by",
            "versions",
        )