from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification
from .serializers import NotificationSerializer


class NotificationService:
    """
    Handles business logic for creating and managing Notification DB records.
    """

    @staticmethod
    def create_admin_notification(title, message, notification_type, metadata=None):
        """
        Saves an Admin system notification to the database.
        """
        return Notification.objects.create(
            recipient=None,
            title=title,
            message=message,
            notification_type=notification_type,
            metadata=metadata or {},
        )

    @staticmethod
    def create_developer_notification(user, title, message, notification_type, metadata=None):
        """
        Saves a Developer-specific notification to the database.
        """
        return Notification.objects.create(
            recipient=user,
            title=title,
            message=message,
            notification_type=notification_type,
            metadata=metadata or {},
        )


class NotificationWebSocketService:
    """
    Handles real-time WebSocket broadcasting operations for Notifications.
    Saves notifications to DB first, then broadcasts full object payload.
    """

    # The Channel Group for all connected admins.
    ADMIN_GROUP = "notifications_admin"

    @classmethod
    def send_admin_notification(cls, title, message, notification_type, metadata=None):
        """
        1. Saves Notification in DB.
        2. Broadcasts full notification payload to 'notifications_admin' Channel Group.
        3. Returns created Notification instance.
        """
        notification = NotificationService.create_admin_notification(
            title=title,
            message=message,
            notification_type=notification_type,
            metadata=metadata,
        )

        # Converts the model into JSON-friendly data.
        serializer = NotificationSerializer(notification)
        payload = {
            "event": "notification_created",
            "notification": serializer.data,
        }

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                cls.ADMIN_GROUP,
                {
                    "type": "notification_created",
                    "payload": payload,
                },
            )

        return notification

    @classmethod
    def send_developer_notification(cls, user, title, message, notification_type, metadata=None):
        """
        1. Saves Notification in DB for specified recipient user.
        2. Broadcasts full notification payload to 'notifications_user_<user_id>' Channel Group.
        3. Returns created Notification instance.
        """
        notification = NotificationService.create_developer_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            metadata=metadata,
        )

        serializer = NotificationSerializer(notification)
        payload = {
            "event": "notification_created",
            "notification": serializer.data,
        }

        group_name = f"notifications_user_{user.id}"

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "notification_created",
                    "payload": payload,
                },
            )

        return notification
