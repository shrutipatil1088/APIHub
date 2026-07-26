from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .filters import DeveloperFilter, ALLOWED_DEVELOPER_ORDERING_FIELDS


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

    @staticmethod
    def logout_user(refresh_token):
        token = RefreshToken(refresh_token)
        token.blacklist()

    @staticmethod
    def get_profile(user):
        return user

    @staticmethod
    def list_developers(query_params):
        """
        Returns filtered, searched, and ordered developer users.
        """
        ordering = query_params.get("ordering")
        if ordering and ordering not in ALLOWED_DEVELOPER_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_DEVELOPER_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        queryset = User.objects.filter(
            role=User.Role.DEVELOPER,
            is_deleted=False,
        )

        return DeveloperFilter(
            query_params,
            queryset=queryset,
        ).qs

    @staticmethod
    def get_developer(uuid):
        """
        Fetches a single developer user by UUID.
        """
        return get_object_or_404(
            User,
            uuid=uuid,
            role=User.Role.DEVELOPER,
            is_deleted=False,
        )