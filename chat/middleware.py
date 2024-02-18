from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import UntypedToken
from asgiref.sync import sync_to_async

User = get_user_model()


class JWTWebsocketMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        print('middleware run')
        print('authentication')
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_parameters = dict(qp.split('=') for qp in query_string.split('&'))
        token = query_parameters.get("token", None)

        if token is None:
            await send({
                "type": "websocket.close",
                'code': 4000
            })
        try:
            print('decoding started')
            # Decode the token
            decoded_data = UntypedToken(token).payload

            user_id = decoded_data['user_id']
            print(user_id)
            # Retrieve the user
            user = await self.get_user(user_id)
            if user is None:
                raise AuthenticationFailed("No such user found!")

            # You can do additional checks here if needed

            # If everything is fine, you can proceed
            # For example, you may set the user in the scope
            scope['user'] = user
            print('decoding ended')

        except (InvalidToken, TokenError, KeyError) as e:
            print('invalid token')
            await send({
                "type": "websocket.close",
                'code': 4001,
                'text': str(e)
            })
        print('all code ')
        return await super().__call__(scope, receive, send)

    @sync_to_async
    def get_user(self, user_id):
        user = User.objects.filter(id=user_id).first()
        return user
