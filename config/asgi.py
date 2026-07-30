"""
ASGI configuration for APIHub project.

Exposes the ASGI application callable for HTTP and WebSocket protocols using
Django Channels, ProtocolTypeRouter, AuthMiddlewareStack, JWTAuthMiddleware, and AllowedHostsOriginValidator.

Daphne → ASGI → ProtocolTypeRouter → (HTTP → Django Views) | (WebSocket → Channels Consumers)
"""

import os
from urllib.parse import parse_qs
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from config.routing import websocket_urlpatterns


@database_sync_to_async
def get_user_from_token(token_string):
    """
    Decodes a JWT access token and retrieves the corresponding User.
    """
    try:
        access_token = AccessToken(token_string)
        user_id = access_token["user_id"]
        return User.objects.get(id=user_id, is_deleted=False)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    Custom Channels middleware that authenticates WebSocket connections
    using a JWT access token passed in the URL query string (e.g., ?token=<access_token>).
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token = query_params.get("token", [None])[0]

        if token:
            user = await get_user_from_token(token)
            if user and user.is_authenticated:
                scope["user"] = user

        return await self.inner(scope, receive, send)


# Route WebSocket URLs, attach JWT auth & AuthMiddlewareStack to the connection.
websocket_application = JWTAuthMiddleware(AuthMiddlewareStack(URLRouter(websocket_urlpatterns)))

# In production, only allow WebSocket connections from trusted hosts.
if not settings.DEBUG:
    websocket_application = AllowedHostsOriginValidator(websocket_application)


# Main ASGI entry point.
application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": websocket_application,
    }
)
