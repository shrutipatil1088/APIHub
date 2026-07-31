from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.dashboard.services import DashboardWebSocketService
from .models import API, APIVersion, Endpoint


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


@receiver(post_save, sender=APIVersion)
def trigger_dashboard_update_on_api_version_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcast
    whenever a new APIVersion instance is created.
    Broadcasts updated Admin metrics to 'dashboard_admin' group.
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
    Broadcasts updated Admin metrics to 'dashboard_admin' group.
    """
    if created:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
