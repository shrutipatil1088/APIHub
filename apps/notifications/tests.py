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

from apps.notifications.routing import websocket_urlpatterns
from apps.accounts.models import User
from apps.api_catalog.models import API
from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.api_keys.models import APIKey
from apps.notifications.models import Notification
from apps.notifications.services import NotificationWebSocketService, NotificationService


class NotificationModelTests(APITestCase):
    """
    Unit tests for the Notification database model.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="notif_model@example.com",
            password="securepassword123",
            full_name="Model Test User",
            role=User.Role.DEVELOPER,
        )

    def test_notification_creation_and_defaults(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title="Test Title",
            message="Test Message",
            notification_type=Notification.NotificationType.SYSTEM,
            metadata={"test_key": "test_val"},
        )
        self.assertIsNotNone(notif.uuid)
        self.assertFalse(notif.is_read)
        self.assertFalse(notif.is_deleted)
        self.assertEqual(str(notif.notification_type), "SYSTEM")
        self.assertEqual(notif.metadata["test_key"], "test_val")

    def test_notification_soft_delete(self):
        notif = Notification.objects.create(
            recipient=self.user,
            title="Delete Title",
            message="Delete Message",
            notification_type=Notification.NotificationType.SYSTEM,
        )
        notif.soft_delete()
        self.assertTrue(notif.is_deleted)
        self.assertIsNotNone(notif.deleted_at)


class NotificationAPITests(APITestCase):
    """
    Integration tests for Notification REST API endpoints.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin_notif@example.com",
            password="securepassword123",
            full_name="Admin Notif User",
            role=User.Role.ADMIN,
        )
        self.dev_a = User.objects.create_user(
            email="deva_notif@example.com",
            password="securepassword123",
            full_name="Dev A Notif User",
            role=User.Role.DEVELOPER,
        )
        self.dev_b = User.objects.create_user(
            email="devb_notif@example.com",
            password="securepassword123",
            full_name="Dev B Notif User",
            role=User.Role.DEVELOPER,
        )

        # Admin notifications (recipient=None)
        self.admin_notif1 = Notification.objects.create(
            recipient=None,
            title="Admin Notif 1",
            message="Admin Message 1",
            notification_type=Notification.NotificationType.DEVELOPER_REGISTERED,
        )
        self.admin_notif2 = Notification.objects.create(
            recipient=None,
            title="Admin Notif 2",
            message="Admin Message 2",
            notification_type=Notification.NotificationType.API_PUBLISHED,
        )

        # Dev A notifications
        self.dev_a_notif1 = Notification.objects.create(
            recipient=self.dev_a,
            title="Dev A Notif 1",
            message="Dev A Message 1",
            notification_type=Notification.NotificationType.PROJECT_CREATED,
        )
        self.dev_a_notif2 = Notification.objects.create(
            recipient=self.dev_a,
            title="Dev A Notif 2",
            message="Dev A Message 2",
            notification_type=Notification.NotificationType.API_KEY_CREATED,
        )

        # Dev B notification
        self.dev_b_notif = Notification.objects.create(
            recipient=self.dev_b,
            title="Dev B Notif",
            message="Dev B Message",
            notification_type=Notification.NotificationType.SUBSCRIPTION_CREATED,
        )

    def test_list_notifications_developer_permissions(self):
        url = reverse("notification-list")
        self.client.force_authenticate(user=self.dev_a)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]
        self.assertEqual(len(results), 2)
        titles = [item["title"] for item in results]
        self.assertIn("Dev A Notif 1", titles)
        self.assertIn("Dev A Notif 2", titles)
        self.assertNotIn("Admin Notif 1", titles)
        self.assertNotIn("Dev B Notif", titles)

    def test_list_notifications_admin_permissions(self):
        url = reverse("notification-list")
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]
        self.assertEqual(len(results), 2)
        titles = [item["title"] for item in results]
        self.assertIn("Admin Notif 1", titles)
        self.assertIn("Admin Notif 2", titles)
        self.assertNotIn("Dev A Notif 1", titles)

    def test_mark_single_notification_read(self):
        url = reverse("notification-mark-read", kwargs={"uuid": self.dev_a_notif1.uuid})
        self.client.force_authenticate(user=self.dev_a)
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["is_read"])
        self.dev_a_notif1.refresh_from_db()
        self.assertTrue(self.dev_a_notif1.is_read)

    def test_mark_single_notification_read_forbidden(self):
        url = reverse("notification-mark-read", kwargs={"uuid": self.dev_a_notif1.uuid})
        self.client.force_authenticate(user=self.dev_b)
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mark_all_notifications_read(self):
        url = reverse("notification-read-all")
        self.client.force_authenticate(user=self.dev_a)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["marked_read_count"], 2)

        self.dev_a_notif1.refresh_from_db()
        self.dev_a_notif2.refresh_from_db()
        self.assertTrue(self.dev_a_notif1.is_read)
        self.assertTrue(self.dev_a_notif2.is_read)

    def test_unread_count_endpoint(self):
        url = reverse("notification-unread-count")
        self.client.force_authenticate(user=self.dev_a)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["unread_count"], 2)

    def test_soft_delete_notification(self):
        url = reverse("notification-detail-delete", kwargs={"uuid": self.dev_a_notif1.uuid})
        self.client.force_authenticate(user=self.dev_a)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dev_a_notif1.refresh_from_db()
        self.assertTrue(self.dev_a_notif1.is_deleted)


class NotificationSignalTests(APITestCase):
    """
    Integration tests for signal-triggered real-time notifications across apps.
    """

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin_sig_n@example.com",
            password="securepassword123",
            full_name="Admin Sig N",
            role=User.Role.ADMIN,
        )
        self.dev = User.objects.create_user(
            email="dev_sig_n@example.com",
            password="securepassword123",
            full_name="Dev Sig N",
            role=User.Role.DEVELOPER,
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Notif Plan",
            description="Notif plan desc",
            price=15.00,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=500,
            is_active=True,
        )

    def test_developer_registered_signal_creates_admin_notification(self):
        with self.captureOnCommitCallbacks(execute=True):
            User.objects.create_user(
                email="new_dev_n@example.com",
                password="securepassword123",
                full_name="New Dev N",
                role=User.Role.DEVELOPER,
            )
        notif = Notification.objects.filter(
            notification_type=Notification.NotificationType.DEVELOPER_REGISTERED
        ).first()
        self.assertIsNotNone(notif)
        self.assertIsNone(notif.recipient)
        self.assertIn("New Developer Registered", notif.title)

    def test_api_published_signal_creates_admin_notification(self):
        with self.captureOnCommitCallbacks(execute=True):
            API.objects.create(
                name="Notif Published API",
                slug="notif-published-api",
                description="API catalog description meeting minimum requirements for test.",
                status=API.Status.PUBLISHED,
                created_by=self.admin,
            )
        notif = Notification.objects.filter(
            notification_type=Notification.NotificationType.API_PUBLISHED
        ).first()
        self.assertIsNotNone(notif)
        self.assertIsNone(notif.recipient)
        self.assertIn("New API Published", notif.title)

    def test_project_created_signal_creates_admin_and_developer_notifications(self):
        with self.captureOnCommitCallbacks(execute=True):
            DeveloperProject.objects.create(
                developer=self.dev,
                name="Notif Project",
                description="Project created for notification test",
            )
        admin_notif = Notification.objects.filter(
            recipient__isnull=True,
            notification_type=Notification.NotificationType.PROJECT_CREATED,
        ).first()
        dev_notif = Notification.objects.filter(
            recipient=self.dev,
            notification_type=Notification.NotificationType.PROJECT_CREATED,
        ).first()

        self.assertIsNotNone(admin_notif)
        self.assertIsNotNone(dev_notif)

    def test_api_key_created_signal_creates_admin_and_developer_notifications(self):
        sub = UserSubscription.objects.create(
            user=self.dev,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            status=UserSubscription.Status.ACTIVE,
        )
        proj = DeveloperProject.objects.create(
            developer=self.dev,
            name="Key Notif Project",
            description="Project created for key notif test",
        )
        with self.captureOnCommitCallbacks(execute=True):
            APIKey.objects.create(
                project=proj,
                subscription=sub,
                name="Notif Key",
                key_hash=hashlib.sha256(b"notif_key_secret").hexdigest(),
                expires_at=sub.end_date,
                is_active=True,
            )
        dev_notif = Notification.objects.filter(
            recipient=self.dev,
            notification_type=Notification.NotificationType.API_KEY_CREATED,
        ).first()
        self.assertIsNotNone(dev_notif)

    def test_subscription_created_signal_creates_admin_and_developer_notifications(self):
        with self.captureOnCommitCallbacks(execute=True):
            UserSubscription.objects.create(
                user=self.dev,
                plan=self.plan,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=30),
                status=UserSubscription.Status.ACTIVE,
            )
        dev_notif = Notification.objects.filter(
            recipient=self.dev,
            notification_type=Notification.NotificationType.SUBSCRIPTION_CREATED,
        ).first()
        self.assertIsNotNone(dev_notif)

    def test_subscription_plan_created_signal_creates_admin_notification(self):
        with self.captureOnCommitCallbacks(execute=True):
            SubscriptionPlan.objects.create(
                name="New Plan Signal Test",
                description="Test plan description",
                price=29.99,
                billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
                request_limit=1000,
                is_active=True,
            )
        admin_notif = Notification.objects.filter(
            recipient__isnull=True,
            title="Subscription Plan Created",
        ).first()
        self.assertIsNotNone(admin_notif)
        self.assertIn("New Plan Signal Test", admin_notif.message)


class NotificationWebSocketTests(APITransactionTestCase):
    """
    WebSocket notification delivery tests using APITransactionTestCase.
    """

    async def test_websocket_unauthenticated_connection_rejected(self):
        await sync_to_async(connections.close_all)()
        router = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(router, "/ws/notifications/")
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

    async def test_websocket_admin_joins_notifications_admin_and_receives_broadcast(self):
        await sync_to_async(connections.close_all)()
        admin_user = await sync_to_async(User.objects.create_user)(
            email="admin_ws_notif@example.com",
            password="securepassword123",
            full_name="Admin WS Notif User",
            role=User.Role.ADMIN,
        )

        router = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(router, "/ws/notifications/")
        communicator.scope["user"] = admin_user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Trigger admin notification
        await sync_to_async(NotificationWebSocketService.send_admin_notification)(
            title="WS Admin Test Title",
            message="WS Admin Test Message",
            notification_type=Notification.NotificationType.SYSTEM,
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response["event"], "notification_created")
        self.assertEqual(response["notification"]["title"], "WS Admin Test Title")
        self.assertEqual(response["notification"]["message"], "WS Admin Test Message")

        await communicator.disconnect()

    async def test_websocket_developer_joins_user_group_and_receives_broadcast(self):
        await sync_to_async(connections.close_all)()
        dev_user = await sync_to_async(User.objects.create_user)(
            email="dev_ws_notif@example.com",
            password="securepassword123",
            full_name="Dev WS Notif User",
            role=User.Role.DEVELOPER,
        )

        router = URLRouter(websocket_urlpatterns)
        communicator = WebsocketCommunicator(router, "/ws/notifications/")
        communicator.scope["user"] = dev_user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Trigger developer notification
        await sync_to_async(NotificationWebSocketService.send_developer_notification)(
            user=dev_user,
            title="WS Dev Test Title",
            message="WS Dev Test Message",
            notification_type=Notification.NotificationType.SYSTEM,
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response["event"], "notification_created")
        self.assertEqual(response["notification"]["title"], "WS Dev Test Title")

        await communicator.disconnect()

    async def test_websocket_developer_a_does_not_receive_developer_b_notification(self):
        await sync_to_async(connections.close_all)()
        dev_a = await sync_to_async(User.objects.create_user)(
            email="deva_ws_notif@example.com",
            password="securepassword123",
            full_name="Dev A WS Notif User",
            role=User.Role.DEVELOPER,
        )
        dev_b = await sync_to_async(User.objects.create_user)(
            email="devb_ws_notif@example.com",
            password="securepassword123",
            full_name="Dev B WS Notif User",
            role=User.Role.DEVELOPER,
        )

        router = URLRouter(websocket_urlpatterns)
        communicator_a = WebsocketCommunicator(router, "/ws/notifications/")
        communicator_a.scope["user"] = dev_a
        connected_a, _ = await communicator_a.connect()
        self.assertTrue(connected_a)

        # Trigger notification for Developer B
        await sync_to_async(NotificationWebSocketService.send_developer_notification)(
            user=dev_b,
            title="WS Dev B Only Title",
            message="WS Dev B Only Message",
            notification_type=Notification.NotificationType.SYSTEM,
        )

        # Developer A should NOT receive Developer B's notification
        self.assertTrue(await communicator_a.receive_nothing())

        await communicator_a.disconnect()
