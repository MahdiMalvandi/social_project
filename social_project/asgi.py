import os

from channels.routing import URLRouter, ProtocolTypeRouter
from channels.security.websocket import AllowedHostsOriginValidator  # new
from django.core.asgi import get_asgi_application
from chat import routing  # new
from notification import routing as notification_routing
from chat.middleware import JWTWebsocketMiddleware  # new

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_project.settings')

all_routings = routing.websocket_urlpatterns + notification_routing.websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket":  # new
        JWTWebsocketMiddleware(URLRouter(all_routings)),
})
