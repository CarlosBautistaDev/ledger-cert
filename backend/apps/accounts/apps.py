"""App config for ``accounts`` (authentication + RBAC)."""
from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Identity app: custom user, roles (Groups) and access sessions."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    verbose_name = "Cuentas y control de acceso"

    def ready(self) -> None:
        """Register access-audit and lockout signals at startup."""
        from . import signals  # noqa: F401  (registers access receivers)
        from . import axes_integration  # noqa: F401  (DRF lockout receiver)
