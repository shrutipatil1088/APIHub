from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema

from apps.core.responses import success_response
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    LoginResponseSerializer,
    LogoutSerializer,
    ProfileSerializer,
)
from .services import AuthenticationService


# ============================================================================
# User Registration Endpoint
# ============================================================================
class RegisterAPIView(APIView):
    permission_classes = []

    @extend_schema(
        summary="Register User",
        description="""
Registers a new developer user account in the API Marketplace Platform.

Permissions:
- Public (Unauthenticated)

Validation rules:
- Requires a unique email address, full name, and strong password.
""",
        request=RegisterSerializer,
        responses={201: None},
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthenticationService.register_user(serializer.validated_data)

        return success_response(
            message="User registered successfully.",
            status_code=status.HTTP_201_CREATED,
        )


# ============================================================================
# User Login Endpoint
# ============================================================================
class LoginAPIView(APIView):
    permission_classes = []

    @extend_schema(
        summary="Authenticate User",
        description="""
Authenticates user credentials and returns JWT access and refresh tokens.

Permissions:
- Public (Unauthenticated)

Validation rules:
- Requires valid email and password credentials for an active user account.
""",
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = AuthenticationService.login_user(
            serializer.validated_data["user"]
        )

        return success_response(
            data=tokens,
            message="Login successful.",
        )


# ============================================================================
# Token Refresh Endpoint
# ============================================================================
@extend_schema(
    summary="Refresh Access Token",
    description="""
Refreshes an expired JWT access token using a valid refresh token.

Permissions:
- Public (Unauthenticated)

Validation rules:
- Requires a valid, unexpired, and unblacklisted refresh token.
""",
    tags=["Authentication"],
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


# ============================================================================
# User Logout Endpoint
# ============================================================================
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Logout User",
        description="""
Logs out the authenticated user by blacklisting their active JWT refresh token.

Permissions:
- Authenticated Users (JWT)

Validation rules:
- Requires a valid active refresh token.
""",
        request=LogoutSerializer,
        responses={200: None},
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthenticationService.logout_user(
            serializer.validated_data["refresh"]
        )

        return success_response(message="Logout successful.")


# ============================================================================
# User Profile Endpoint
# ============================================================================
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve User Profile",
        description="""
Retrieves detailed account information for the currently authenticated user.

Permissions:
- Authenticated Users (JWT)
""",
        responses={200: ProfileSerializer},
        tags=["Authentication"],
    )
    def get(self, request):
        user = AuthenticationService.get_profile(request.user)
        serializer = ProfileSerializer(user)

        return success_response(
            data=serializer.data,
            message="Profile fetched successfully.",
        )