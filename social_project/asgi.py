import os

from channels.routing import URLRouter, ProtocolTypeRouter
from channels.security.websocket import AllowedHostsOriginValidator  # new
from django.core.asgi import get_asgi_application
from chat import routing  # new
from chat.middleware import JWTWebsocketMiddleware  # new

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket":   # new
        JWTWebsocketMiddleware(URLRouter(routing.websocket_urlpatterns))
})