from django.shortcuts import get_object_or_404

# Used to generate URL-friendly slugs.
from django.utils.text import slugify

from rest_framework.exceptions import ValidationError

from .models import API
from .filters import (
    APIFilter,
    ALLOWED_ORDERING_FIELDS,
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