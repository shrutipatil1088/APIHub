# config/routing.py

# Purpose:
# - Central place to collect all WebSocket routes.
# - Combines WebSocket patterns from dashboard and notifications apps.

from apps.dashboard.routing import websocket_urlpatterns as dashboard_websocket_urlpatterns
from apps.notifications.routing import websocket_urlpatterns as notifications_websocket_urlpatterns


websocket_urlpatterns = [
    *dashboard_websocket_urlpatterns,
    *notifications_websocket_urlpatterns,
]
