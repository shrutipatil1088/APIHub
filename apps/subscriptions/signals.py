from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User
from apps.dashboard.services import DashboardWebSocketService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationWebSocketService
from .models import SubscriptionPlan, UserSubscription


@receiver(post_save, sender=SubscriptionPlan)
def trigger_notification_on_subscription_plan_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket notification
    whenever a new SubscriptionPlan is created.
    """
    if created:
        transaction.on_commit(
            lambda: NotificationWebSocketService.send_admin_notification(
                title="Subscription Plan Created",
                message=f'New subscription plan "{instance.name}" has been created.',
                notification_type=Notification.NotificationType.SYSTEM,
                metadata={
                    "plan_uuid": str(instance.uuid),
                    "plan_name": instance.name,
                    "price": str(instance.price),
                },
            )
        )


@receiver(post_save, sender=UserSubscription)
def trigger_dashboard_and_notification_on_subscription_save(sender, instance, created, **kwargs):
    """
    Signal handler that triggers real-time WebSocket dashboard broadcasts
    and notifications whenever a new UserSubscription is created.
    """
    if created:
        transaction.on_commit(
            DashboardWebSocketService.broadcast_admin_dashboard_update
        )
        if instance.user and instance.user.role == User.Role.DEVELOPER:
            developer = instance.user
            transaction.on_commit(
                lambda dev=developer: DashboardWebSocketService.broadcast_developer_dashboard_update(dev)
            )
            # Admin Notification
            transaction.on_commit(
                lambda dev=developer: NotificationWebSocketService.send_admin_notification(
                    title="Subscription Activated",
                    message=f"Developer {dev.email} activated {instance.plan.name} subscription.",
                    notification_type=Notification.NotificationType.SUBSCRIPTION_CREATED,
                    metadata={
                        "subscription_uuid": str(instance.uuid),
                        "plan_name": instance.plan.name,
                    },
                )
            )
            # Developer Notification
            transaction.on_commit(
                lambda dev=developer: NotificationWebSocketService.send_developer_notification(
                    user=dev,
                    title="Subscription Activated",
                    message=f"Your {instance.plan.name} subscription is now active.",
                    notification_type=Notification.NotificationType.SUBSCRIPTION_CREATED,
                    metadata={
                        "subscription_uuid": str(instance.uuid),
                        "plan_name": instance.plan.name,
                    },
                )
            )
