from django.contrib import admin

from .models import UsageLog


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "project",
        "method",
        "endpoint",
        "status_code",
        "response_time_ms",
        "requested_at",
    )
    search_fields = (
        "endpoint",
        "project__name",
        "project__developer__email",
        "ip_address",
    )
    list_filter = (
        "method",
        "status_code",
        "requested_at",
    )
