"""ASGI entry point for the Ledger de Certificados.

Available for future async deployments. The default settings module is
production; dev overrides it via ``DJANGO_SETTINGS_MODULE``.
"""
from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_asgi_application()
