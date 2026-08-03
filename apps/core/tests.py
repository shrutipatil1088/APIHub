from unittest.mock import patch
from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.api_catalog.models import API
from apps.developer_projects.models import DeveloperProject
from apps.core.tasks import say_hello, generate_daily_report


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
