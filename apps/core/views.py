from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import connection

from drf_spectacular.utils import extend_schema


class HealthCheckAPIView(APIView):
    """
    Health check endpoint.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Health Check"],
        description="Check if the API service is running.",
        responses={
            200: {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "service": {"type": "string"},
                    "version": {"type": "string"},
                },
            }
        },
    )
    def get(self, request):
        try:
            connection.ensure_connection()
            database_status = "connected"
        except Exception:
            database_status = "disconnected"
            
        return Response(
            {
                "status": "ok" if database_status == "connected" else "error",
                "service": "APIHub",
                "version": "1.0.0",
                "database": database_status,
            }
        )