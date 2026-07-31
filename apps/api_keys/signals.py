from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationWebSocketService
from .models import APIKey


@receiver(post_save, sender=APIKey)
def trigger_dashboard_and_notification_on_api_key_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcasts
    and notifications whenever a new APIKey is created.
    """
    if created:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
        if instance.project and instance.project.developer:
            developer = instance.project.developer
            transaction.on_commit(
                lambda dev=developer: DashboardWebSocketService.broadcast_developer_dashboard_update(dev)
            )
            # Admin Notification
            transaction.on_commit(
                lambda dev=developer: NotificationWebSocketService.send_admin_notification(
                    title="API Key Generated",
                    message=f'A new API Key "{instance.name}" was generated for project "{instance.project.name}".',
                    notification_type=Notification.NotificationType.API_KEY_CREATED,
                    metadata={
                        "key_uuid": str(instance.uuid),
                        "project_name": instance.project.name,
                    },
                )
            )
            # Developer Notification
            transaction.on_commit(
                lambda dev=developer: NotificationWebSocketService.send_developer_notification(
                    user=dev,
                    title="API Key Generated",
                    message=f'A new API Key "{instance.name}" has been generated.',
                    notification_type=Notification.NotificationType.API_KEY_CREATED,
                    metadata={
                        "key_uuid": str(instance.uuid),
                        "key_name": instance.name,
                    },
                )
            )
