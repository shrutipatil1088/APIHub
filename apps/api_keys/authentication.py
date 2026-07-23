from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .services import APIKeyService


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication scheme for validating API Keys in request headers.
    Checks 'X-API-Key' header or 'Authorization: Api-Key <key>'.
    """

    def authenticate(self, request):
        api_key_header = request.headers.get("X-API-Key")

        if not api_key_header:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Api-Key "):
                api_key_header = auth_header.split("Api-Key ")[1].strip()

        if not api_key_header:
            return None  # Pass through to other authentication methods

        user, api_key = APIKeyService.authenticate_key(api_key_header)
        return (user, api_key)

    def authenticate_header(self, request):
        return 'Api-Key realm="api"'
