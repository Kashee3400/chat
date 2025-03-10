"""
WSGI config for wannachat project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)

if DEBUG:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wannachat.settings.local')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wannachat.settings.production')

application = get_wsgi_application()
