import hashlib
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.api_catalog.models import API, APIVersion, Endpoint
from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.api_keys.models import APIKey
from apps.usage_logs.models import UsageLog


class DashboardAPITests(APITestCase):
    """
    Integration tests for Admin and Developer Dashboard endpoints.
    """

    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin_dash@example.com",
            password="securepassword123",
            full_name="Admin Dashboard User",
            role=User.Role.ADMIN,
        )

        # Create developer user
        self.dev_user = User.objects.create_user(
            email="dev_dash@example.com",
            password="securepassword123",
            full_name="Developer Dashboard User",
            role=User.Role.DEVELOPER,
        )

        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name="Pro Plan",
            description="Professional plan with 10,000 requests limit.",
            price=29.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=10000,
            is_active=True,
        )

        # Create user subscription
        self.subscription = UserSubscription.objects.create(
            user=self.dev_user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            status=UserSubscription.Status.ACTIVE,
        )

        # Create developer project
        self.project = DeveloperProject.objects.create(
            developer=self.dev_user,
            name="Dashboard Test Project",
            description="Project created for testing dashboard analytics.",
        )

        # Create API key
        self.api_key = APIKey.objects.create(
            project=self.project,
            subscription=self.subscription,
            name="Dashboard Test Key",
            key_hash=hashlib.sha256(b"dash_key_secret").hexdigest(),
            expires_at=self.subscription.end_date,
            is_active=True,
        )

        # Create sample catalog items
        self.api_obj = API.objects.create(
            name="Catalog Test API",
            slug="catalog-test-api",
            description="API catalog item description meeting minimum length requirements.",
            status=API.Status.PUBLISHED,
            created_by=self.admin_user,
        )
        self.version_obj = APIVersion.objects.create(
            api=self.api_obj,
            version="v1.0",
        )
        self.endpoint_obj = Endpoint.objects.create(
            version=self.version_obj,
            path="/test-api/v1/resource",
            method=Endpoint.Method.GET,
            summary="Test Endpoint",
        )

        # Create sample usage logs
        self.log1 = UsageLog.objects.create(
            project=self.project,
            api_key=self.api_key,
            endpoint="/test-api/v1/resource",
            method="GET",
            status_code=200,
            response_time_ms=75,
        )

    def test_admin_dashboard_access_and_metrics(self):
        url = reverse("dashboard-admin")

        # Admin user request succeeds
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        data = response.data["data"]
        self.assertEqual(data["total_apis"], 1)
        self.assertEqual(data["total_api_versions"], 1)
        self.assertEqual(data["total_endpoints"], 1)
        self.assertEqual(data["total_developers"], 1)
        self.assertEqual(data["total_projects"], 1)
        self.assertEqual(data["total_api_keys"], 1)
        self.assertEqual(data["active_subscriptions"], 1)
        self.assertEqual(data["today_requests"], 1)
        self.assertEqual(data["this_month_requests"], 1)

    def test_admin_dashboard_developer_forbidden(self):
        url = reverse("dashboard-admin")

        # Developer user request fails with 403 Forbidden
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_developer_dashboard_access_and_metrics(self):
        url = reverse("dashboard-developer")

        # Developer user request succeeds
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

        data = response.data["data"]
        self.assertEqual(data["my_projects"], 1)
        self.assertEqual(data["my_api_keys"], 1)
        self.assertEqual(data["my_requests_today"], 1)
        self.assertEqual(data["my_requests_this_month"], 1)
        self.assertIsNotNone(data["current_subscription"])
        self.assertEqual(data["current_subscription"]["plan"], "Pro Plan")
        self.assertEqual(data["current_subscription"]["status"], "ACTIVE")
        self.assertEqual(data["remaining_requests"], 9999)

    def test_developer_dashboard_admin_forbidden(self):
        url = reverse("dashboard-developer")

        # Admin user request fails with 403 Forbidden
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_developer_dashboard_unlimited_plan_remaining_requests_null(self):
        # Update plan to unlimited (Enterprise)
        self.plan.request_limit = 0
        self.plan.name = "Enterprise Unlimited Plan"
        self.plan.save()

        url = reverse("dashboard-developer")
        self.client.force_authenticate(user=self.dev_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertIsNone(data["remaining_requests"])
