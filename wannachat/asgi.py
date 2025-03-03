import os
import django
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from decouple import config

# Set Django settings module BEFORE calling django.setup()
DEBUG = config("DEBUG", default=False, cast=bool)

if DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wannachat.settings.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wannachat.settings.production")

# Now setup Django
django.setup()
from wannachat import routing  # noqa

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        ),
    }
)
