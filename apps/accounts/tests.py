from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class DeveloperManagementAPITests(APITestCase):
    """
    Integration tests for Admin Developer List and Detail endpoints.
    """

    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin_devs@example.com",
            password="securepassword123",
            full_name="Admin User",
            role=User.Role.ADMIN,
        )

        # Create developer users
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

    def test_admin_can_list_developers(self):
        url = reverse("developer-list")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["pagination"]["count"], 2)

    def test_admin_can_retrieve_developer_detail(self):
        url = reverse("developer-detail", kwargs={"uuid": self.dev_user1.uuid})
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["email"], "dev1@example.com")

    def test_developer_cannot_access_developer_list(self):
        url = reverse("developer-list")
        self.client.force_authenticate(user=self.dev_user1)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
