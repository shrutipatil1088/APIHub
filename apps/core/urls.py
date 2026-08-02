from django.urls import path
from .views import HealthCheckAPIView, TestCeleryAPIView

urlpatterns = [
    path(
        "health/",
        HealthCheckAPIView.as_view(),
        name="health-check",
    ),
    path(
        "test-celery/",
        TestCeleryAPIView.as_view(),
        name="test-celery",
    ),
]