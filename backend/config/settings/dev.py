"""Development settings for the Ledger de Certificados.

Inherits from :mod:`config.settings.base` and relaxes controls for local DX.
Selected with ``DJANGO_SETTINGS_MODULE=config.settings.dev`` (manage.py default).
"""
from __future__ import annotations

from typing import List

from .base import *  # noqa: F401,F403
from .base import env_bool, env_list

DEBUG: bool = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS: List[str] = env_list(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,api,proxy,0.0.0.0"
)

SESSION_COOKIE_SECURE: bool = False
CSRF_COOKIE_SECURE: bool = False
