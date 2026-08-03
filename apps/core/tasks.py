from datetime import timedelta
import logging
from django.utils import timezone
from celery import shared_task

from apps.accounts.models import User
from apps.api_catalog.models import API
from apps.developer_projects.models import DeveloperProject
from apps.api_keys.models import APIKey
from apps.subscriptions.models import UserSubscription
from apps.usage_logs.models import UsageLog
from apps.notifications.models import Notification
from apps.notifications.services import NotificationWebSocketService

logger = logging.getLogger(__name__)


# @shared_task : This decorator tells Celery:
#                 "Register this function as a background task."
#                  Without it: just a normal python function
@shared_task
def say_hello():
    """
    First learning task for Celery.
    When executed:
    - Prints "Hello from Celery!" to stdout (visible in Celery worker terminal)
    - Writes a log message
    - Returns "Task Completed"
    """
    print("Hello from Celery!")
    logger.info("say_hello Celery task executed successfully.")
    return "Task Completed"


@shared_task
def generate_daily_report():
    """
    Celery background task that calculates and logs a platform daily summary report.
    Queries database models asynchronously and returns a dictionary of metrics.
    """
    now = timezone.now()
    today = now.date()

    total_apis = API.objects.filter(is_deleted=False).count()
    total_developers = User.objects.filter(role=User.Role.DEVELOPER, is_deleted=False).count()
    total_developer_projects = DeveloperProject.objects.filter(is_deleted=False).count()
    total_api_keys = APIKey.objects.filter(is_deleted=False).count()
    active_subscriptions = UserSubscription.objects.filter(
        status=UserSubscription.Status.ACTIVE,
        is_deleted=False,
    ).count()
    todays_api_requests = UsageLog.objects.filter(created_at__date=today).count()

    report_data = {
        "timestamp": now.isoformat(),
        "total_apis": total_apis,
        "total_developers": total_developers,
        "total_developer_projects": total_developer_projects,
        "total_api_keys": total_api_keys,
        "active_subscriptions": active_subscriptions,
        "todays_api_requests": todays_api_requests,
    }

    report_text = f"""
====================================================
               DAILY PLATFORM REPORT               
====================================================
Timestamp:                {report_data['timestamp']}
Total APIs:               {report_data['total_apis']}
Total Developers:         {report_data['total_developers']}
Total Developer Projects: {report_data['total_developer_projects']}
Total API Keys:           {report_data['total_api_keys']}
Active Subscriptions:     {report_data['active_subscriptions']}
Today's API Requests:     {report_data['todays_api_requests']}
====================================================
"""

    print(report_text)
    logger.info("Daily Platform Report generated: %s", report_data)

    return report_data


@shared_task
def check_subscription_reminders():
    """
    Celery background task that queries active subscriptions expiring in 3, 2, 1, or 0 days (today)
    and sends dynamic reminder notifications to developers via NotificationWebSocketService.
    """
    today = timezone.now().date()
    # Daily reminders for 3 days, 2 days, 1 day (tomorrow), and 0 days (today)
    reminder_days = [3, 2, 1, 0]

    processed_count = 0

    for days in reminder_days:
        target_date = today + timedelta(days=days)

        expiring_subscriptions = UserSubscription.objects.filter(
            status=UserSubscription.Status.ACTIVE,
            is_deleted=False,
            end_date__date=target_date,
        ).select_related("user", "plan")

        for subscription in expiring_subscriptions:
            developer = subscription.user

            # Skip invalid users or non-Developer users
            if not developer or developer.role != User.Role.DEVELOPER:
                continue

            # Construct dynamic title & message based on remaining days
            if days == 0:
                title = "Subscription Expires Today"
                message = f"Your {subscription.plan.name} subscription expires today. Please renew immediately to avoid service interruption."
            elif days == 1:
                title = "Subscription Expiring Tomorrow"
                message = f"Your {subscription.plan.name} subscription will expire tomorrow. Please renew your subscription to continue using APIHub services."
            else:
                title = "Subscription Expiring Soon"
                message = f"Your {subscription.plan.name} subscription will expire in {days} days. Please renew your subscription to continue using APIHub services."

            NotificationWebSocketService.send_developer_notification(
                user=developer,
                title=title,
                message=message,
                notification_type=Notification.NotificationType.SYSTEM,
                metadata={
                    "subscription_uuid": str(subscription.uuid),
                    "expires_on": str(subscription.end_date),
                    "days_remaining": days,
                },
            )

            processed_count += 1
            logger.info("Subscription reminder (%d days left) sent to %s", days, developer.email)

    logger.info("Subscription reminder task completed. Total reminders sent: %d", processed_count)

    return {"processed": processed_count}
