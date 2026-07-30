# dashboard/routing.py

# Purpose:
# - Defines WebSocket URLs for the Dashboard app.
# - Similar to urls.py, but routes WebSocket connections.
# - Maps "/ws/dashboard/" → DashboardConsumer.
# - .as_asgi() converts the Consumer class into an ASGI application that Channels can execute.


from django.urls import path
from .consumers import DashboardConsumer


# WebSocket URL routing.
# Maps the "/ws/dashboard/" WebSocket endpoint to DashboardConsumer.
websocket_urlpatterns = [
    path("ws/dashboard/", DashboardConsumer.as_asgi()),
]




