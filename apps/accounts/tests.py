from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthenticationAPITests(APITestCase):
    """
    Integration tests for User Registration, Login, Token Refresh, and Permissions.
    """

    def setUp(self):
        self.dev_user = User.objects.create_user(
            email="existing_dev@example.com",
            password="SecurePassword123!",
            full_name="Existing Developer",
            role=User.Role.DEVELOPER,
        )
        self.admin_user = User.objects.create_user(
            email="existing_admin@example.com",
            password="SecurePassword123!",
            full_name="Existing Admin",
            role=User.Role.ADMIN,
        )

    def test_user_registration_success(self):
        url = reverse("register")
        data = {
            "email": "new_developer@example.com",
            "full_name": "New Developer",
            "phone_number": "+1234567890",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "User registered successfully.")
        self.assertTrue(User.objects.filter(email="new_developer@example.com").exists())

    def test_user_registration_duplicate_email(self):
        url = reverse("register")
        data = {
            "email": "existing_dev@example.com",
            "full_name": "Duplicate User",
            "password": "StrongPassword123!",
            "confirm_password": "StrongPassword123!",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data.get("errors", {}))

    def test_user_registration_password_validation(self):
        url = reverse("register")

        # 1. Passwords do not match
        response_mismatch = self.client.post(url, {
            "email": "mismatch@example.com",
            "full_name": "Mismatch User",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!",
        }, format="json")
        self.assertEqual(response_mismatch.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("confirm_password", response_mismatch.data.get("errors", {}))

        # 2. Password too short (< 8 chars)
        response_short = self.client.post(url, {
            "email": "shortpass@example.com",
            "full_name": "Short Pass User",
            "password": "pass",
            "confirm_password": "pass",
        }, format="json")
        self.assertEqual(response_short.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response_short.data.get("errors", {}))

    def test_login_success(self):
        url = reverse("login")
        data = {
            "email": "existing_dev@example.com",
            "password": "SecurePassword123!",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])

    def test_login_invalid_password(self):
        url = reverse("login")
        data = {
            "email": "existing_dev@example.com",
            "password": "WrongPassword123!",
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_jwt_refresh(self):
        # Login to obtain refresh token
        login_url = reverse("login")
        login_resp = self.client.post(login_url, {
            "email": "existing_dev@example.com",
            "password": "SecurePassword123!",
        }, format="json")
        refresh_token = login_resp.data["data"]["refresh"]

        # Refresh token
        refresh_url = reverse("token_refresh")
        refresh_resp = self.client.post(refresh_url, {"refresh": refresh_token}, format="json")

        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_resp.data)

    def test_unauthorized_access(self):
        profile_url = reverse("profile")

        # Request without token fails
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_role_based_permissions_admin_vs_developer(self):
        profile_url = reverse("profile")

        # Developer access to profile
        self.client.force_authenticate(user=self.dev_user)
        response_dev = self.client.get(profile_url)
        self.assertEqual(response_dev.status_code, status.HTTP_200_OK)
        self.assertEqual(response_dev.data["data"]["role"], "DEVELOPER")

        # Admin access to profile
        self.client.force_authenticate(user=self.admin_user)
        response_admin = self.client.get(profile_url)
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        self.assertEqual(response_admin.data["data"]["role"], "ADMIN")


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
