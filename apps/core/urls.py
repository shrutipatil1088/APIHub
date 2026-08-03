from django.urls import path
from .views import (
    HealthCheckAPIView,
    TestCeleryAPIView,
    GenerateDailyReportAPIView,
    SubscriptionReminderAPIView,
)

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
    path(
        "generate-report/",
        GenerateDailyReportAPIView.as_view(),
        name="generate-daily-report",
    ),
    path(
        "subscription-reminder/",
        SubscriptionReminderAPIView.as_view(),
        name="subscription-reminder",
    ),
]