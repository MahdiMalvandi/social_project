import re

from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from asgiref.sync import sync_to_async
from .models import *

User = get_user_model()


class JWTWebsocketMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_parameters = dict(qp.split('=') for qp in query_string.split('&'))
        token = query_parameters.get("token", None)

        pattern = r'(\d+)'
        match = re.search(pattern, scope['path'])
        conversation_id = match.group(1)

        conversation = await self.get_coversation(pk=conversation_id)
        if conversation is None:
            await send({
                "type": "websocket.close",
                'code': 4001,
                'error': str("Conversation id is invalid")
            })

        if token is None:
            await send({
                "type": "websocket.close",
                'code': 4000
            })
        try:
            # Decode the token
            decoded_data = UntypedToken(token).payload

            user_id = decoded_data['user_id']
            # Retrieve the user
            user = await self.get_user(user_id)
            if user is None:
                raise AuthenticationFailed("No such user found!")

            # You can do additional checks here if needed

            # If everything is fine, you can proceed
            # For example, you may set the user in the scope
            scope['user'] = user
            if not await self.user_participant(conversation, user):
                await send({
                    "type": "websocket.close",
                    'code': 4001,
                    'error': str("You are not allowed")
                })
        except (InvalidToken, TokenError, KeyError) as e:
            await send({
                "type": "websocket.close",
                'code': 4001,
                'text': str(e)
            })
        return await super().__call__(scope, receive, send)

    @sync_to_async
    def get_user(self, user_id):
        user = User.objects.filter(id=user_id).first()
        return user

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

