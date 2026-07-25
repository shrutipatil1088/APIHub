"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)



urlpatterns = [
    path("admin/", admin.site.urls),

    # OpenAPI Schema
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

    # Swagger UI
    path("api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # ReDoc
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    path("api/v1/", include("apps.core.urls")),

    # Authentication APIs
    path("api/v1/auth/", include("apps.accounts.urls")),

    # API Catalog APIs
    path("api/v1/apis/", include("apps.api_catalog.urls")),

    # Subscriptions and Plans APIs
    path("api/v1/", include("apps.subscriptions.urls")),

    # Developer Projects APIs
    path("api/v1/", include("apps.developer_projects.urls")),

    # API Keys APIs
    path("api/v1/", include("apps.api_keys.urls")),

    # Usage Logs APIs
    path("api/v1/", include("apps.usage_logs.urls")),

    # Dashboard APIs
    path("api/v1/", include("apps.dashboard.urls")),
]




