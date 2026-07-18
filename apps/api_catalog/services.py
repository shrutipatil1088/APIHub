from django.shortcuts import get_object_or_404
from django.db.models import Prefetch

# Used to generate URL-friendly slugs.
from django.utils.text import slugify

from rest_framework.exceptions import ValidationError

from .models import API, APIVersion, Endpoint
from .filters import (
    APIFilter,
    ALLOWED_ORDERING_FIELDS,
    APIVersionFilter,
    ALLOWED_VERSION_ORDERING_FIELDS,
    EndpointFilter,
    ALLOWED_ENDPOINT_ORDERING_FIELDS,
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

    # Fetch API documentation by UUID.
    @staticmethod
    def get_api_documentation(api_uuid):
        return get_object_or_404(
            API.objects.select_related("created_by").prefetch_related(
                Prefetch(
                    "versions",
                    queryset=APIVersion.objects.filter(
                        is_deleted=False
                    ).prefetch_related(
                        Prefetch(
                            "endpoints",
                            queryset=Endpoint.objects.filter(
                                is_deleted=False
                            )
                        )
                    )
                )
            ),
            uuid=api_uuid,
            is_deleted=False,
        )


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
        version_str = validated_data.get("version")
        existing_version = APIVersion.objects.filter(
            api=api,
            version=version_str,
        ).first()

        if existing_version:
            existing_version.restore()
            for field, value in validated_data.items():
                setattr(existing_version, field, value)
            existing_version.save()
            return existing_version

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


# Contains business logic for the API Endpoint module.
class EndpointService:

    # Return Endpoint list with search, filter and ordering.
    @staticmethod
    def list_endpoints(version_uuid, query_params):
        # Validate parent API version exists and is not soft deleted.
        version = APIVersionService.get_version(version_uuid)

        ordering = query_params.get("ordering")

        if ordering and ordering not in ALLOWED_ENDPOINT_ORDERING_FIELDS:
            raise ValidationError(
                {
                    "ordering": [
                        (
                            "Invalid ordering field. Allowed values are: "
                            f"{', '.join(sorted(ALLOWED_ENDPOINT_ORDERING_FIELDS))}."
                        )
                    ]
                }
            )

        queryset = (
            Endpoint.objects
            .filter(version=version, is_deleted=False)
            .select_related("version", "version__api")
        )

        return EndpointFilter(
            query_params,
            queryset=queryset,
        ).qs

    # Fetch a single Endpoint by UUID.
    @staticmethod
    def get_endpoint(uuid):
        return get_object_or_404(
            Endpoint.objects.select_related("version", "version__api"),
            uuid=uuid,
            is_deleted=False,
            version__is_deleted=False,
            version__api__is_deleted=False,
        )

    # Create a new Endpoint.
    @staticmethod
    def create_endpoint(version, validated_data):
        method = validated_data.get("method")
        path = validated_data.get("path")
        existing_endpoint = Endpoint.objects.filter(
            version=version,
            method=method,
            path=path,
        ).first()

        if existing_endpoint:
            existing_endpoint.restore()
            for field, value in validated_data.items():
                setattr(existing_endpoint, field, value)
            existing_endpoint.save()
            return existing_endpoint

        return Endpoint.objects.create(
            version=version,
            **validated_data,
        )

    # Update an existing Endpoint.
    @staticmethod
    def update_endpoint(endpoint, validated_data):
        for field, value in validated_data.items():
            setattr(
                endpoint,
                field,
                value,
            )

        endpoint.save(
            update_fields=[
                *validated_data.keys(),
                "updated_at",
            ]
        )

        return endpoint

    # Soft delete an Endpoint.
    @staticmethod
    def delete_endpoint(endpoint):
        endpoint.soft_delete()