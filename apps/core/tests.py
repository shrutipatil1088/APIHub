from unittest.mock import patch
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.api_catalog.models import API
from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.usage_logs.models import UsageLog
from apps.notifications.models import Notification
from apps.core.tasks import (
    say_hello,
    generate_daily_report,
    check_subscription_reminders,
    delete_old_usage_logs,
)


class HealthCheckAPITests(APITestCase):
    """
    Integration tests for the Health Check API endpoint and Redis caching.
    """

    def test_health_check_endpoint(self):
        url = reverse("health-check")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("service", response.data)
        self.assertIn("version", response.data)
        self.assertIn("database", response.data)
        self.assertIn("redis", response.data)
        self.assertEqual(response.data["service"], "APIHub")

    def test_redis_cache_operations(self):
        cache.set("test_key", "test_value", timeout=10)
        self.assertEqual(cache.get("test_key"), "test_value")
        cache.delete("test_key")
        self.assertIsNone(cache.get("test_key"))


class CeleryTaskTests(APITestCase):
    """
    Unit tests for learning Celery tasks and endpoints.
    """

    def test_say_hello_task(self):
        result = say_hello()
        self.assertEqual(result, "Task Completed")

    @patch("apps.core.views.say_hello.delay")
    def test_test_celery_endpoint(self, mock_delay):
        url = reverse("test-celery")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Task queued successfully.")
        mock_delay.assert_called_once()

    def test_generate_daily_report_task_execution(self):
        # Create test records
        admin = User.objects.create_user(
            email="report_admin@example.com",
            password="securepassword123",
            full_name="Report Admin",
            role=User.Role.ADMIN,
        )
        dev = User.objects.create_user(
            email="report_dev@example.com",
            password="securepassword123",
            full_name="Report Dev",
            role=User.Role.DEVELOPER,
        )
        API.objects.create(
            name="Report Test API",
            slug="report-test-api",
            description="API description for daily report test.",
            created_by=admin,
        )
        DeveloperProject.objects.create(
            developer=dev,
            name="Report Project",
            description="Project created for daily report test",
        )

        result = generate_daily_report()

        self.assertIn("timestamp", result)
        self.assertIn("total_apis", result)
        self.assertIn("total_developers", result)
        self.assertIn("total_developer_projects", result)
        self.assertIn("total_api_keys", result)
        self.assertIn("active_subscriptions", result)
        self.assertIn("todays_api_requests", result)
        self.assertGreaterEqual(result["total_apis"], 1)
        self.assertGreaterEqual(result["total_developers"], 1)
        self.assertGreaterEqual(result["total_developer_projects"], 1)

    @patch("apps.core.views.generate_daily_report.delay")
    def test_generate_daily_report_endpoint(self, mock_delay):
        url = reverse("generate-daily-report")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Daily report task queued successfully.")
        mock_delay.assert_called_once()

    def test_check_subscription_reminders_task_execution(self):
        dev = User.objects.create_user(
            email="reminder_dev@example.com",
            password="securepassword123",
            full_name="Reminder Dev",
            role=User.Role.DEVELOPER,
        )
        plan = SubscriptionPlan.objects.create(
            name="Reminder Plan",
            description="Plan for reminder test",
            price=29.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=1000,
            is_active=True,
        )
        
        # Subscriptions expiring in 3, 2, 1, and 0 days
        for days in [3, 2, 1, 0]:
            UserSubscription.objects.create(
                user=dev,
                plan=plan,
                start_date=timezone.now() - timedelta(days=27),
                end_date=timezone.now() + timedelta(days=days),
                status=UserSubscription.Status.ACTIVE,
            )

        result = check_subscription_reminders()

        self.assertEqual(result["processed"], 4)

        notifs = Notification.objects.filter(recipient=dev)
        self.assertEqual(notifs.count(), 4)

        titles = list(notifs.values_list("title", flat=True))
        self.assertIn("Subscription Expiring Soon", titles)
        self.assertIn("Subscription Expiring Tomorrow", titles)
        self.assertIn("Subscription Expires Today", titles)

    @patch("apps.core.views.check_subscription_reminders.delay")
    def test_subscription_reminder_endpoint(self, mock_delay):
        url = reverse("subscription-reminder")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Subscription reminder task queued successfully.")
        mock_delay.assert_called_once()

    def test_delete_old_usage_logs_task_execution(self):
        dev = User.objects.create_user(
            email="log_cleanup_dev@example.com",
            password="securepassword123",
            full_name="Log Dev",
            role=User.Role.DEVELOPER,
        )
        project = DeveloperProject.objects.create(
            developer=dev,
            name="Log Cleanup Project",
            description="Project for testing log cleanup task",
        )

        # Create recent log (created_at = now)
        recent_log = UsageLog.objects.create(
            project=project,
            endpoint="/api/v1/test/",
            method="GET",
            status_code=200,
            response_time_ms=50,
        )

        # Create old log (>90 days old)
        old_log = UsageLog.objects.create(
            project=project,
            endpoint="/api/v1/old-test/",
            method="POST",
            status_code=201,
            response_time_ms=120,
        )
        # Update created_at timestamp to 95 days ago
        old_date = timezone.now() - timedelta(days=95)
        UsageLog.objects.filter(id=old_log.id).update(created_at=old_date)

        result = delete_old_usage_logs()

        self.assertEqual(result["deleted_count"], 1)

        # Verify old log is deleted and recent log still exists
        self.assertFalse(UsageLog.objects.filter(id=old_log.id).exists())
        self.assertTrue(UsageLog.objects.filter(id=recent_log.id).exists())

    @patch("apps.core.views.delete_old_usage_logs.delay")
    def test_delete_old_usage_logs_endpoint(self, mock_delay):
        url = reverse("delete-old-logs")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            "Old usage log cleanup task queued successfully.",
        )
        mock_delay.assert_called_once()
