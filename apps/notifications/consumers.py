# Used for converting Python objects into JSON.
import json
from django.core.serializers.json import DjangoJSONEncoder
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from apps.accounts.models import User


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket Consumer for real-time Notifications.
    - Admin users connect and join the 'notifications_admin' channel group.
    - Developer users connect and join their unique 'notifications_user_<user_id>' group.
    - Unauthenticated connections are rejected with close code 4001.
    """

    ADMIN_GROUP = "notifications_admin"

    # encode_json : Uses DjangoJSONEncoder so objects like UUID and datetime can be converted to JSON.
    @classmethod
    async def encode_json(cls, content):
        """
        Custom JSON encoder using DjangoJSONEncoder to handle UUID, datetime, etc.
        """
        return json.dumps(content, cls=DjangoJSONEncoder)

    async def connect(self):
        """
        Handles a new WebSocket connection for Notifications.
        Verifies authentication, joins role-based group, and accepts connection.
        """
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        if getattr(user, "role", None) == User.Role.ADMIN:
            self.group_name = self.ADMIN_GROUP
        else:
            self.group_name = f"notifications_user_{user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        """
        Removes the connection from assigned notifications group on disconnect.
        """
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def notification_created(self, event):
        """
        Handler for 'notification_created' group messages.
        Forwards the payload to the connected client as JSON.
        It is called from service file when a new notification is created and sent to the group.
        """
        payload = event.get("payload", {})
        await self.send_json(payload)
