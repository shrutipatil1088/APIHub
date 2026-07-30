from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from .models import DeveloperProject


@receiver(post_save, sender=DeveloperProject)
def trigger_dashboard_update_on_project_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcasts
    whenever a new DeveloperProject is created:
    - Broadcasts updated Admin metrics to 'dashboard_admin' group.
    - Broadcasts updated Developer metrics to 'dashboard_user_<user_id>' for affected developer.
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
