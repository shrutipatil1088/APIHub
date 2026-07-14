from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterSerializer
from .services import AuthenticationService
from .serializers import LoginSerializer,LoginResponseSerializer


from drf_spectacular.utils import extend_schema

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

        return Response(
            {
                "message": "User registered successfully."
            },
            status=status.HTTP_201_CREATED,
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

        return Response(
            tokens,
            status=status.HTTP_200_OK,
        )