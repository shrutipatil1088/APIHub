from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal

from apps.accounts.models import User
from apps.subscriptions.models import SubscriptionPlan


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
