# config/routing.py

# Purpose:
# - Central place to collect all WebSocket routes.
# - Similar to config/urls.py, but for WebSockets.
# - Imports routing.py from each app.
# - URLRouter in asgi.py uses this list to find the correct Consumer.



# Import WebSocket routes from the Dashboard app.
from apps.dashboard.routing import websocket_urlpatterns as dashboard_websocket_urlpatterns


# Combine WebSocket routes from all apps into a single routing table.
# (Similar to config/urls.py for HTTP routes.)
websocket_urlpatterns = [
    *dashboard_websocket_urlpatterns,
]
