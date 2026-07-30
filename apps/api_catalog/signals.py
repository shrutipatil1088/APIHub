from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from .models import API


@receiver(post_save, sender=API)
def trigger_dashboard_update_on_api_publish(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcast
    whenever an API instance is saved with status PUBLISHED.
    Broadcasts updated Admin metrics to 'dashboard_admin' group.
    """
    if instance.status == API.Status.PUBLISHED:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
