from .base import *



SITE_ID = 1

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "sqlite3.db"),
    },
}

STATICFILES_DIR = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_DIRS = [STATICFILES_DIR, ]
