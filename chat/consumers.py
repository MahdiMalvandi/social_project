import json
import re

from asgiref.sync import async_to_sync, sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from django.core.files.base import ContentFile
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from .serializers import MessageSerializer
from .models import *

from users.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['id']
        self.room_group_name = f'chat_{self.room_id}'

        pattern = r'(\d+)'
        match = re.search(pattern, self.scope['path'])
        conversation_id = match.group(1)
        conversation = await self.get_coversation(pk=conversation_id)
        if conversation is None:
            await self.accept({
                "type": "websocket.close",
                'code': 4001,
                'error': str("Conversation id is invalid")
            })
            return None
        if not await self.user_participant(conversation, self.scope['user']):
            await self.accept({
                "type": "websocket.close",
                'code': 4001,
                'error': str("You are not allowed")
            })
            return None


        token = self.scope['query_string'].decode("utf-8").split('=')[1]
        try:
            # Parse the token
            access_token = AccessToken(token)
            # Validate the token
            access_token.verify()
            # Return the user associated with the token
            user = await self.get_user_by_id(access_token.payload['user_id'])
        except TokenError as e:

            # If token is invalid, raise an InvalidToken exception
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
        # Retrieve the user from the database using the user_id
        return User.objects.get(id=user_id)

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name if hasattr(self, 'room_group_name') else None,
            self.channel_name
        )

    async def receive(self, text_data):
        json_text = json.loads(text_data)
        message_text = json_text["message"]
        sender = self.user

        # Get or create conversation
        conversation = await self.get_or_create_conversation(pk=self.scope['url_route']['kwargs']['id'])

        # Create a new message object
        message = await self.save_message(conversation.id, message_text, sender)

        # Serialize the message

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
        message = event['message']

        # Send message to WebSocke
        await self.send(text_data=json.dumps({"message": message}))

    async def get_or_create_conversation(self, pk=None):
        conversation = await sync_to_async(Conversation.objects.get)(pk=pk)
        return conversation

    async def save_message(self, conversation_id, message, sender):
        # Save the message to database
        mes = await sync_to_async(Message.objects.create)(
            sender=sender,
            text=message,
            conversation_id=conversation_id
        )
        return mes

    @sync_to_async
    def get_coversation(self, pk):
        try:
            con = Conversation.objects.get(pk=pk)
            return con
        except Conversation.DoesNotExist:
            return None


    @sync_to_async
    def user_participant(self, conversation, user):
        return user == conversation.receiver or user == conversation.initiator

