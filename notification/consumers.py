import json
from channels.db import database_sync_to_async
from .models import Notification
from channels.generic.websocket import AsyncWebsocketConsumer
from .serializers import *


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = f'notification_{self.scope["user"].username}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        notifications = await self.get_notification(self.scope['user'])
        if notifications:
            serializer = NotificationSerializer(notifications, many=True)
            await self.send(text_data=json.dumps({
                'notifications': serializer.data
            }))


    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({'message': event['message']}))

    @database_sync_to_async
    def get_notification(self, user):
        notifications = Notification.objects.filter(user=user, is_seen=False)
        return list(notifications)
