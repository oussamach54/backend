# my_project/settings.py
import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

from __future__ import annotations


# ---------------------------------------------------------------------
# BASE & ENV
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
# charge .env pour le dev local uniquement (inoffensif en prod)
load_dotenv(BASE_DIR / ".env")

def _split_env_list(value: str | None, default: str = ""):
    raw = (value if value is not None else default)
    return [x.strip() for x in raw.split(",") if x.strip()]

# ---------------------------------------------------------------------
# CORE
# ---------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me"  # fallback dev seulement
)
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"

# En dev: autorise tout si DEBUG=True, sinon prends la liste fournie
if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = _split_env_list(os.environ.get("DJANGO_ALLOWED_HOSTS", ""))

ROOT_URLCONF = "my_project.urls"
WSGI_APPLICATION = "my_project.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------
# APPS
# ---------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd-party
    "rest_framework",
    "corsheaders",

    # Local
    "product",
    "payments",
    "account",
    "newsletter",
]

# ---------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Whitenoise DOIT être juste après SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    # CORS avant CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ---------------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # emails/password_reset.html etc.
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get(
            "DATABASE_URL",
            # fallback dev local — à surcharger en prod via Coolify
            "postgres://postgres:postgres@localhost:5432/ecommerce_db"
        ),
        conn_max_age=600,
        ssl_require=False,  # réseau interne Coolify, pas besoin d'SSL
    )
}

# ---------------------------------------------------------------------
# AUTH / JWT / DRF
# ---------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=300),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
}

# ---------------------------------------------------------------------
# STATIC / MEDIA
# ---------------------------------------------------------------------
STATIC_URL = "/static/"
MEDIA_URL  = "/images/"

# Emplacements overridables par env (utile pour monter des volumes)
STATIC_ROOT = os.environ.get("STATIC_ROOT", str(BASE_DIR / "staticfiles"))
MEDIA_ROOT  = os.environ.get("MEDIA_ROOT",  str(BASE_DIR / "static" / "images"))

# Django 4.2+ storage API
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    # IMPORTANT: Whitenoise Manifest (cache-busting)
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------
# I18N / TZ
# ---------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.environ.get("TZ", "Africa/Casablanca")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------
# CORS / CSRF
# ---------------------------------------------------------------------
if DEBUG:
    # Dev: permissif
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []
else:
    # Prod: whitelist stricte
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = _split_env_list(os.environ.get("CORS_ALLOWED_ORIGINS", ""))

CSRF_TRUSTED_ORIGINS = _split_env_list(
    os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost:3000")
)

# ---------------------------------------------------------------------
# FRONTEND & BUSINESS SETTINGS
# ---------------------------------------------------------------------
FRONTEND_URL   = os.environ.get("FRONTEND_URL", "http://localhost:3000")
WHATSAPP_ADMIN = os.environ.get("WHATSAPP_ADMIN", "2126XXXXXXXX")  # digits only

# ---------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------
# Par défaut en dev: console (pas d’envoi réel)
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = os.environ.get(
        "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
    )

EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    f"MiniGlow <{EMAIL_HOST_USER or 'no-reply@miniglow.ma'}>",
)

# sécurité: ne pas activer TLS et SSL simultanément
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ValueError("EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True.")

# ---------------------------------------------------------------------
# SECURITY (derrière reverse proxy / HTTPS)
# ---------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))  # augmente après validation SSL
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django.core.mail": {"handlers": ["console"], "level": "DEBUG"},
        "django.security.DisallowedHost": {"handlers": ["console"], "level": "ERROR"},
    },
}
