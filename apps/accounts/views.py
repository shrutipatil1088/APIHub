from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import AuthenticationService
from .serializers import RegisterSerializer,LoginSerializer,LoginResponseSerializer,LogoutSerializer,ProfileSerializer
from rest_framework.permissions import IsAuthenticated


from drf_spectacular.utils import extend_schema
from apps.core.responses import success_response


class RegisterAPIView(APIView):

    permission_classes = []

    @extend_schema(
        request=RegisterSerializer,
        responses={201: None},
        tags=["Authentication"],
        description="Register a new developer account.",
    )

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        AuthenticationService.register_user(
            serializer.validated_data
        )

        return success_response(
            message="User registered successfully.",
            status_code=status.HTTP_201_CREATED,
        )
    

class LoginAPIView(APIView):

    permission_classes = []

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        tags=["Authentication"],
        description="Login and receive JWT access and refresh tokens.",
    )
    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        tokens = AuthenticationService.login_user(
            serializer.validated_data["user"]
        )

        return success_response(
            data=tokens,
            message="Login successful.",
        )
    

class LogoutAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={200: None},
        tags=["Authentication"],
        description="Logout user by blacklisting refresh token.",
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        AuthenticationService.logout_user(
            serializer.validated_data["refresh"]
        )

        return success_response(
            message="Logout successful."
        )
    

class ProfileAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: ProfileSerializer},
        tags=["Profile"],
        description="Retrieve the authenticated user's profile.",
    )
    def get(self, request):
        user = AuthenticationService.get_profile(request.user)

        serializer = ProfileSerializer(user)

        return success_response(
            data=serializer.data,
            message="Profile fetched successfully.",
        )