from django.contrib import admin

from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "name",
        "project",
        "subscription",
        "is_active",
        "created_at",
    )
    search_fields = (
        "name",
        "project__name",
        "project__developer__email",
    )
    list_filter = (
        "is_active",
        "is_deleted",
        "created_at",
    )
