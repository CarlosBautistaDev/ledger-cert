"""App config for ``audit`` (audit trail of the Ledger)."""
from __future__ import annotations

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Cross-cutting audit app: append-only access log + pghistory glue."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    verbose_name = "Auditoría"
