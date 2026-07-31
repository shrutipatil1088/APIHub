from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    Maps 'uuid' to 'id' for a clean public REST API representation.
    """

    id = serializers.UUIDField(source="uuid", read_only=True)
    recipient_email = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "recipient_email",
            "title",
            "message",
            "notification_type",
            "metadata",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "recipient_email",
            "title",
            "message",
            "notification_type",
            "metadata",
            "created_at",
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_recipient_email(self, obj):
        return obj.recipient.email if obj.recipient else None
