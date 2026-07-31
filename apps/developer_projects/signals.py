from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationWebSocketService
from .models import DeveloperProject


@receiver(post_save, sender=DeveloperProject)
def trigger_dashboard_and_notification_on_project_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcasts
    and notifications whenever a new DeveloperProject is created.
    """
    if created:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
        if instance.developer:
            developer = instance.developer
            transaction.on_commit(
                lambda dev=developer: DashboardWebSocketService.broadcast_developer_dashboard_update(dev)
            )
            # Admin Notification
            transaction.on_commit(
                lambda dev=developer: NotificationWebSocketService.send_admin_notification(
                    title="Project Created",
                    message=f'Project "{instance.name}" was created by {dev.email}.',
                    notification_type=Notification.NotificationType.PROJECT_CREATED,
                    metadata={
                        "project_uuid": str(instance.uuid),
                        "project_name": instance.name,
                        "developer_email": dev.email,
                    },
                )
            )
            # Developer Notification
            transaction.on_commit(
                lambda dev=developer: NotificationWebSocketService.send_developer_notification(
                    user=dev,
                    title="Project Created",
                    message=f'Project "{instance.name}" was created successfully.',
                    notification_type=Notification.NotificationType.PROJECT_CREATED,
                    metadata={
                        "project_uuid": str(instance.uuid),
                        "project_name": instance.name,
                    },
                )
            )
