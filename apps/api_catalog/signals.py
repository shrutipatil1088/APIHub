from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationWebSocketService
from .models import API, APIVersion, Endpoint


@receiver(post_save, sender=API)
def trigger_dashboard_update_on_api_publish(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcast
    and Admin notification whenever an API instance is published.
    """
    if instance.status == API.Status.PUBLISHED:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
        transaction.on_commit(
            lambda: NotificationWebSocketService.send_admin_notification(
                title="New API Published",
                message=f"{instance.name} has been published.",
                notification_type=Notification.NotificationType.API_PUBLISHED,
                metadata={"api_uuid": str(instance.uuid), "api_name": instance.name},
            )
        )


@receiver(post_save, sender=APIVersion)
def trigger_dashboard_update_on_api_version_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcast
    whenever a new APIVersion instance is created.
    """
    if created:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )


@receiver(post_save, sender=Endpoint)
def trigger_dashboard_update_on_endpoint_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcast
    whenever a new Endpoint instance is created.
    """
    if created:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
