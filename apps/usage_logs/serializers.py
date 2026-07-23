from rest_framework import serializers

from apps.developer_projects.models import DeveloperProject
from apps.api_keys.models import APIKey
from .models import UsageLog


class ProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for nested project details in UsageLog responses.
    """

    class Meta:
        model = DeveloperProject
        fields = (
            "uuid",
            "name",
        )


class APIKeyDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for nested APIKey details in UsageLog responses.
    """

    class Meta:
        model = APIKey
        fields = (
            "uuid",
            "name",
        )


class UsageLogSerializer(serializers.ModelSerializer):
    """
    Response serializer for UsageLog details.
    """

    project = ProjectDetailSerializer(read_only=True)
    api_key = APIKeyDetailSerializer(read_only=True)

    class Meta:
        model = UsageLog
        fields = (
            "uuid",
            "project",
            "api_key",
            "endpoint",
            "method",
            "status_code",
            "response_time_ms",
            "ip_address",
            "user_agent",
            "requested_at",
            "created_at",
        )
