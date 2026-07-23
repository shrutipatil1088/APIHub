import hashlib
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.api_keys.models import APIKey
from apps.usage_logs.models import UsageLog


class UsageLogAPITests(APITestCase):
    """
    Integration tests for UsageLog read APIs and filter rules.
    """

    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="securepassword123",
            full_name="Admin User",
            role=User.Role.ADMIN,
        )
        self.dev_user1 = User.objects.create_user(
            email="dev1@example.com",
            password="securepassword123",
            full_name="Developer One",
            role=User.Role.DEVELOPER,
        )
        self.dev_user2 = User.objects.create_user(
            email="dev2@example.com",
            password="securepassword123",
            full_name="Developer Two",
            role=User.Role.DEVELOPER,
        )

        # Create plan & active subscription for dev_user1
        self.plan = SubscriptionPlan.objects.create(
            name="Pro Developer Plan",
            description="Professional tier with unlimited requests.",
            price=29.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=10000,
        )
        self.subscription1 = UserSubscription.objects.create(
            user=self.dev_user1,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            status=UserSubscription.Status.ACTIVE,
        )

        # Create developer projects
        self.project1 = DeveloperProject.objects.create(
            developer=self.dev_user1,
            name="Weather API Service",
            description="High precision weather data delivery service for developers.",
        )
        self.project2 = DeveloperProject.objects.create(
            developer=self.dev_user2,
            name="Analytics Engine",
            description="Real-time analytics engine and dashboard backend service.",
        )

        # Create API key for dev_user1
        self.api_key1 = APIKey.objects.create(
            project=self.project1,
            subscription=self.subscription1,
            name="Production Key",
            key_hash=hashlib.sha256(b"dummy_plain_key").hexdigest(),
            expires_at=self.subscription1.end_date,
            is_active=True,
        )

        # Create initial usage logs
        self.log1 = UsageLog.objects.create(
            project=self.project1,
            api_key=self.api_key1,
            endpoint="/api/v1/weather/current",
            method="GET",
            status_code=200,
            response_time_ms=120,
            ip_address="192.168.1.1",
            user_agent="PostmanRuntime/7.29.0",
        )
        self.log2 = UsageLog.objects.create(
            project=self.project2,
            endpoint="/api/v1/analytics/events",
            method="POST",
            status_code=201,
            response_time_ms=250,
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0",
        )

    def test_list_usage_logs_ownership(self):
        url = reverse("usage-log-list")

        # Developer 1 list sees only log1
        self.client.force_authenticate(user=self.dev_user1)
        response_dev1 = self.client.get(url)
        self.assertEqual(response_dev1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_dev1.data["data"]), 1)
        self.assertEqual(response_dev1.data["data"][0]["uuid"], str(self.log1.uuid))

        # Admin list sees both logs
        self.client.force_authenticate(user=self.admin_user)
        response_admin = self.client.get(url)
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_admin.data["data"]), 2)

    def test_filter_usage_logs_by_endpoint(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("usage-log-list")

        response = self.client.get(f"{url}?search=weather")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["endpoint"], "/api/v1/weather/current")

    def test_filter_usage_logs_by_status_code_and_method(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("usage-log-list")

        response = self.client.get(f"{url}?status_code=201&method=POST")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["uuid"], str(self.log2.uuid))

    def test_filter_usage_logs_by_project_and_api_key(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("usage-log-list")

        response = self.client.get(f"{url}?project={self.project1.uuid}&api_key={self.api_key1.uuid}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["uuid"], str(self.log1.uuid))

    def test_retrieve_usage_log_owner_or_admin(self):
        detail_url = reverse("usage-log-detail", kwargs={"uuid": self.log1.uuid})

        # Non-owner developer retrieve fails (403)
        self.client.force_authenticate(user=self.dev_user2)
        res_forbidden = self.client.get(detail_url)
        self.assertEqual(res_forbidden.status_code, status.HTTP_403_FORBIDDEN)

        # Owner retrieve succeeds
        self.client.force_authenticate(user=self.dev_user1)
        res_owner = self.client.get(detail_url)
        self.assertEqual(res_owner.status_code, status.HTTP_200_OK)
        self.assertEqual(res_owner.data["data"]["endpoint"], "/api/v1/weather/current")

        # Admin retrieve succeeds
        self.client.force_authenticate(user=self.admin_user)
        res_admin = self.client.get(detail_url)
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)

    def test_invalid_ordering_field_fails(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("usage-log-list")

        response = self.client.get(f"{url}?ordering=invalid_field")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ordering", response.data.get("errors", {}))
