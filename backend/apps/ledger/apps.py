"""App config for ``ledger`` (certificate domain)."""
from __future__ import annotations

from django.apps import AppConfig


class LedgerConfig(AppConfig):
    """Domain app: certificates of conformity (signed, immutable records)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ledger"
    verbose_name = "Ledger de Certificados"
