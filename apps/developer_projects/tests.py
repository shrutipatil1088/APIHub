from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.developer_projects.models import DeveloperProject


class DeveloperProjectAPITests(APITestCase):
    """
    Integration tests for DeveloperProject CRUD APIs.
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

        # Precreate some projects
        self.project1 = DeveloperProject.objects.create(
            developer=self.dev_user1,
            name="Developer One Project",
            description="Detailed description for project one meeting length limit.",
        )
        self.project2 = DeveloperProject.objects.create(
            developer=self.dev_user2,
            name="Developer Two Project",
            description="Detailed description for project two meeting length limit.",
        )

    def test_create_project_success(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("developer-project-list-create")

        response = self.client.post(url, {
            "name": "Weather App",
            "description": "A very useful weather forecasting app."
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DeveloperProject.objects.filter(developer=self.dev_user1).count(), 2)

        data = response.data["data"]
        self.assertEqual(data["name"], "Weather App")
        self.assertEqual(data["developer"]["email"], self.dev_user1.email)

    def test_create_project_admin_fails(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("developer-project-list-create")

        response = self.client.post(url, {
            "name": "Admin Project",
            "description": "Admin trying to create a project description."
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Only developers can create projects.")

    def test_create_project_validation_min_lengths(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("developer-project-list-create")

        # 1. Name too short (< 3)
        response = self.client.post(url, {
            "name": "ab",
            "description": "Detailed description for this project."
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data.get("errors", {}))

        # 2. Description too short (< 20)
        response = self.client.post(url, {
            "name": "Valid Name",
            "description": "Too short"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data.get("errors", {}))

    def test_create_project_uniqueness_per_developer(self):
        self.client.force_authenticate(user=self.dev_user1)
        url = reverse("developer-project-list-create")

        # 1. Developer 1 creating duplicate project name should fail
        response = self.client.post(url, {
            "name": "Developer One Project",
            "description": "Detailed description for project one meeting length limit."
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data.get("errors", {}))

        # 2. Developer 2 creating project with same name should succeed
        self.client.force_authenticate(user=self.dev_user2)
        response2 = self.client.post(url, {
            "name": "Developer One Project",
            "description": "Detailed description for project one meeting length limit."
        }, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)

    def test_list_projects_ownership(self):
        url = reverse("developer-project-list-create")

        # 1. Developer 1 list should see only their own project
        self.client.force_authenticate(user=self.dev_user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)
        self.assertEqual(response.data["data"][0]["name"], "Developer One Project")

        # 2. Admin list should see both projects
        self.client.force_authenticate(user=self.admin_user)
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response2.data["data"]), 2)

    def test_retrieve_project_owner_or_admin(self):
        detail_url = reverse("developer-project-detail", kwargs={"uuid": self.project1.uuid})

        # 1. Other developer retrieval should fail (403)
        self.client.force_authenticate(user=self.dev_user2)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Owner retrieval should succeed
        self.client.force_authenticate(user=self.dev_user1)
        response2 = self.client.get(detail_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # 3. Admin retrieval should succeed
        self.client.force_authenticate(user=self.admin_user)
        response3 = self.client.get(detail_url)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

    def test_update_project_owner_only(self):
        detail_url = reverse("developer-project-detail", kwargs={"uuid": self.project1.uuid})

        # 1. Other developer update fails
        self.client.force_authenticate(user=self.dev_user2)
        response = self.client.patch(detail_url, {"name": "New Name Value"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin update fails (Owner only)
        self.client.force_authenticate(user=self.admin_user)
        response2 = self.client.patch(detail_url, {"name": "New Name Value"}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Owner update succeeds
        self.client.force_authenticate(user=self.dev_user1)
        response3 = self.client.patch(detail_url, {
            "name": "Updated Project Name",
            "description": "Newly updated description that exceeds twenty characters."
        }, format="json")
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.data["data"]["name"], "Updated Project Name")

    def test_delete_project_owner_only(self):
        detail_url = reverse("developer-project-detail", kwargs={"uuid": self.project1.uuid})

        # 1. Other developer delete fails
        self.client.force_authenticate(user=self.dev_user2)
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin delete fails
        self.client.force_authenticate(user=self.admin_user)
        response2 = self.client.delete(detail_url)
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Owner delete succeeds
        self.client.force_authenticate(user=self.dev_user1)
        response3 = self.client.delete(detail_url)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        # Confirm soft deleted in DB
        proj = DeveloperProject.objects.get(uuid=self.project1.uuid)
        self.assertTrue(proj.is_deleted)
