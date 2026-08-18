"""WSGI entry point for the Ledger de Certificados.

Used by gunicorn in the ``api`` container. The default settings module is
production; dev overrides it via ``DJANGO_SETTINGS_MODULE``.
"""
from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

application = get_wsgi_application()
