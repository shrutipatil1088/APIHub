from django.urls import reverse
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase


class HealthCheckAPITests(APITestCase):
    """
    Integration tests for the Health Check API endpoint and Redis caching.
    """

    def test_health_check_endpoint(self):
        url = reverse("health-check")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("service", response.data)
        self.assertIn("version", response.data)
        self.assertIn("database", response.data)
        self.assertIn("redis", response.data)
        self.assertEqual(response.data["service"], "APIHub")

    def test_redis_cache_operations(self):
        cache.set("test_key", "test_value", timeout=10)
        self.assertEqual(cache.get("test_key"), "test_value")
        cache.delete("test_key")
        self.assertIsNone(cache.get("test_key"))
