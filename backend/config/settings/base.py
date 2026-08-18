"""Base Django settings for the Ledger de Certificados de Conformidad.

Common settings for all environments (dev / prod). Environment-specific
variants live in ``config.settings.dev`` and ``config.settings.prod`` and are
selected via the ``DJANGO_SETTINGS_MODULE`` environment variable.

Everything is env-driven so the stack boots with ``docker compose up`` without
manual steps.
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List


def env_bool(name: str, default: bool = False) -> bool:
    """Read an environment variable as a boolean.

    Accepts ``1/0``, ``true/false``, ``yes/no`` (case-insensitive).

    :param name: environment variable name.
    :type name: str
    :param default: default value if the variable is missing.
    :type default: bool
    :returns: the parsed boolean value.
    :rtype: bool
    """
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> List[str]:
    """Read a comma-separated environment variable as a list.

    :param name: environment variable name.
    :type name: str
    :param default: default string if the variable is missing.
    :type default: str
    :returns: list of non-empty, stripped tokens.
    :rtype: List[str]
    """
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Base paths --------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

# --- Security ----------------------------------------------------------------
SECRET_KEY: str = os.environ.get("DJANGO_SECRET_KEY", "dev-insecure-change-me")
DEBUG: bool = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS: List[str] = env_list(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,api,proxy"
)

# --- Applications ------------------------------------------------------------
DJANGO_APPS: List[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS: List[str] = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "simple_history",
    "drf_spectacular",
    "axes",
    "pghistory",
    "pgtrigger",
]

LOCAL_APPS: List[str] = [
    "apps.accounts",
    "apps.ledger",
    "apps.audit",
]

INSTALLED_APPS: List[str] = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --- Middleware --------------------------------------------------------------
MIDDLEWARE: List[str] = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Propagates the request user to Historical* rows (simple-history).
    "simple_history.middleware.HistoryRequestMiddleware",
    # Propagates the actor to the pghistory context for DB-level attribution.
    # For JWT requests the actor is resolved inside the view, so the attribution
    # is set explicitly in a DRF layer (see apps.audit.pghistory_drf).
    "pghistory.middleware.HistoryMiddleware",
    # AxesMiddleware MUST be last: it observes the login result to count
    # failures and apply the lockout.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF: str = "config.urls"

TEMPLATES: List[Dict[str, Any]] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION: str = "config.wsgi.application"
ASGI_APPLICATION: str = "config.asgi.application"

# --- Database (PostgreSQL 17) ------------------------------------------------
DATABASES: Dict[str, Dict[str, Any]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "ledger"),
        "USER": os.environ.get("POSTGRES_USER", "ledger"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "changeme"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.environ.get("DJANGO_CONN_MAX_AGE", "60")),
    }
}

# --- Custom user model -------------------------------------------------------
AUTH_USER_MODEL: str = "accounts.User"

# ``AxesStandaloneBackend`` MUST be first: it short-circuits the login when the
# account is locked, before ``ModelBackend`` validates the password.
AUTHENTICATION_BACKENDS: List[str] = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# --- Password hashing Argon2id (Argon2 first) --------------------------------
PASSWORD_HASHERS: List[str] = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS: List[Dict[str, Any]] = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation."
        "MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internationalization ----------------------------------------------------
LANGUAGE_CODE: str = "es"
LANGUAGES: List[tuple] = [
    ("es", "Español"),
    ("en", "English"),
]
TIME_ZONE: str = os.environ.get("TZ", "UTC")
USE_I18N: bool = True
USE_TZ: bool = True

# --- Static files ------------------------------------------------------------
STATIC_URL: str = "/static/"
STATIC_ROOT: Path = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

# --- Django REST Framework ---------------------------------------------------
REST_FRAMEWORK: Dict[str, Any] = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": (
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
}

# --- SimpleJWT (access 15 min, refresh rotated + blacklist) ------------------
SIMPLE_JWT: Dict[str, Any] = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": (
        "apps.accounts.serializers.LedgerTokenObtainPairSerializer"
    ),
}

# --- drf-spectacular (OpenAPI) ----------------------------------------------
SPECTACULAR_SETTINGS: Dict[str, Any] = {
    "TITLE": "Ledger de Certificados de Conformidad — API",
    "DESCRIPTION": (
        "Registro de certificados de conformidad firmados e inmutables. "
        "API REST: autenticación, RBAC y ciclo de vida del certificado."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# --- CORS --------------------------------------------------------------------
CORS_ALLOWED_ORIGINS: List[str] = env_list(
    "CORS_ALLOWED_ORIGINS", "https://localhost"
)
CORS_ALLOW_CREDENTIALS: bool = True

# --- Security behind the Caddy proxy (internal TLS) --------------------------
SECURE_PROXY_SSL_HEADER: tuple = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS: List[str] = env_list(
    "CSRF_TRUSTED_ORIGINS", "https://localhost"
)

# --- Logging -----------------------------------------------------------------
LOGGING: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}

# --- django-axes: brute-force lockout (5 tries / 15 min) ---------------------
AXES_FAILURE_LIMIT: int = int(os.environ.get("AXES_FAILURE_LIMIT", "5"))
AXES_COOLOFF_TIME: timedelta = timedelta(
    minutes=int(os.environ.get("AXES_COOLOFF_MINUTES", "15"))
)
AXES_LOCKOUT_PARAMETERS: List[List[str]] = [["username", "ip_address"]]
AXES_IPWARE_META_PRECEDENCE_ORDER: tuple = (
    "HTTP_X_FORWARDED_FOR",
    "REMOTE_ADDR",
)
AXES_USERNAME_FORM_FIELD: str = "email"
AXES_USERNAME_CALLABLE: str = "apps.accounts.axes_integration.get_username"
AXES_RESET_ON_SUCCESS: bool = True
AXES_ENABLED: bool = env_bool("AXES_ENABLED", True)

# --- Seed (entrypoint, idempotent) -------------------------------------------
ADMIN_EMAIL: str = os.environ.get("ADMIN_EMAIL", "admin@ledger.local")
ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "Admin12345!")
