import hashlib
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.developer_projects.models import DeveloperProject
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.api_keys.models import APIKey


class APIKeyAPITests(APITestCase):
    """
    Integration tests for APIKey module APIs and business rules.
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

        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name="Pro Developer Plan",
            description="Professional tier with unlimited requests.",
            price=29.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=10000,
        )

        # Active subscription for dev_user1
        self.subscription1 = UserSubscription.objects.create(
            user=self.dev_user1,
            plan=self.plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            status=UserSubscription.Status.ACTIVE,
        )

        # Precreate developer projects
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

    def test_generate_api_key_success(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("api-key-list-create")

        response = self.client.post(
            url,
            {
                "name": "Production Key",
                "project": str(self.project1.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        data = response.data["data"]
        self.assertIn("api_key", data)
        self.assertTrue(data["api_key"].startswith("pk_live_"))

        key_data = data["key"]
        self.assertEqual(key_data["name"], "Production Key")
        self.assertEqual(key_data["project"]["uuid"], str(self.project1.uuid))
        self.assertNotIn("key_hash", key_data)

        # Verify DB record
        api_key_obj = APIKey.objects.get(uuid=key_data["uuid"])
        self.assertNotEqual(api_key_obj.key_hash, data["api_key"])
        expected_hash = hashlib.sha256(data["api_key"].encode("utf-8")).hexdigest()
        self.assertEqual(api_key_obj.key_hash, expected_hash)
        self.assertEqual(api_key_obj.expires_at, self.subscription1.end_date)

    def test_generate_api_key_requires_developer_role(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("api-key-list-create")

        response = self.client.post(
            url,
            {
                "name": "Admin Key Attempt",
                "project": str(self.project1.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_generate_api_key_requires_own_project(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("api-key-list-create")

        # dev_user1 attempts to create key for dev_user2's project
        response = self.client.post(
            url,
            {
                "name": "Unauthorized Key",
                "project": str(self.project2.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_api_key_without_active_subscription_fails(self):
        # dev_user2 has no active subscription
        self.client.force_authenticate(user=self.dev_user2)
        url = reverse("api-key-list-create")

        response = self.client.post(
            url,
            {
                "name": "No Sub Key",
                "project": str(self.project2.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_generate_api_key_expired_subscription_fails(self):
        # Create expired subscription marked ACTIVE for dev_user2
        UserSubscription.objects.create(
            user=self.dev_user2,
            plan=self.plan,
            start_date=timezone.now() - timezone.timedelta(days=60),
            end_date=timezone.now() - timezone.timedelta(days=1),
            status=UserSubscription.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.dev_user2)
        url = reverse("api-key-list-create")

        response = self.client.post(
            url,
            {
                "name": "Expired Sub Key",
                "project": str(self.project2.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_api_keys_ownership_and_admin(self):
        # Create key for dev_user1
        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        self.client.post(
            create_url,
            {
                "name": "Dev 1 Key",
                "project": str(self.project1.uuid),
            },
            format="json",
        )

        # Developer 1 list
        response_dev = self.client.get(create_url)
        self.assertEqual(response_dev.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_dev.data["data"]), 1)

        # Developer 2 list (no keys)
        self.client.force_authenticate(user=self.dev_user2)
        response_dev2 = self.client.get(create_url)
        self.assertEqual(response_dev2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_dev2.data["data"]), 0)

        # Admin list (sees dev 1 key)
        self.client.force_authenticate(user=self.admin_user)
        response_admin = self.client.get(create_url)
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_admin.data["data"]), 1)

    def test_retrieve_api_key_detail(self):
        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        res = self.client.post(
            create_url,
            {
                "name": "Detail Key",
                "project": str(self.project1.uuid),
            },
            format="json",
        )
        key_uuid = res.data["data"]["key"]["uuid"]

        detail_url = reverse("api-key-detail", kwargs={"uuid": key_uuid})

        # Owner retrieve
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Detail Key")
        self.assertNotIn("key_hash", response.data["data"])
        self.assertNotIn("api_key", response.data["data"])

        # Non-owner retrieve fails
        self.client.force_authenticate(user=self.dev_user2)
        response_forbidden = self.client.get(detail_url)
        self.assertEqual(response_forbidden.status_code, status.HTTP_403_FORBIDDEN)

    def test_rename_api_key(self):
        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        res = self.client.post(
            create_url,
            {
                "name": "Old Key Name",
                "project": str(self.project1.uuid),
            },
            format="json",
        )
        key_uuid = res.data["data"]["key"]["uuid"]

        detail_url = reverse("api-key-detail", kwargs={"uuid": key_uuid})
        response = self.client.patch(
            detail_url,
            {"name": "Renamed Key Name"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Renamed Key Name")

    def test_deactivate_api_key(self):
        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        res = self.client.post(
            create_url,
            {
                "name": "Key To Deactivate",
                "project": str(self.project1.uuid),
            },
            format="json",
        )
        key_uuid = res.data["data"]["key"]["uuid"]

        detail_url = reverse("api-key-detail", kwargs={"uuid": key_uuid})
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        key_obj = APIKey.objects.get(uuid=key_uuid)
        self.assertFalse(key_obj.is_active)

    def test_regenerate_api_key(self):
        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        res = self.client.post(
            create_url,
            {
                "name": "Key To Regenerate",
                "project": str(self.project1.uuid),
            },
            format="json",
        )
        original_plain_key = res.data["data"]["api_key"]
        key_uuid = res.data["data"]["key"]["uuid"]

        regen_url = reverse("api-key-regenerate", kwargs={"uuid": key_uuid})
        regen_response = self.client.post(regen_url)

        self.assertEqual(regen_response.status_code, status.HTTP_200_OK)
        new_plain_key = regen_response.data["data"]["api_key"]

        self.assertNotEqual(original_plain_key, new_plain_key)
        self.assertTrue(new_plain_key.startswith("pk_live_"))

        key_obj = APIKey.objects.get(uuid=key_uuid)
        expected_hash = hashlib.sha256(new_plain_key.encode("utf-8")).hexdigest()
        self.assertEqual(key_obj.key_hash, expected_hash)
        self.assertEqual(key_obj.expires_at, self.subscription1.end_date)

    def test_regenerate_api_key_expired_subscription_fails(self):
        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        res = self.client.post(
            create_url,
            {
                "name": "Key Pre-Expiry",
                "project": str(self.project1.uuid),
            },
            format="json",
        )
        key_uuid = res.data["data"]["key"]["uuid"]

        # Expire subscription
        self.subscription1.end_date = timezone.now() - timezone.timedelta(days=1)
        self.subscription1.save()

        regen_url = reverse("api-key-regenerate", kwargs={"uuid": key_uuid})
        regen_response = self.client.post(regen_url)

        self.assertEqual(regen_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticate_key_validation(self):
        from rest_framework.exceptions import AuthenticationFailed
        from apps.api_keys.services import APIKeyService

        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        res = self.client.post(
            create_url,
            {
                "name": "Auth Key Test",
                "project": str(self.project1.uuid),
            },
            format="json",
        )
        plain_key = res.data["data"]["api_key"]
        key_uuid = res.data["data"]["key"]["uuid"]

        # 1. Valid authentication succeeds and updates last_used_at
        user, key_obj = APIKeyService.authenticate_key(plain_key)
        self.assertEqual(user, self.dev_user1)
        self.assertIsNotNone(key_obj.last_used_at)

        # 2. Invalid key raises AuthenticationFailed
        with self.assertRaises(AuthenticationFailed) as ctx:
            APIKeyService.authenticate_key("pk_live_invalidkey")
        self.assertIn("Invalid API Key", str(ctx.exception))

        # 3. Inactive key raises AuthenticationFailed
        key_obj.is_active = False
        key_obj.save()
        with self.assertRaises(AuthenticationFailed) as ctx:
            APIKeyService.authenticate_key(plain_key)
        self.assertIn("API Key is inactive", str(ctx.exception))

        # Reset active status
        key_obj.is_active = True
        key_obj.save()

        # 4. Expired key/subscription raises PermissionDenied (403)
        key_obj.expires_at = timezone.now() - timezone.timedelta(days=1)
        key_obj.save()
        with self.assertRaises(PermissionDenied) as ctx:
            APIKeyService.authenticate_key(plain_key)
        self.assertIn("Subscription has expired", str(ctx.exception))

        # Reset expires_at
        key_obj.expires_at = timezone.now() + timezone.timedelta(days=30)
        key_obj.save()

        # 5. Cancelled subscription raises PermissionDenied (403)
        self.subscription1.status = UserSubscription.Status.CANCELLED
        self.subscription1.save()
        with self.assertRaises(PermissionDenied) as ctx:
            APIKeyService.authenticate_key(plain_key)
        self.assertIn("Subscription has been cancelled", str(ctx.exception))

    def test_protected_sample_endpoint_api_key_auth(self):
        from apps.usage_logs.models import UsageLog

        # 1. Create an API Key for dev_user1
        self.client.force_authenticate(user=self.dev_user1)
        create_url = reverse("api-key-list-create")
        res = self.client.post(
            create_url,
            {
                "name": "Sample Key",
                "project": str(self.project1.uuid),
            },
            format="json",
        )
        plain_key = res.data["data"]["api_key"]
        key_uuid = res.data["data"]["key"]["uuid"]

        # Clear authentication
        self.client.logout()

        protected_url = reverse("api-key-protected-sample")

        # 2. Unauthenticated request should fail (401)
        res_unauth = self.client.get(protected_url)
        self.assertEqual(res_unauth.status_code, status.HTTP_401_UNAUTHORIZED)

        initial_log_count = UsageLog.objects.count()

        # 3. Authenticated request using X-API-Key header should succeed
        res_auth = self.client.get(
            protected_url,
            HTTP_X_API_KEY=plain_key,
            HTTP_USER_AGENT="TestClient/1.0",
            HTTP_X_FORWARDED_FOR="203.0.113.195, 198.51.100.10",
        )
        self.assertEqual(res_auth.status_code, status.HTTP_200_OK)
        self.assertTrue(res_auth.data["success"])

        data = res_auth.data["data"]
        self.assertEqual(data["developer_email"], self.dev_user1.email)
        self.assertEqual(data["developer_uuid"], str(self.dev_user1.uuid))
        self.assertEqual(data["project_name"], self.project1.name)
        self.assertEqual(data["project_uuid"], str(self.project1.uuid))
        self.assertEqual(data["api_key_uuid"], key_uuid)

        # 4. Verify automatic UsageLog creation
        self.assertEqual(UsageLog.objects.count(), initial_log_count + 1)
        latest_log = UsageLog.objects.order_by("-created_at").first()

        self.assertEqual(latest_log.project.uuid, self.project1.uuid)
        self.assertEqual(str(latest_log.api_key.uuid), key_uuid)
        self.assertEqual(latest_log.endpoint, "/api/v1/api-keys/protected-sample/")
        self.assertEqual(latest_log.method, "GET")
        self.assertEqual(latest_log.status_code, 200)
        self.assertGreaterEqual(latest_log.response_time_ms, 0)
        self.assertEqual(latest_log.ip_address, "203.0.113.195")
        self.assertEqual(latest_log.user_agent, "TestClient/1.0")

        # 5. Verify log appears in GET /api/v1/usage-logs/
        self.client.force_authenticate(user=self.dev_user1)
        usage_logs_url = reverse("usage-log-list")
        res_list = self.client.get(usage_logs_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        listed_uuids = [item["uuid"] for item in res_list.data["data"]]
        self.assertIn(str(latest_log.uuid), listed_uuids)

    def test_protected_endpoint_cancelled_subscription_returns_403(self):
        self.client.force_authenticate(user=self.dev_user1)
        res = self.client.post(
            reverse("api-key-list-create"),
            {"name": "Cancelled Test Key", "project": str(self.project1.uuid)},
            format="json",
        )
        plain_key = res.data["data"]["api_key"]
        self.client.logout()

        # Cancel subscription
        self.subscription1.status = UserSubscription.Status.CANCELLED
        self.subscription1.save()

        protected_url = reverse("api-key-protected-sample")
        res_auth = self.client.get(protected_url, HTTP_X_API_KEY=plain_key)

        self.assertEqual(res_auth.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(res_auth.data["success"])
        self.assertEqual(res_auth.data["message"], "Subscription has been cancelled.")

    def test_protected_endpoint_exceeded_usage_limit_returns_429(self):
        from apps.usage_logs.models import UsageLog

        # Set plan limit to 1
        self.plan.request_limit = 1
        self.plan.save()

        self.client.force_authenticate(user=self.dev_user1)
        res = self.client.post(
            reverse("api-key-list-create"),
            {"name": "Limit Test Key", "project": str(self.project1.uuid)},
            format="json",
        )
        plain_key = res.data["data"]["api_key"]
        key_uuid = res.data["data"]["key"]["uuid"]
        self.client.logout()

        protected_url = reverse("api-key-protected-sample")

        # First call succeeds (1 request)
        res1 = self.client.get(protected_url, HTTP_X_API_KEY=plain_key)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Second call fails with 429 (limit exceeded)
        res2 = self.client.get(protected_url, HTTP_X_API_KEY=plain_key)
        self.assertEqual(res2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertFalse(res2.data["success"])
        self.assertEqual(res2.data["message"], "Monthly API request limit exceeded.")
