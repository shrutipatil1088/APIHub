from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal

from apps.accounts.models import User
from apps.subscriptions.models import SubscriptionPlan, UserSubscription


class SubscriptionPlanAPITests(APITestCase):
    def setUp(self):
        # Create an admin user
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="password123",
            full_name="Admin User"
        )
        # Create a regular developer user
        self.developer_user = User.objects.create_user(
            email="developer@example.com",
            password="password123",
            full_name="Developer User",
            role=User.Role.DEVELOPER
        )

        # Create active subscription plan
        self.plan_active = SubscriptionPlan.objects.create(
            name="Developer Basic Plan",
            description="Basic plan for developers starting out with 10k requests.",
            price=19.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=10000,
            is_active=True
        )

        # Create inactive subscription plan
        self.plan_inactive = SubscriptionPlan.objects.create(
            name="Enterprise Premium Plan",
            description="Premium plan for enterprise developers with 1M requests.",
            price=199.99,
            billing_cycle=SubscriptionPlan.BillingCycle.YEARLY,
            request_limit=1000000,
            is_active=False
        )

        # Authenticate developer client by default
        self.client.force_authenticate(user=self.developer_user)

    def test_list_plans_as_developer(self):
        list_url = reverse("subscription-plan-list-create")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["data"]
        # Both active and inactive (but not deleted) plans should be listed
        self.assertEqual(len(results), 2)
        
        # Verify pagination and keys in response
        self.assertIn("uuid", results[0])
        self.assertIn("name", results[0])
        self.assertIn("price", results[0])
        self.assertIn("billing_cycle", results[0])
        self.assertIn("is_active", results[0])

    def test_filter_and_search_plans(self):
        list_url = reverse("subscription-plan-list-create")

        # Search by name
        response = self.client.get(list_url, {"search": "Basic"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Developer Basic Plan")

        # Filter by active status
        response = self.client.get(list_url, {"is_active": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Enterprise Premium Plan")

        # Filter by billing cycle
        response = self.client.get(list_url, {"billing_cycle": "YEARLY"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Enterprise Premium Plan")

    def test_ordering_plans(self):
        list_url = reverse("subscription-plan-list-create")

        # Order by price ascending
        response = self.client.get(list_url, {"ordering": "price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"][0]["name"], "Developer Basic Plan")

        # Order by price descending
        response = self.client.get(list_url, {"ordering": "-price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"][0]["name"], "Enterprise Premium Plan")

    def test_create_plan_permissions(self):
        list_url = reverse("subscription-plan-list-create")
        data = {
            "name": "Startup Growth Plan",
            "description": "Growth plan for fast growing startups with 100k requests.",
            "price": 49.99,
            "billing_cycle": "MONTHLY",
            "request_limit": 100000,
            "is_active": True
        }

        # Regular developer cannot create
        response = self.client.post(list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can create
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(list_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["name"], "Startup Growth Plan")

    def test_create_plan_validation(self):
        self.client.force_authenticate(user=self.admin_user)
        list_url = reverse("subscription-plan-list-create")

        # 1. Invalid name length (less than 3)
        response = self.client.post(list_url, {
            "name": "a",
            "description": "Short description must be 20 chars minimum.",
            "price": 9.99,
            "billing_cycle": "MONTHLY",
            "request_limit": 1000
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data.get("errors", {}))

        # 2. Invalid description length (less than 20)
        response = self.client.post(list_url, {
            "name": "Valid Name",
            "description": "Short desc",
            "price": 9.99,
            "billing_cycle": "MONTHLY",
            "request_limit": 1000
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data.get("errors", {}))

        # 3. Price less than or equal to 0 for a paid plan
        response = self.client.post(list_url, {
            "name": "Valid Name",
            "description": "Valid description of at least twenty characters.",
            "price": 0.00,
            "billing_cycle": "MONTHLY",
            "request_limit": 1000
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data.get("errors", {}))

        # 3b. Free plan with non-zero price should fail
        response = self.client.post(list_url, {
            "name": "Free",
            "description": "Valid description of at least twenty characters.",
            "price": 9.99,
            "billing_cycle": "MONTHLY",
            "request_limit": 1000
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data.get("errors", {}))

        # 3c. Free plan with zero price should succeed
        response = self.client.post(list_url, {
            "name": "Free Plan",
            "description": "Valid description of at least twenty characters.",
            "price": 0.00,
            "billing_cycle": "MONTHLY",
            "request_limit": 1000
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 4. Request limit less than or equal to 0
        response = self.client.post(list_url, {
            "name": "Valid Name",
            "description": "Valid description of at least twenty characters.",
            "price": 9.99,
            "billing_cycle": "MONTHLY",
            "request_limit": 0
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("request_limit", response.data.get("errors", {}))

    def test_retrieve_plan_details(self):
        detail_url = reverse("subscription-plan-detail", kwargs={"uuid": self.plan_active.uuid})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data["data"]
        self.assertEqual(data["name"], "Developer Basic Plan")
        self.assertEqual(data["description"], "Basic plan for developers starting out with 10k requests.")
        self.assertEqual(float(data["price"]), 19.99)
        self.assertEqual(data["billing_cycle"], "MONTHLY")
        self.assertEqual(data["request_limit"], 10000)

    def test_update_plan_permissions_and_renaming(self):
        detail_url = reverse("subscription-plan-detail", kwargs={"uuid": self.plan_active.uuid})
        update_data = {
            "name": "Developer Basic Plan Updated",
            "description": "Updated basic plan description that meets 20 characters.",
            "price": 24.99,
            "billing_cycle": "MONTHLY",
            "request_limit": 12000,
            "is_active": True
        }

        # Regular user cannot update
        response = self.client.put(detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can update
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["name"], "Developer Basic Plan Updated")
        self.assertEqual(float(response.data["data"]["price"]), 24.99)

    def test_soft_delete_and_restoration(self):
        self.client.force_authenticate(user=self.admin_user)
        detail_url = reverse("subscription-plan-detail", kwargs={"uuid": self.plan_active.uuid})

        # Soft delete
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify soft delete status in DB
        self.plan_active.refresh_from_db()
        self.assertTrue(self.plan_active.is_deleted)

        # Listing should not return soft-deleted plan
        self.client.force_authenticate(user=self.developer_user)
        list_url = reverse("subscription-plan-list-create")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)  # Only Enterprise plan left

        # Detail should return 404
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Restore-on-create logic:
        # Posting a plan with same name as soft-deleted plan should restore it
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(list_url, {
            "name": "Developer Basic Plan",
            "description": "New restored basic plan description meeting limit.",
            "price": 29.99,
            "billing_cycle": "MONTHLY",
            "request_limit": 15000,
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["uuid"], str(self.plan_active.uuid))

        # Refresh and confirm restored in DB
        self.plan_active.refresh_from_db()
        self.assertFalse(self.plan_active.is_deleted)
        self.assertEqual(self.plan_active.price, Decimal("29.99"))
        self.assertEqual(self.plan_active.request_limit, 15000)

        # Rename to an active duplicate name should fail
        # Let's try to update Enterprise plan name to "Developer Basic Plan"
        ent_detail_url = reverse("subscription-plan-detail", kwargs={"uuid": self.plan_inactive.uuid})
        response = self.client.patch(ent_detail_url, {"name": "Developer Basic Plan"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data.get("errors", {}))

    def test_single_active_free_plan_constraint(self):
        self.client.force_authenticate(user=self.admin_user)
        list_url = reverse("subscription-plan-list-create")

        # 1. Create first active Free plan (price = 0)
        resp1 = self.client.post(list_url, {
            "name": "Free Plan A",
            "description": "First free plan description with at least 20 characters.",
            "price": 0.00,
            "billing_cycle": "MONTHLY",
            "request_limit": 1000,
            "is_active": True
        }, format="json")
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        uuid1 = resp1.data["data"]["uuid"]

        # Confirm first plan is active
        plan1 = SubscriptionPlan.objects.get(uuid=uuid1)
        self.assertTrue(plan1.is_active)

        # 2. Create second active Free plan (price = 0)
        resp2 = self.client.post(list_url, {
            "name": "Free Plan B",
            "description": "Second free plan description with at least 20 characters.",
            "price": 0.00,
            "billing_cycle": "MONTHLY",
            "request_limit": 1000,
            "is_active": True
        }, format="json")
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        uuid2 = resp2.data["data"]["uuid"]

        # Confirm first plan became inactive, and second plan is active
        plan1.refresh_from_db()
        plan2 = SubscriptionPlan.objects.get(uuid=uuid2)
        self.assertFalse(plan1.is_active)
        self.assertTrue(plan2.is_active)

        # 3. Update the first plan to be active again (using PATCH)
        detail_url1 = reverse("subscription-plan-detail", kwargs={"uuid": uuid1})
        resp3 = self.client.patch(detail_url1, {"is_active": True}, format="json")
        self.assertEqual(resp3.status_code, status.HTTP_200_OK)

        # Confirm first plan is active again, and second plan became inactive
        plan1.refresh_from_db()
        plan2.refresh_from_db()
        self.assertTrue(plan1.is_active)
        self.assertFalse(plan2.is_active)


class UserSubscriptionAPITests(APITestCase):
    """
    Integration tests for UserSubscription CRUD APIs.
    """

    def setUp(self):
        # Create user accounts
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

        # Create subscription plans
        self.plan_monthly = SubscriptionPlan.objects.create(
            name="Developer Monthly",
            description="Monthly developer subscription plan description",
            price=29.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=10000,
            is_active=True,
        )
        self.plan_yearly = SubscriptionPlan.objects.create(
            name="Developer Yearly",
            description="Yearly developer subscription plan description",
            price=299.99,
            billing_cycle=SubscriptionPlan.BillingCycle.YEARLY,
            request_limit=150000,
            is_active=True,
        )
        self.plan_inactive = SubscriptionPlan.objects.create(
            name="Developer Legacy Plan",
            description="Legacy developer subscription plan description",
            price=19.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=5000,
            is_active=False,
        )

    def test_purchase_subscription_success(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("user-subscription-list-create")

        # Purchase Monthly Plan
        response = self.client.post(url, {
            "plan": str(self.plan_monthly.uuid),
            "auto_renew": True
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserSubscription.objects.filter(user=self.dev_user1).count(), 1)
        
        sub = UserSubscription.objects.get(user=self.dev_user1)
        self.assertEqual(sub.plan, self.plan_monthly)
        self.assertEqual(sub.status, UserSubscription.Status.ACTIVE)
        self.assertTrue(sub.auto_renew)
        self.assertAlmostEqual(
            (sub.end_date - sub.start_date).days, 
            30, 
            delta=1
        )

    def test_purchase_subscription_admin_fails(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("user-subscription-list-create")

        response = self.client.post(url, {
            "plan": str(self.plan_monthly.uuid),
            "auto_renew": True
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Only developers can purchase a subscription plan.")

    def test_purchase_subscription_inactive_plan_fails(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("user-subscription-list-create")

        response = self.client.post(url, {
            "plan": str(self.plan_inactive.uuid),
            "auto_renew": True
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("plan", response.data.get("errors", {}))

    def test_purchase_subscription_already_active_fails(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("user-subscription-list-create")

        # Create active subscription first
        self.client.post(url, {
            "plan": str(self.plan_monthly.uuid),
            "auto_renew": True
        }, format="json")

        # Try to purchase again
        response = self.client.post(url, {
            "plan": str(self.plan_yearly.uuid),
            "auto_renew": True
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "User already has an active subscription.")

    def test_list_subscriptions_admin_only(self):
        url = reverse("user-subscription-list-create")

        # Non-admin list should fail (403)
        self.client.force_authenticate(user=self.dev_user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin list should succeed (200)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_subscription_owner_or_admin(self):
        # 1. Owner purchases subscription
        self.client.force_authenticate(user=self.dev_user1)
        url_create = reverse("user-subscription-list-create")
        resp_create = self.client.post(url_create, {
            "plan": str(self.plan_monthly.uuid),
            "auto_renew": True
        }, format="json")
        uuid = resp_create.data["data"]["uuid"]

        detail_url = reverse("user-subscription-detail", kwargs={"uuid": uuid})

        # 2. Other user tries to retrieve -> 403 Forbidden
        self.client.force_authenticate(user=self.dev_user2)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Owner retrieves -> 200 OK
        self.client.force_authenticate(user=self.dev_user1)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["user"]["email"], self.dev_user1.email)

        # 4. Admin retrieves -> 200 OK
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_subscription_admin_only(self):
        # Create subscription
        self.client.force_authenticate(user=self.dev_user1)
        url_create = reverse("user-subscription-list-create")
        resp_create = self.client.post(url_create, {
            "plan": str(self.plan_monthly.uuid),
            "auto_renew": True
        }, format="json")
        uuid = resp_create.data["data"]["uuid"]

        detail_url = reverse("user-subscription-detail", kwargs={"uuid": uuid})

        # Non-admin update fails
        self.client.force_authenticate(user=self.dev_user1)
        response = self.client.patch(detail_url, {"auto_renew": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin update succeeds
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(detail_url, {
            "status": "EXPIRED",
            "auto_renew": False
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "EXPIRED")
        self.assertFalse(response.data["data"]["auto_renew"])

    def test_delete_subscription_admin_only(self):
        # Create subscription
        self.client.force_authenticate(user=self.dev_user1)
        url_create = reverse("user-subscription-list-create")
        resp_create = self.client.post(url_create, {
            "plan": str(self.plan_monthly.uuid),
            "auto_renew": True
        }, format="json")
        uuid = resp_create.data["data"]["uuid"]

        detail_url = reverse("user-subscription-detail", kwargs={"uuid": uuid})

        # Non-admin delete fails
        self.client.force_authenticate(user=self.dev_user1)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin delete succeeds
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify soft-delete
        sub = UserSubscription.objects.get(uuid=uuid)
        self.assertTrue(sub.is_deleted)

    def test_my_subscriptions(self):
        self.client.force_authenticate(user=self.dev_user1)
        url_create = reverse("user-subscription-list-create")
        url_me = reverse("user-subscription-me")

        # Purchase Monthly Plan
        self.client.post(url_create, {
            "plan": str(self.plan_monthly.uuid),
            "auto_renew": True
        }, format="json")

        # Retrieve `/me/`
        response = self.client.get(url_me)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["plan_name"], "Developer Monthly")


class SubscriptionValidationServiceTests(APITestCase):
    """
    Unit and integration tests for SubscriptionValidationService.
    """

    def setUp(self):
        import hashlib
        from django.utils import timezone
        from apps.developer_projects.models import DeveloperProject
        from apps.api_keys.models import APIKey
        from apps.usage_logs.models import UsageLog

        self.developer = User.objects.create_user(
            email="val_dev@example.com",
            password="password123",
            full_name="Validation Developer",
            role=User.Role.DEVELOPER,
        )

        self.plan_limited = SubscriptionPlan.objects.create(
            name="Limited Plan",
            description="Limited plan description with 2 requests limit.",
            price=9.99,
            billing_cycle=SubscriptionPlan.BillingCycle.MONTHLY,
            request_limit=2,
            is_active=True,
        )

        self.plan_enterprise = SubscriptionPlan.objects.create(
            name="Enterprise Unlimited Plan",
            description="Unlimited enterprise plan description with zero request limit.",
            price=499.99,
            billing_cycle=SubscriptionPlan.BillingCycle.YEARLY,
            request_limit=0,
            is_active=True,
        )

        self.subscription_active = UserSubscription.objects.create(
            user=self.developer,
            plan=self.plan_limited,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=29),
            status=UserSubscription.Status.ACTIVE,
        )

        self.project = DeveloperProject.objects.create(
            developer=self.developer,
            name="Validation Test Project",
            description="Project created for testing subscription validations.",
        )

        self.api_key = APIKey.objects.create(
            project=self.project,
            subscription=self.subscription_active,
            name="Test Validation Key",
            key_hash=hashlib.sha256(b"val_key_secret").hexdigest(),
            expires_at=self.subscription_active.end_date,
            is_active=True,
        )

    def test_validate_active_subscription_success(self):
        from apps.subscriptions.services import SubscriptionValidationService
        self.assertTrue(SubscriptionValidationService.validate_subscription(self.api_key))

    def test_validate_expired_subscription_fails(self):
        from django.utils import timezone
        from rest_framework.exceptions import PermissionDenied
        from apps.subscriptions.services import SubscriptionValidationService

        self.subscription_active.status = UserSubscription.Status.EXPIRED
        self.subscription_active.save()

        with self.assertRaises(PermissionDenied) as ctx:
            SubscriptionValidationService.validate_subscription(self.api_key)
        self.assertIn("Subscription has expired.", str(ctx.exception))

    def test_validate_cancelled_subscription_fails(self):
        from rest_framework.exceptions import PermissionDenied
        from apps.subscriptions.services import SubscriptionValidationService

        self.subscription_active.status = UserSubscription.Status.CANCELLED
        self.subscription_active.save()

        with self.assertRaises(PermissionDenied) as ctx:
            SubscriptionValidationService.validate_subscription(self.api_key)
        self.assertIn("Subscription has been cancelled.", str(ctx.exception))

    def test_validate_usage_limit_success_and_exceeded(self):
        from apps.subscriptions.services import SubscriptionValidationService
        from apps.subscriptions.exceptions import UsageLimitExceeded
        from apps.usage_logs.models import UsageLog

        # 0 requests -> Under limit (2)
        self.assertTrue(SubscriptionValidationService.validate_usage_limit(self.api_key))

        # Create 2 usage log records
        for i in range(2):
            UsageLog.objects.create(
                project=self.project,
                api_key=self.api_key,
                endpoint="/api/v1/test",
                method="GET",
                status_code=200,
                response_time_ms=50,
            )

        # 2 requests -> Limit exceeded
        with self.assertRaises(UsageLimitExceeded) as ctx:
            SubscriptionValidationService.validate_usage_limit(self.api_key)
        self.assertIn("Monthly API request limit exceeded.", str(ctx.exception))

    def test_enterprise_unlimited_plan_bypasses_limit(self):
        from apps.subscriptions.services import SubscriptionValidationService
        from apps.usage_logs.models import UsageLog

        self.subscription_active.plan = self.plan_enterprise
        self.subscription_active.save()

        # Create 10 usage log records
        for i in range(10):
            UsageLog.objects.create(
                project=self.project,
                api_key=self.api_key,
                endpoint="/api/v1/test",
                method="GET",
                status_code=200,
                response_time_ms=50,
            )

        # Unlimited plan should pass
        self.assertTrue(SubscriptionValidationService.validate_usage_limit(self.api_key))

