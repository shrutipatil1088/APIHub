from django.conf import settings
from django.db import connection
from django.core.cache import caches
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, inline_serializer

from .tasks import say_hello, generate_daily_report, check_subscription_reminders


class HealthCheckAPIView(APIView):
    """
    Health check endpoint verifying system, database, and Redis connectivity.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Health Check",
        description="""
Checks system health, service operational status, database connectivity, and Redis cache connectivity.

Permissions:
- Public (Unauthenticated)
""",
        request=None,
        responses={
            200: inline_serializer(
                name="HealthCheckResponse",
                fields={
                    "status": serializers.CharField(),
                    "service": serializers.CharField(),
                    "version": serializers.CharField(),
                    "database": serializers.CharField(),
                    "redis": serializers.CharField(),
                },
            )
        },
        tags=["Health Check"],
    )
    def get(self, request):
        # 1. Verify PostgreSQL connectivity
        try:
            connection.ensure_connection()
            database_status = "connected"
        except Exception:
            database_status = "disconnected"

        # 2. Verify Redis connectivity & clean up ping key
        try:
            cache = caches["default"]
            cache.set("health_check_ping", "pong", timeout=5)
            if cache.get("health_check_ping") == "pong":
                redis_status = "connected"
            else:
                redis_status = "disconnected"
            cache.delete("health_check_ping")
        except Exception:
            redis_status = "disconnected"

        is_healthy = (database_status == "connected" and redis_status == "connected")
        version = getattr(settings, "API_VERSION", "1.0.0")

        return Response(
            {
                "status": "ok" if is_healthy else "error",
                "service": "APIHub",
                "version": version,
                "database": database_status,
                "redis": redis_status,
            }
        )


class TestCeleryAPIView(APIView):
    """
    Temporary DRF API endpoint for learning Celery basics.
    Triggers say_hello.delay() asynchronously.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Trigger Test Celery Task",
        description="""
Triggers the say_hello Celery task asynchronously using .delay().

Permissions:
- Public (Unauthenticated)
""",
        request=None,
        responses={
            200: inline_serializer(
                name="TestCeleryResponse",
                fields={
                    "message": serializers.CharField(),
                },
            )
        },
        tags=["Celery Learning"],
    )
    def post(self, request):
        # Trigger the Celery task asynchronously.
        # .delay() doesn't execute the function directly.
        # It sends a task message to Redis queue and returns control immediately.
        say_hello.delay()

        return Response(
            {"message": "Task queued successfully."},
            status=status.HTTP_200_OK,
        )


class GenerateDailyReportAPIView(APIView):
    """
    Temporary DRF API endpoint for learning Celery database tasks.
    Triggers generate_daily_report.delay() asynchronously.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Trigger Daily Platform Report Task",
        description="""
Triggers the generate_daily_report Celery task asynchronously using .delay().
Queries database metrics in the background worker and prints/logs the daily report.

Permissions:
- Public (Unauthenticated)
""",
        request=None,
        responses={
            200: inline_serializer(
                name="GenerateDailyReportResponse",
                fields={
                    "message": serializers.CharField(),
                },
            )
        },
        tags=["Celery Learning"],
    )
    def post(self, request):
        # Trigger the daily report task asynchronously.
        # Returns control immediately without waiting for database query completion.
        generate_daily_report.delay()

        return Response(
            {"message": "Daily report task queued successfully."},
            status=status.HTTP_200_OK,
        )


class SubscriptionReminderAPIView(APIView):
    """
    Temporary DRF API endpoint for learning Celery subscription reminder tasks.
    Triggers check_subscription_reminders.delay() asynchronously.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Trigger Subscription Reminder Task",
        description="""
Triggers the check_subscription_reminders Celery task asynchronously using .delay().
Queries active subscriptions expiring in 3 days and sends WebSocket notifications to developers.

Permissions:
- Public (Unauthenticated)
""",
        request=None,
        responses={
            200: inline_serializer(
                name="SubscriptionReminderResponse",
                fields={
                    "message": serializers.CharField(),
                },
            )
        },
        tags=["Celery Learning"],
    )
    def post(self, request):
        # Trigger the subscription reminder task asynchronously.
        # Returns control immediately without waiting for task completion.
        check_subscription_reminders.delay()

        return Response(
            {"message": "Subscription reminder task queued successfully."},
            status=status.HTTP_200_OK,
        )