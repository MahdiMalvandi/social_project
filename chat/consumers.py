import json
import re

from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.files.base import ContentFile
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from .serializers import MessageSerializer
from .models import *

from users.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling chat messages.
    """

    async def connect(self):
        """
        Connects a user to the WebSocket.
        """
        self.room_id = self.scope['url_route']['kwargs']['id']
        self.room_group_name = f'chat_{self.room_id}'

        # Retrieve conversation ID from URL
        pattern = r'(\d+)'
        match = re.search(pattern, self.scope['path'])
        conversation_id = match.group(1)

        # Check if conversation exists
        conversation = await self.get_conversation(pk=conversation_id)
        if conversation is None:
            await self.accept({
                "type": "websocket.close",
                'code': 4001,
                'error': str("Conversation id is invalid")
            })
            return None

        # Check if user is a participant of the conversation
        if not await self.user_participant(conversation, self.scope['user']):
            await self.accept({
                "type": "websocket.close",
                'code': 4001,
                'error': str("You are not allowed")
            })
            return None

        # Validate JWT token
        token = self.scope['query_string'].decode("utf-8").split('=')[1]
        try:
            access_token = AccessToken(token)
            access_token.verify()
            user = await self.get_user_by_id(access_token.payload['user_id'])
        except TokenError as e:
            raise InvalidToken(str(e))

        self.user = user

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """
        Retrieve user by ID from the database.
        """
        return User.objects.get(id=user_id)

    async def disconnect(self, close_code):
        """
        Disconnects the user from the WebSocket.
        """
        await self.channel_layer.group_discard(
            self.room_group_name if hasattr(self, 'room_group_name') else None,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Receives a message from the WebSocket.
        """
        json_text = json.loads(text_data)
        message_text = json_text["message"]
        sender = self.user

        # Get or create conversation
        conversation = await self.get_or_create_conversation(pk=self.scope['url_route']['kwargs']['id'])

        # Save message
        message = await self.save_message(conversation.id, message_text, sender)

        # Serialize message
        serializer = MessageSerializer(message, context={'user': self.scope['user']})
        serialized_message = serializer.data

        # Send serialized message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": serialized_message
            }
        )

    async def chat_message(self, event):
        """
        Sends a message to the WebSocket.
        """
        message = event['message']
        await self.send(text_data=json.dumps({"message": message}))

    async def get_or_create_conversation(self, pk=None):
        """
        Retrieves or creates a conversation by ID.
        """
        conversation = await sync_to_async(Conversation.objects.get)(pk=pk)
        return conversation

    async def save_message(self, conversation_id, message, sender):
        """
        Saves a message to the database.
        """
        mes = await sync_to_async(Message.objects.create)(
            sender=sender,
            text=message,
            conversation_id=conversation_id
        )
        return mes

    @sync_to_async
    def get_conversation(self, pk):
        """
        Retrieves a conversation by ID from the database.
        """
        try:
            con = Conversation.objects.get(pk=pk)
            return con
        except Conversation.DoesNotExist:
            return None

    @sync_to_async
    def user_participant(self, conversation, user):
        """
        Checks if a user is a participant of a conversation.
        """
        return user == conversation.receiver or user == conversation.initiator
