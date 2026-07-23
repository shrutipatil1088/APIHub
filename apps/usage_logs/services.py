import time

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from .filters import UsageLogFilter, ALLOWED_ORDERING_FIELDS
from .models import UsageLog


class UsageLogService:
    """
    Contains business logic for the UsageLog module.
    """

    # Helper method to extract client IP address from HTTP request headers.
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    # Return UsageLog list with search, filter and ordering.
    @staticmethod
    def list_logs(user, query_params):
        ordering = query_params.get("ordering")

        if ordering and ordering not in ALLOWED_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        # Admin can see all logs, developer sees only logs for their own projects
        if user.role == User.Role.ADMIN:
            queryset = (
                UsageLog.objects
                .filter(is_deleted=False)
                .select_related("project", "api_key")
            )
        else:
            queryset = (
                UsageLog.objects
                .filter(
                    project__developer=user,
                    is_deleted=False,
                )
                .select_related("project", "api_key")
            )

        return UsageLogFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single UsageLog by UUID.
    @staticmethod
    def get_log(uuid):
        return get_object_or_404(
            UsageLog.objects.select_related(
                "project",
                "api_key",
                "project__developer",
            ),
            uuid=uuid,
            is_deleted=False,
        )

    # Create a new usage log entry.
    @staticmethod
    def create_log(**kwargs):
        return UsageLog.objects.create(
            **kwargs,
        )

    # Automatically record a usage log for an authenticated API key request.
    @staticmethod
    def log_request(request, response, start_time):
        end_time = time.perf_counter()
        response_time_ms = int((end_time - start_time) * 1000)

        # Retrieve authenticated APIKey from request.auth
        api_key = getattr(request, "auth", None)
        if not api_key or not hasattr(api_key, "project"):
            return None

        ip_address = UsageLogService.get_client_ip(request)
        user_agent = request.headers.get("User-Agent") or request.META.get("HTTP_USER_AGENT")

        return UsageLogService.create_log(
            project=api_key.project,
            api_key=api_key,
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent,
        )
