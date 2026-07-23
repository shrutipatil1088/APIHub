from rest_framework import serializers
from apps.accounts.models import User
from .models import DeveloperProject


class DeveloperProjectBaseSerializer(serializers.ModelSerializer):
    """
    Base serializer containing shared validation for DeveloperProject.
    """

    class Meta:
        model = DeveloperProject
        fields = (
            "name",
            "description",
        )

    # Validate project name.
    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Project name must contain at least 3 characters."
            )

        # Unique check: (developer, name) per developer
        request = self.context.get("request")
        if self.instance:
            developer = self.instance.developer
        else:
            developer = request.user if request else None

        if developer:
            queryset = DeveloperProject.objects.filter(
                developer=developer,
                name__iexact=value,
                is_deleted=False,
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    "You already have a project with this name."
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


class DeveloperDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Developer details in nested responses.
    """
    class Meta:
        model = User
        fields = (
            "uuid",
            "email",
            "full_name",
        )


class DeveloperProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for DeveloperProject details response.
    """
    developer = DeveloperDetailSerializer(read_only=True)

    class Meta:
        model = DeveloperProject
        fields = (
            "uuid",
            "developer",
            "name",
            "description",
            "created_at",
            "updated_at",
        )
