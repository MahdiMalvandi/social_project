import json
import re

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from .serializers import MessageSerializer
from .models import Conversation, Message
from users.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling chat messages.
    """

    async def connect(self):
        """
        Connects a user to the WebSocket.
        """
        self.user = self.scope['user']
        username = self.scope['url_route']['kwargs']['username']
        token = self.scope['query_string'].decode("utf-8").split('=')[1]

        # Validate JWT token
        try:
            access_token = AccessToken(token)
            access_token.verify()
            user = await self.get_user_by_id(access_token.payload['user_id'])
            self.user = user
        except TokenError as e:
            await self.accept()
            await self.close_with_error(code=4001, error="Invalid Token")
            return

        try:
            participant = await self.get_user_by_username(username)
        except User.DoesNotExist:
            await self.accept({
                "type": "websocket.close",
                'code': 4001,
                'error': str("You cannot chat with a non-existent user")
            })
            return None


        # Check if conversation exists
        conversation = await self.get_or_create_conversation(participant)
        if conversation is None:
            await self.accept()
            await self.close_with_error(code=4001, error="Invalid Conversation ID")
            return

        # Check if user is a participant of the conversation
        if not await self.user_participant(conversation, self.user):
            await self.accept()
            await self.close_with_error(code=4001, error="You are not a participant")
            return

        self.room_id = conversation.id
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """
        Disconnects the user from the WebSocket.
        """
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """
        Receives a message from the WebSocket.
        """
        json_text = json.loads(text_data)
        message_text = json_text["message"]
        username = self.scope['url_route']['kwargs']['username']
        print(self.scope)

        try:
            participant = await self.get_user_by_username(username)
        except User.DoesNotExist:
            await self.accept({
                "type": "websocket.close",
                'code': 4001,
                'error': str("You cannot chat with a non-existent user")
            })
            return None

        # Get or create conversation
        conversation = await self.get_or_create_conversation(participant)

        # Save message
        message = await self.save_message(conversation, message_text, self.user)

        # Serialize message
        serializer = MessageSerializer(message, context={'user': self.user})
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

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        """
        Retrieve user by ID from the database.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user_by_username(self, username):
        """
        Retrieve user by username from the database.
        """
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_conversation(self, pk):
        """
        Retrieves a conversation by ID from the database.
        """
        try:
            return Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def user_participant(self, conversation, user):
        """
        Checks if a user is a participant of a conversation.
        """
        return user == conversation.receiver or user == conversation.initiator

    @database_sync_to_async
    def get_or_create_conversation(self, participant):
        """
        Retrieves or creates a conversation.
        """
        conversations = Conversation.objects.filter(
            Q(initiator=self.user, receiver=participant) |
            Q(initiator=participant, receiver=self.user)
        )
        if conversations.exists():
            return conversations.first()
        return Conversation.objects.create(initiator=self.user, receiver=participant)

    @database_sync_to_async
    def save_message(self, conversation, message, sender):
        """
        Saves a message to the database.
        """
        return Message.objects.create(
            sender=sender,
            text=message,
            conversation=conversation
        )

    async def close_with_error(self, code, error):
        """
        Closes the WebSocket with an error message.
        """
        await self.send(text_data=json.dumps({
            "type": "websocket.close",
            'code': code,
            'error': error
        }))
        await self.close()