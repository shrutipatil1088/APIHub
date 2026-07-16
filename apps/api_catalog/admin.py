from django.contrib import admin

from .models import API, APIVersion, Endpoint


@admin.register(API)
class APIAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = (
        "status",
        "created_at",
    )
    search_fields = (
        "name",
        "slug",
    )
    ordering = ("name",)


@admin.register(APIVersion)
class APIVersionAdmin(admin.ModelAdmin):
    list_display = (
        "api",
        "version",
        "is_latest",
        "created_at",
    )
    list_filter = (
        "is_latest",
    )
    search_fields = (
        "api__name",
        "version",
    )
    ordering = ("-created_at",)


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = (
        "method",
        "path",
        "version",
    )
    list_filter = (
        "method",
    )
    search_fields = (
        "path",
        "summary",
    )
    ordering = ("path",)