from rest_framework import serializers
from django.contrib.auth import authenticate

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    confirm_password = serializers.CharField(
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "email",
            "full_name",
            "phone_number",
            "password",
            "confirm_password",
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs
    


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "uuid",
            "email",
            "full_name",
            "phone_number",
            "role",
            "is_verified",
        )


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "User account is inactive."
            )

        attrs["user"] = user

        return attrs