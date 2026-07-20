from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Use SQLite (or your preferred dev DB)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Optional: email backend for console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"