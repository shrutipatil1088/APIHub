from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from .models import User


@receiver(post_save, sender=User)
def trigger_dashboard_update_on_user_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcast
    whenever a new Developer user is created.
    Broadcasts updated Admin metrics to 'dashboard_admin' group.
    """
    if created and instance.role == User.Role.DEVELOPER:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
