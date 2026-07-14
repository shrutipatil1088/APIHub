from django.urls import path

from .views import RegisterAPIView,LoginAPIView,LogoutAPIView,ProfileAPIView
from rest_framework_simplejwt.views import TokenRefreshView

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
        TokenRefreshView.as_view(),
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
]