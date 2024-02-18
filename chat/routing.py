from django.urls import path

from . import consumers

websocket_urlpatterns = [
    # path(r"ws/chat/<int:id>/", consumers.PersonalChatConsumer.as_asgi()),
    path(r"ws/chat/<int:id>/", consumers.ChatConsumer.as_asgi()),
    # path(r"ws/chat/<int:id>/", consumers.PersonalChatConsumer.as_asgi()),

]