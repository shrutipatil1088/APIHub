from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationWebSocketService
from .models import User


@receiver(post_save, sender=User)
def trigger_dashboard_and_notification_on_user_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcast
    and Admin notification whenever a new Developer user registers.
    """
    if created and instance.role == User.Role.DEVELOPER:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
        transaction.on_commit(
            lambda: NotificationWebSocketService.send_admin_notification(
                title="New Developer Registered",
                message=f"{instance.full_name or instance.email} joined APIHub.",
                notification_type=Notification.NotificationType.DEVELOPER_REGISTERED,
                metadata={"user_id": instance.id, "email": instance.email},
            )
        )
