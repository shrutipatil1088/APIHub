from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.api_catalog.models import API

class APICatalogTests(APITestCase):
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
        
        # Authenticate developer client by default
        self.client.force_authenticate(user=self.developer_user)

    def test_create_and_list_apis_behavior(self):
        # 1. Admin can create an API
        self.client.force_authenticate(user=self.admin_user)
        create_url = reverse("api-list-create")
        data = {
            "name": "Weather API",
            "description": "An API to fetch real-time weather information.",
            "status": "PUBLISHED"
        }
        response = self.client.post(create_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["is_active"], True)
        self.assertEqual(response.data["data"]["status"], "PUBLISHED")
        uuid = response.data["data"]["uuid"]

        # 2. Developer can list APIs and see is_active in response
        self.client.force_authenticate(user=self.developer_user)
        list_url = reverse("api-list-create")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify the returned list contains weather API and is_active field
        results = response.data["data"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["uuid"], uuid)
        self.assertEqual(results[0]["is_active"], True)

        # 3. Modify is_active to False using PATCH
        self.client.force_authenticate(user=self.admin_user)
        detail_url = reverse("api-detail", kwargs={"uuid": uuid})
        response = self.client.patch(detail_url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["is_active"], False)

        # Update it back to True using PUT
        response = self.client.put(detail_url, {
            "name": "Weather API Updated",
            "description": "An API to fetch real-time weather information updated.",
            "status": "PUBLISHED",
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["is_active"], True)

        # Update it to False using PUT
        response = self.client.put(detail_url, {
            "name": "Weather API Updated",
            "description": "An API to fetch real-time weather information updated.",
            "status": "PUBLISHED",
            "is_active": False
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["is_active"], False)

        # 4. Listing should still return the inactive API (since it is not deleted)
        self.client.force_authenticate(user=self.developer_user)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["is_active"], False)

        # 5. Detail endpoint should still return the inactive API
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["is_active"], False)

        # 6. Soft delete the API
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check DB state
        api_obj = API.objects.get(uuid=uuid)
        self.assertEqual(api_obj.is_deleted, True)
        self.assertIsNotNone(api_obj.deleted_at)

        # 7. Listing should NOT return soft-deleted APIs
        self.client.force_authenticate(user=self.developer_user)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 0)

        # 8. Detail endpoint should NOT return soft-deleted API
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
