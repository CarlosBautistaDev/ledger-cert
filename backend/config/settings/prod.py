"""Production settings for the Ledger de Certificados.

Inherits from :mod:`config.settings.base` and hardens security. Selected with
``DJANGO_SETTINGS_MODULE=config.settings.prod``. TLS is terminated by the Caddy
proxy; ``X-Forwarded-Proto`` (set in base) is trusted for secure redirects.
"""
from __future__ import annotations

from .base import *  # noqa: F401,F403
from ._guards import require_secure_secrets

# Fail-fast: abort if SECRET_KEY / POSTGRES_PASSWORD / ADMIN_PASSWORD are still
# example/insecure values. SECRET_KEY signs the JWTs (HS256).
require_secure_secrets(
    secret_key=SECRET_KEY,  # noqa: F405
    db_password=DATABASES["default"]["PASSWORD"],  # noqa: F405
    admin_password=ADMIN_PASSWORD,  # noqa: F405
)

DEBUG: bool = False

SESSION_COOKIE_SECURE: bool = True
CSRF_COOKIE_SECURE: bool = True
SESSION_COOKIE_HTTPONLY: bool = True
SECURE_SSL_REDIRECT: bool = False  # the 80->443 redirect is done by Caddy
SECURE_HSTS_SECONDS: int = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
SECURE_HSTS_PRELOAD: bool = True
SECURE_CONTENT_TYPE_NOSNIFF: bool = True
X_FRAME_OPTIONS: str = "DENY"
