import hashlib
from unittest.mock import patch
from django.db import connections
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from asgiref.sync import sync_to_async

from apps.dashboard.routing import websocket_urlpatterns
from apps.accounts.models import User
from apps.api_catalog.models import API, APIVersion, Endpoint
from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.api_keys.models import APIKey
from apps.usage_logs.models import UsageLog
from apps.dashboard.services import DashboardWebSocketService, DashboardService


class DashboardAPITests(APITestCase):
    """
    Integration tests for Admin and Developer Dashboard REST endpoints.
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


class DashboardSignalBroadcastingTests(APITestCase):
    """
    Tests that business event signals trigger targeted broadcast calls
    on DashboardWebSocketService.
    """

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email="admin_sig@example.com",
            password="securepassword123",
            full_name="Admin Signal User",
            role=User.Role.ADMIN,
        )
        self.dev_user = User.objects.create_user(
            email="dev_sig@example.com",
            password="securepassword123",
            full_name="Dev Signal User",
            role=User.Role.DEVELOPER,
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Sig Plan",
            description="Plan for signal test",
            price=10.00,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=100,
            is_active=True,
        )

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    @patch.object(DashboardWebSocketService, "broadcast_developer_dashboard_update")
    def test_developer_user_created_triggers_admin_broadcast_only(self, mock_dev_broadcast, mock_admin_broadcast):
        with self.captureOnCommitCallbacks(execute=True):
            User.objects.create_user(
                email="new_dev_sig@example.com",
                password="securepassword123",
                full_name="New Dev Signal User",
                role=User.Role.DEVELOPER,
            )
        mock_admin_broadcast.assert_called_once()
        mock_dev_broadcast.assert_not_called()

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    @patch.object(DashboardWebSocketService, "broadcast_developer_dashboard_update")
    def test_developer_project_created_triggers_both_broadcasts(self, mock_dev_broadcast, mock_admin_broadcast):
        with self.captureOnCommitCallbacks(execute=True):
            DeveloperProject.objects.create(
                developer=self.dev_user,
                name="Signal Project",
                description="Project created for signal test",
            )
        mock_admin_broadcast.assert_called_once()
        mock_dev_broadcast.assert_called_once_with(self.dev_user)

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    @patch.object(DashboardWebSocketService, "broadcast_developer_dashboard_update")
    def test_user_subscription_created_triggers_both_broadcasts(self, mock_dev_broadcast, mock_admin_broadcast):
        with self.captureOnCommitCallbacks(execute=True):
            UserSubscription.objects.create(
                user=self.dev_user,
                plan=self.plan,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                status=UserSubscription.Status.ACTIVE,
            )
        mock_admin_broadcast.assert_called_once()
        mock_dev_broadcast.assert_called_once_with(self.dev_user)

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    @patch.object(DashboardWebSocketService, "broadcast_developer_dashboard_update")
    def test_api_key_created_triggers_both_broadcasts(self, mock_dev_broadcast, mock_admin_broadcast):
        sub = UserSubscription.objects.create(
            user=self.dev_user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            status=UserSubscription.Status.ACTIVE,
        )
        proj = DeveloperProject.objects.create(
            developer=self.dev_user,
            name="Key Signal Project",
            description="Project created for key signal test",
        )
        with self.captureOnCommitCallbacks(execute=True):
            APIKey.objects.create(
                project=proj,
                subscription=sub,
                name="Signal Key",
                key_hash=hashlib.sha256(b"signal_key_secret").hexdigest(),
                expires_at=sub.end_date,
                is_active=True,
            )
        mock_admin_broadcast.assert_called()
        mock_dev_broadcast.assert_called_with(self.dev_user)

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    @patch.object(DashboardWebSocketService, "broadcast_developer_dashboard_update")
    def test_usage_log_created_triggers_both_broadcasts(self, mock_dev_broadcast, mock_admin_broadcast):
        sub = UserSubscription.objects.create(
            user=self.dev_user,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            status=UserSubscription.Status.ACTIVE,
        )
        proj = DeveloperProject.objects.create(
            developer=self.dev_user,
            name="Log Signal Project",
            description="Project created for log signal test",
        )
        key = APIKey.objects.create(
            project=proj,
            subscription=sub,
            name="Log Signal Key",
            key_hash=hashlib.sha256(b"log_key_secret").hexdigest(),
            expires_at=sub.end_date,
            is_active=True,
        )
        with self.captureOnCommitCallbacks(execute=True):
            UsageLog.objects.create(
                project=proj,
                api_key=key,
                endpoint="/test/signal",
                method="GET",
                status_code=200,
                response_time_ms=50,
            )
        mock_admin_broadcast.assert_called_once()
        mock_dev_broadcast.assert_called_once_with(self.dev_user)

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    @patch.object(DashboardWebSocketService, "broadcast_developer_dashboard_update")
    def test_published_api_created_triggers_admin_broadcast_only(self, mock_dev_broadcast, mock_admin_broadcast):
        with self.captureOnCommitCallbacks(execute=True):
            API.objects.create(
                name="Signal API",
                slug="signal-api",
                description="API description meeting minimum requirements for test.",
                status=API.Status.PUBLISHED,
                created_by=self.admin_user,
            )
        mock_admin_broadcast.assert_called_once()
        mock_dev_broadcast.assert_not_called()

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    def test_api_version_created_triggers_admin_broadcast(self, mock_admin_broadcast):
        api_obj = API.objects.create(
            name="Version Test API",
            slug="version-test-api",
            description="API description meeting minimum requirements.",
            status=API.Status.PUBLISHED,
            created_by=self.admin_user,
        )
        with self.captureOnCommitCallbacks(execute=True):
            APIVersion.objects.create(
                api=api_obj,
                version="v2.0",
            )
        mock_admin_broadcast.assert_called()

    @patch.object(DashboardWebSocketService, "broadcast_admin_dashboard_update")
    def test_endpoint_created_triggers_admin_broadcast(self, mock_admin_broadcast):
        api_obj = API.objects.create(
            name="Endpoint Test API",
            slug="endpoint-test-api",
            description="API description meeting minimum requirements.",
            status=API.Status.PUBLISHED,
            created_by=self.admin_user,
        )
        version_obj = APIVersion.objects.create(
            api=api_obj,
            version="v1.0",
        )
        with self.captureOnCommitCallbacks(execute=True):
            Endpoint.objects.create(
                version=version_obj,
                path="/test-api/v1/endpoint",
                method=Endpoint.Method.POST,
                summary="New Endpoint Test",
            )
        mock_admin_broadcast.assert_called()


class DashboardWebSocketTests(APITransactionTestCase):
    """
    WebSocket and real-time broadcasting tests for Dashboard module using APITransactionTestCase.
    """

    async def test_websocket_unauthenticated_connection_rejected(self):
        router = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(router, "/ws/dashboard/")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

    async def test_websocket_admin_joins_admin_group_and_receives_broadcast(self):
        admin_user = await sync_to_async(User.objects.create_user)(
            email="admin_ws_test@example.com",
            password="securepassword123",
            full_name="Admin WS User",
            role=User.Role.ADMIN,
        )

        router = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(router, "/ws/dashboard/")
        communicator.scope["user"] = admin_user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Trigger admin broadcast
        await sync_to_async(DashboardWebSocketService.broadcast_admin_dashboard_update)()

        response = await communicator.receive_json_from()
        self.assertEqual(response["event"], "admin_dashboard_update")
        self.assertIn("today_requests", response["data"])
        self.assertIn("total_developers", response["data"])
        self.assertIn("total_projects", response["data"])

        await communicator.disconnect()

    async def test_websocket_developer_joins_developer_group_and_receives_broadcast(self):
        dev_user = await sync_to_async(User.objects.create_user)(
            email="dev_ws_test@example.com",
            password="securepassword123",
            full_name="Dev WS User",
            role=User.Role.DEVELOPER,
        )

        router = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(router, "/ws/dashboard/")
        communicator.scope["user"] = dev_user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Trigger developer broadcast for this user
        await sync_to_async(DashboardWebSocketService.broadcast_developer_dashboard_update)(dev_user)

        response = await communicator.receive_json_from()
        self.assertEqual(response["event"], "developer_dashboard_update")
        self.assertIn("my_projects", response["data"])
        self.assertIn("my_api_keys", response["data"])
        self.assertIn("my_requests_today", response["data"])

        await communicator.disconnect()

    async def test_websocket_developer_a_does_not_receive_developer_b_broadcast(self):
        dev_a = await sync_to_async(User.objects.create_user)(
            email="deva_ws_test@example.com",
            password="securepassword123",
            full_name="Dev A WS User",
            role=User.Role.DEVELOPER,
        )
        dev_b = await sync_to_async(User.objects.create_user)(
            email="devb_ws_test@example.com",
            password="securepassword123",
            full_name="Dev B WS User",
            role=User.Role.DEVELOPER,
        )

        router = URLRouter(websocket_urlpatterns)
        communicator_a = WebsocketCommunicator(router, "/ws/dashboard/")
        communicator_a.scope["user"] = dev_a
        connected_a, _ = await communicator_a.connect()
        self.assertTrue(connected_a)

        # Trigger broadcast for Developer B
        await sync_to_async(DashboardWebSocketService.broadcast_developer_dashboard_update)(dev_b)

        # Developer A should NOT receive Developer B's update (receive times out)
        self.assertTrue(await communicator_a.receive_nothing())

        await communicator_a.disconnect()
