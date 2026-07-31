import json
from django.core.serializers.json import DjangoJSONEncoder
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from apps.accounts.models import User


class DashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket Consumer for real-time Dashboard analytics updates.
    - Admin users connect and join the 'dashboard_admin' channel group.
    - Developer users connect and join their unique 'dashboard_user_<user_id>' group.
    - Unauthenticated connections are rejected with close code 4001.
    """

    ADMIN_GROUP = "dashboard_admin"

    @classmethod
    async def encode_json(cls, content):
        """
        Custom JSON encoder using DjangoJSONEncoder to handle UUID, datetime, Decimal, etc.
        """
        return json.dumps(content, cls=DjangoJSONEncoder)

    async def connect(self):
        """
        Handles a new WebSocket connection.
        - Verifies user authentication.
        - Determines group based on user role (Admin vs Developer).
        - Joins the channel group before accepting the connection.
        """
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        if getattr(user, "role", None) == User.Role.ADMIN:
            self.group_name = self.ADMIN_GROUP
        else:
            self.group_name = f"dashboard_user_{user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when a WebSocket client disconnects.
        Removes the channel from the client's assigned group.
        """
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def admin_dashboard_update(self, event):
        """
        Handler for 'admin_dashboard_update' group messages.
        Forwards the payload to the connected Admin WebSocket client as JSON.
        """
        payload = event.get("payload", {})
        await self.send_json(payload)

    async def developer_dashboard_update(self, event):
        """
        Handler for 'developer_dashboard_update' group messages.
        Forwards the payload to the connected Developer WebSocket client as JSON.
        """
        payload = event.get("payload", {})
        await self.send_json(payload)

    async def dashboard_update(self, event):
        """
        Backward compatibility handler for generic 'dashboard_update' messages.
        """
        payload = event.get("payload", {})
        await self.send_json(payload)
