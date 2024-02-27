import json
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Notification
from .serializers import NotificationSerializer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling notifications.
    """

    async def connect(self):
        """
        Connects the WebSocket consumer.
        """
        self.group_name = f'notification_{self.scope["user"].username}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Send existing notifications to the client upon connection
        notifications = await self.get_notification(self.scope['user'])
        if notifications:
            serializer = NotificationSerializer(notifications, many=True)
            await self.send(text_data=json.dumps({
                'notifications': serializer.data
            }))

    async def disconnect(self, close_code):
        """
        Disconnects the WebSocket consumer.
        """
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        """
        Sends a notification to the WebSocket consumer.
        """
        await self.send(text_data=json.dumps({'message': event['message']}))

    @database_sync_to_async
    def get_notification(self, user):
        """
        Retrieves unread notifications for a user from the database.

        Parameters:
            user (User): The user for whom to retrieve notifications.

        Returns:
            list: List of unread notifications for the user.
        """
        notifications = Notification.objects.filter(user=user, is_seen=False)
        return list(notifications)
