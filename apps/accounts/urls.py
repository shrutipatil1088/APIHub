from django.urls import path

from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    ProfileAPIView,
    CustomTokenRefreshView,
    DeveloperListAPIView,
    DeveloperDetailAPIView,
)

urlpatterns = [
    path(
        "register/",
        RegisterAPIView.as_view(),
        name="register",
    ),
    path(
        "login/",
        LoginAPIView.as_view(),
        name="login",
    ),
    path(
        "refresh/",
        CustomTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "logout/",
        LogoutAPIView.as_view(),
        name="logout",
    ),
    path(
        "profile/",
        ProfileAPIView.as_view(),
        name="profile",
    ),
    path(
        "developers/",
        DeveloperListAPIView.as_view(),
        name="developer-list",
    ),
    path(
        "developers/<uuid:uuid>/",
        DeveloperDetailAPIView.as_view(),
        name="developer-detail",
    ),
]