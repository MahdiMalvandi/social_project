from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path(r"ws/chat/<str:username>/", consumers.ChatConsumer.as_asgi()),
]
