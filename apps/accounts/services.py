from .models import User
from rest_framework_simplejwt.tokens import RefreshToken


class AuthenticationService:

    @staticmethod
    def register_user(validated_data):
        validated_data.pop("confirm_password")

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data,
        )

        return user
    

    @staticmethod
    def login_user(user):
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "uuid": str(user.uuid),
                "email": user.email,
                "full_name": user.full_name,
                "phone_number": user.phone_number,
                "role": user.role,
                "is_verified": user.is_verified,
            },
        }