from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.accounts.models import User
from apps.api_catalog.models import API, APIVersion, Endpoint

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


class APIVersionTests(APITestCase):
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
        
        # Create a test API
        self.api = API.objects.create(
            name="Payment API",
            slug="payment-api",
            description="API for processing client payments.",
            status=API.Status.PUBLISHED,
            created_by=self.admin_user
        )

        # Authenticate developer client by default
        self.client.force_authenticate(user=self.developer_user)

    def test_create_and_list_versions_behavior(self):
        # 1. Non-admin user cannot create a version (Forbidden)
        create_url = reverse("api-version-list-create", kwargs={"api_uuid": self.api.uuid})
        response = self.client.post(create_url, {"version": "v1.0.0"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin can create a version
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(create_url, {
            "version": "v1.0.0",
            "release_notes": "First version release.",
            "is_latest": True,
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["version"], "v1.0.0")
        self.assertEqual(response.data["data"]["is_latest"], True)
        self.assertEqual(response.data["data"]["is_active"], True)
        version_uuid = response.data["data"]["uuid"]

        # 3. Validation: Unique version per API
        response = self.client.post(create_url, {
            "version": "v1.0.0"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Developer can list versions
        self.client.force_authenticate(user=self.developer_user)
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["uuid"], version_uuid)

        # 5. Developer can retrieve version detail
        detail_url = reverse("api-version-detail", kwargs={"uuid": version_uuid})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["version"], "v1.0.0")

        # 6. Admin can update version (PUT / PATCH)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(detail_url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["is_active"], False)

        response = self.client.put(detail_url, {
            "version": "v1.1.0",
            "release_notes": "Updated release notes.",
            "is_latest": False,
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["version"], "v1.1.0")
        self.assertEqual(response.data["data"]["is_latest"], False)

        # 7. Soft delete version
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        version_obj = APIVersion.objects.get(uuid=version_uuid)
        self.assertEqual(version_obj.is_deleted, True)

        # 8. Soft-deleted version is no longer accessible
        self.client.force_authenticate(user=self.developer_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 0)

    def test_protected_soft_delete_validation(self):
        # 1. Create a version under our API
        self.client.force_authenticate(user=self.admin_user)
        create_url = reverse("api-version-list-create", kwargs={"api_uuid": self.api.uuid})
        response = self.client.post(create_url, {
            "version": "v1.0.0",
            "release_notes": "Validation test version.",
            "is_latest": True,
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        version_uuid = response.data["data"]["uuid"]

        # 2. Try to soft-delete the API (should fail because it has an active version)
        api_detail_url = reverse("api-detail", kwargs={"uuid": self.api.uuid})
        response = self.client.delete(api_detail_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Checking that the error detail has the correct message
        self.assertIn("Cannot delete Api because it is used in: Api Version (1).", response.data["message"])

        # 3. Soft-delete the version
        version_detail_url = reverse("api-version-detail", kwargs={"uuid": version_uuid})
        response = self.client.delete(version_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Try deleting the API again (should succeed now because the version is soft-deleted)
        response = self.client.delete(api_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.api.refresh_from_db()
        self.assertEqual(self.api.is_deleted, True)

    def test_unique_latest_version(self):
        self.client.force_authenticate(user=self.admin_user)
        create_url = reverse("api-version-list-create", kwargs={"api_uuid": self.api.uuid})

        # 1. Create version v1.0.0 as latest
        resp_v1 = self.client.post(create_url, {
            "version": "v1.0.0",
            "release_notes": "v1 release.",
            "is_latest": True,
            "is_active": True
        }, format="json")
        self.assertEqual(resp_v1.status_code, status.HTTP_201_CREATED)
        v1_uuid = resp_v1.data["data"]["uuid"]

        # 2. Create version v2.0.0 as latest
        resp_v2 = self.client.post(create_url, {
            "version": "v2.0.0",
            "release_notes": "v2 release.",
            "is_latest": True,
            "is_active": True
        }, format="json")
        self.assertEqual(resp_v2.status_code, status.HTTP_201_CREATED)
        v2_uuid = resp_v2.data["data"]["uuid"]

        # Verify database: v2 should be latest, v1 should NOT be latest
        v1_obj = APIVersion.objects.get(uuid=v1_uuid)
        v2_obj = APIVersion.objects.get(uuid=v2_uuid)
        self.assertFalse(v1_obj.is_latest)
        self.assertTrue(v2_obj.is_latest)

        # 3. Create version v3.0.0 as NOT latest
        resp_v3 = self.client.post(create_url, {
            "version": "v3.0.0",
            "release_notes": "v3 release.",
            "is_latest": False,
            "is_active": True
        }, format="json")
        self.assertEqual(resp_v3.status_code, status.HTTP_201_CREATED)
        v3_uuid = resp_v3.data["data"]["uuid"]

        # Verify database: v2 is still latest, v3 is not
        v2_obj.refresh_from_db()
        v3_obj = APIVersion.objects.get(uuid=v3_uuid)
        self.assertTrue(v2_obj.is_latest)
        self.assertFalse(v3_obj.is_latest)

        # 4. Update v3.0.0 to be latest using PATCH
        detail_url_v3 = reverse("api-version-detail", kwargs={"uuid": v3_uuid})
        resp_patch = self.client.patch(detail_url_v3, {"is_latest": True}, format="json")
        self.assertEqual(resp_patch.status_code, status.HTTP_200_OK)

        # Verify database: v3 is now latest, v2 is no longer latest
        v2_obj.refresh_from_db()
        v3_obj.refresh_from_db()
        self.assertFalse(v2_obj.is_latest)
        self.assertTrue(v3_obj.is_latest)

    def test_semantic_version_validation(self):
        self.client.force_authenticate(user=self.admin_user)
        create_url = reverse("api-version-list-create", kwargs={"api_uuid": self.api.uuid})



        # Test invalid version strings
        invalid_versions = ["abc", "hello", "xyz", "v1.a", "v1.2.3-alpha", "1.0"]
        for val in invalid_versions:
            response = self.client.post(create_url, {
                "version": val,
                "release_notes": "invalid version tests.",
                "is_latest": False,
                "is_active": True
            }, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                f"Version value '{val}' should have been rejected as invalid."
            )
            self.assertIn("version", response.data.get("errors", {}))

        # Test valid version strings
        valid_versions = ["v1", "v2", "v1.0", "v1.0.1", "v10.5.2"]
        for val in valid_versions:
            response = self.client.post(create_url, {
                "version": val,
                "release_notes": "valid version tests.",
                "is_latest": False,
                "is_active": True
            }, format="json")
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                f"Version value '{val}' should have been accepted as valid."
            )

    def test_soft_deleted_version_recreation_and_update(self):
        self.client.force_authenticate(user=self.admin_user)
        create_url = reverse("api-version-list-create", kwargs={"api_uuid": self.api.uuid})

        # 1. Create a version v1.5.0
        response = self.client.post(create_url, {
            "version": "v1.5.0",
            "release_notes": "Original release notes.",
            "is_latest": False,
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        version_uuid = response.data["data"]["uuid"]

        # 2. Soft delete it
        detail_url = reverse("api-version-detail", kwargs={"uuid": version_uuid})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Confirm it is soft-deleted
        self.assertTrue(APIVersion.objects.get(uuid=version_uuid).is_deleted)

        # 3. Try to recreate it (should restore and update)
        response = self.client.post(create_url, {
            "version": "v1.5.0",
            "release_notes": "Restored and updated notes.",
            "is_latest": True,
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Confirm it's the same UUID and it's restored
        self.assertEqual(response.data["data"]["uuid"], str(version_uuid))
        version_obj = APIVersion.objects.get(uuid=version_uuid)
        self.assertFalse(version_obj.is_deleted)
        self.assertEqual(version_obj.release_notes, "Restored and updated notes.")
        self.assertTrue(version_obj.is_latest)

        # 4. Soft delete it again
        self.client.delete(detail_url)
        self.assertTrue(APIVersion.objects.get(uuid=version_uuid).is_deleted)

        # 5. Create another version v1.6.0
        response = self.client.post(create_url, {
            "version": "v1.6.0",
            "release_notes": "V1.6 notes.",
            "is_latest": False,
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        v1_6_uuid = response.data["data"]["uuid"]

        # 6. Try to rename v1.6.0 to v1.5.0 (which is soft-deleted) -> should fail with 400 Bad Request
        detail_url_v1_6 = reverse("api-version-detail", kwargs={"uuid": v1_6_uuid})
        response = self.client.patch(detail_url_v1_6, {"version": "v1.5.0"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("version", response.data.get("errors", {}))


class EndpointTests(APITestCase):
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

        # Create a test API
        self.api = API.objects.create(
            name="Payment API",
            slug="payment-api",
            description="API for processing client payments.",
            status=API.Status.PUBLISHED,
            created_by=self.admin_user
        )

        # Create a test version
        self.version = APIVersion.objects.create(
            api=self.api,
            version="v1.0.0",
            release_notes="First version release.",
            is_latest=True,
            is_active=True
        )

        # Authenticate developer client by default
        self.client.force_authenticate(user=self.developer_user)

    def test_create_and_list_endpoints_behavior(self):
        # 1. Non-admin user cannot create an endpoint (Forbidden)
        create_url = reverse("endpoint-list-create", kwargs={"version_uuid": self.version.uuid})
        response = self.client.post(create_url, {
            "method": "GET",
            "path": "/payments",
            "summary": "List payments",
            "description": "Returns all payments."
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Admin can create an endpoint
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(create_url, {
            "method": "GET",
            "path": "/payments",
            "summary": "List payments",
            "description": "Returns all payments.",
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["path"], "/payments")
        self.assertEqual(response.data["data"]["is_active"], True)
        endpoint_uuid = response.data["data"]["uuid"]

        # 3. Validation: Duplicate combination of version, method, and path
        response = self.client.post(create_url, {
            "method": "GET",
            "path": "/payments",
            "summary": "List payments again"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Developer can list endpoints
        self.client.force_authenticate(user=self.developer_user)
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["uuid"], endpoint_uuid)

        # 5. Developer can retrieve endpoint detail
        detail_url = reverse("endpoint-detail", kwargs={"uuid": endpoint_uuid})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["path"], "/payments")

        # 6. Admin can update endpoint (PUT / PATCH)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(detail_url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["is_active"], False)

        response = self.client.put(detail_url, {
            "method": "POST",
            "path": "/payments",
            "summary": "Create payment",
            "description": "Creates a payment.",
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["method"], "POST")
        self.assertEqual(response.data["data"]["is_active"], True)

        # 7. Soft delete endpoint
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        endpoint_obj = Endpoint.objects.get(uuid=endpoint_uuid)
        self.assertEqual(endpoint_obj.is_deleted, True)

        # 8. Soft-deleted endpoint is no longer accessible
        self.client.force_authenticate(user=self.developer_user)
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.client.get(create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 0)

    def test_soft_deleted_endpoint_recreation_and_update(self):
        self.client.force_authenticate(user=self.admin_user)
        create_url = reverse("endpoint-list-create", kwargs={"version_uuid": self.version.uuid})

        # 1. Create an endpoint GET /test-endpoint
        response = self.client.post(create_url, {
            "method": "GET",
            "path": "/test-endpoint",
            "summary": "Original summary",
            "description": "Original desc",
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        endpoint_uuid = response.data["data"]["uuid"]

        # 2. Soft delete it
        detail_url = reverse("endpoint-detail", kwargs={"uuid": endpoint_uuid})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Confirm it is soft-deleted
        self.assertTrue(Endpoint.objects.get(uuid=endpoint_uuid).is_deleted)

        # 3. Try to recreate it (should restore and update)
        response = self.client.post(create_url, {
            "method": "GET",
            "path": "/test-endpoint",
            "summary": "Restored and updated summary",
            "description": "Restored desc",
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Confirm it's the same UUID and it's restored
        self.assertEqual(response.data["data"]["uuid"], str(endpoint_uuid))
        endpoint_obj = Endpoint.objects.get(uuid=endpoint_uuid)
        self.assertFalse(endpoint_obj.is_deleted)
        self.assertEqual(endpoint_obj.summary, "Restored and updated summary")
        self.assertEqual(endpoint_obj.description, "Restored desc")

        # 4. Soft delete it again
        self.client.delete(detail_url)
        self.assertTrue(Endpoint.objects.get(uuid=endpoint_uuid).is_deleted)

        # 5. Create another endpoint POST /another-endpoint
        response = self.client.post(create_url, {
            "method": "POST",
            "path": "/another-endpoint",
            "summary": "Another sum",
            "is_active": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        another_uuid = response.data["data"]["uuid"]

        # 6. Try to rename POST /another-endpoint to GET /test-endpoint (which is soft-deleted) -> should fail with 400 Bad Request
        detail_url_another = reverse("endpoint-detail", kwargs={"uuid": another_uuid})
        response = self.client.patch(detail_url_another, {
            "method": "GET",
            "path": "/test-endpoint"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class APIDocumentationTests(APITestCase):
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

        # Create a test API
        self.api = API.objects.create(
            name="Employee API",
            slug="employee-api",
            description="API for employee management.",
            status=API.Status.PUBLISHED,
            created_by=self.admin_user
        )

        # Create two versions: one active, one soft-deleted
        self.version_active = APIVersion.objects.create(
            api=self.api,
            version="v1",
            release_notes="Active version 1",
            is_latest=False,
            is_active=True
        )
        self.version_deleted = APIVersion.objects.create(
            api=self.api,
            version="v2",
            release_notes="Deleted version 2",
            is_latest=True,
            is_active=True,
            is_deleted=True
        )

        # Create endpoints under active version: one active, one soft-deleted
        self.endpoint_active = Endpoint.objects.create(
            version=self.version_active,
            method="GET",
            path="/employees",
            summary="Get employees",
            description="Returns all employees",
            is_active=True
        )
        self.endpoint_deleted = Endpoint.objects.create(
            version=self.version_active,
            method="POST",
            path="/employees",
            summary="Create employee",
            description="Creates an employee",
            is_active=True,
            is_deleted=True
        )

        # Authenticate developer client by default
        self.client.force_authenticate(user=self.developer_user)

    def test_retrieve_api_documentation_structure(self):
        doc_url = reverse("api-documentation", kwargs={"api_uuid": self.api.uuid})
        response = self.client.get(doc_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data["data"]
        self.assertEqual(data["uuid"], str(self.api.uuid))
        self.assertEqual(data["name"], "Employee API")
        self.assertEqual(data["slug"], "employee-api")
        self.assertEqual(data["description"], "API for employee management.")
        self.assertEqual(data["status"], "PUBLISHED")
        self.assertEqual(data["created_by"], self.admin_user.email)

        # Verify versions: only the active version should be returned
        versions = data["versions"]
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["uuid"], str(self.version_active.uuid))
        self.assertEqual(versions[0]["version"], "v1")
        self.assertFalse(versions[0]["is_latest"])

        # Verify endpoints: only the active endpoint should be returned
        endpoints = versions[0]["endpoints"]
        self.assertEqual(len(endpoints), 1)
        self.assertEqual(endpoints[0]["uuid"], str(self.endpoint_active.uuid))
        self.assertEqual(endpoints[0]["method"], "GET")
        self.assertEqual(endpoints[0]["path"], "/employees")

    def test_retrieve_api_documentation_unauthenticated_fails(self):
        self.client.force_authenticate(user=None)
        doc_url = reverse("api-documentation", kwargs={"api_uuid": self.api.uuid})
        response = self.client.get(doc_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_api_documentation_query_count(self):
        doc_url = reverse("api-documentation", kwargs={"api_uuid": self.api.uuid})
        
        # Warm up the cache/connection
        self.client.get(doc_url)
        
        # Measure query count
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(doc_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
        self.assertLessEqual(len(queries), 5)
