"""Localisation famille — backend autonome (séparé de wifimobiletv).
Transparence d'abord : l'enfant voit le partage et peut le couper (sharing_on).
Config par variables d'environnement pour la production (voir .env.famille.example)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _bool(v, default=False):
    return str(os.environ.get(v, default)).lower() in ("1", "true", "yes", "on")


SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me-en-prod")
DEBUG = _bool("DEBUG", True)                      # prod : DEBUG=0
ALLOWED_HOSTS = [h.strip() for h in os.environ.get(
    "ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get(
    "CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "rest_framework.authtoken",
    "famille",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates",
             "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True, "OPTIONS": {}}]
WSGI_APPLICATION = "config.wsgi.application"

# Base : Postgres si DATABASE_URL fourni (prod), sinon SQLite (dev/tests).
_db = os.environ.get("DATABASE_URL", "")
if _db:
    import dj_database_url  # type: ignore
    DATABASES = {"default": dj_database_url.parse(_db, conn_max_age=600)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.TokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}

# Derrière Caddy (HTTPS) : respecte l'en-tête de proxy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_TZ = True
TIME_ZONE = "UTC"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
POSITION_RETENTION_DAYS = int(os.environ.get("POSITION_RETENTION_DAYS", "30"))
