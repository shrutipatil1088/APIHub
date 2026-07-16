from django.shortcuts import get_object_or_404

# Used to generate URL-friendly slugs.
from django.utils.text import slugify

from rest_framework.exceptions import ValidationError

from .models import API, APIVersion
from .filters import (
    APIFilter,
    ALLOWED_ORDERING_FIELDS,
    APIVersionFilter,
    ALLOWED_VERSION_ORDERING_FIELDS,
)

# Contains business logic for the API module.
class APIService:

    # Return API list with search, filter and ordering.
    @staticmethod
    def list_apis(query_params):
        ordering = query_params.get("ordering")

        if ordering and ordering not in ALLOWED_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        queryset = (
            API.objects
            .filter(is_deleted=False)
            .select_related("created_by")
        )

        return APIFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single API by UUID.
    @staticmethod
    def get_api(uuid):
        return get_object_or_404(
            API.objects.select_related("created_by"),
            uuid=uuid,
            is_deleted=False,
        )

    # Create a new API.
    @staticmethod
    def create_api(validated_data, user):
        validated_data["slug"] = slugify(
            validated_data["name"]
        )

        return API.objects.create(
            created_by=user,
            **validated_data,
        )
    
    # Update an existing API.
    @staticmethod
    def update_api(api, validated_data):
        if "name" in validated_data:
            validated_data["slug"] = slugify(
                validated_data["name"]
            )

        for field, value in validated_data.items():
            setattr(
                api,
                field,
                value,
            )

        api.save(
            update_fields=[
                *validated_data.keys(),
                "updated_at",
            ]
        )

        return api

    # Soft delete an API.
    @staticmethod
    def delete_api(api):
        api.soft_delete()


# Contains business logic for the API Version module.
class APIVersionService:

    # Return API Version list with search, filter and ordering.
    @staticmethod
    def list_versions(api_uuid, query_params):
        # Validate parent API exists and is not soft deleted.
        api = APIService.get_api(api_uuid)

        ordering = query_params.get("ordering")

        if ordering and ordering not in ALLOWED_VERSION_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_VERSION_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        queryset = (
            APIVersion.objects
            .filter(api=api, is_deleted=False)
            .select_related("api")
        )

        return APIVersionFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single API Version by UUID.
    @staticmethod
    def get_version(uuid):
        return get_object_or_404(
            APIVersion.objects.select_related("api"),
            uuid=uuid,
            is_deleted=False,
            api__is_deleted=False,
        )

    # Create a new API Version.
    @staticmethod
    def create_version(api, validated_data):
        return APIVersion.objects.create(
            api=api,
            **validated_data,
        )

    # Update an existing API Version.
    @staticmethod
    def update_version(version, validated_data):
        for field, value in validated_data.items():
            setattr(
                version,
                field,
                value,
            )

        version.save(
            update_fields=[
                *validated_data.keys(),
                "updated_at",
            ]
        )

        return version

    # Soft delete an API Version.
    @staticmethod
    def delete_version(version):
        version.soft_delete()