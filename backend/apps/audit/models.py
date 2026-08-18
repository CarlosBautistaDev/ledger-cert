"""Models for the ``audit`` app: append-only access log.

Two audit layers:

1. **Version history** of domain models — implemented with
   ``django-simple-history`` (``HistoricalRecords``) directly on the tracked
   models, plus ``django-pghistory`` triggers (DB-level ``*event`` tables).
2. **Access log** — this :class:`AccessLog` table, populated by Django auth
   signals (login / logout / failed), unifying access evidence with the domain
   audit trail.

The DB-level hardening (REVOKE + trigger) is applied by:

* the ``0002`` migration → ``audit_accesslog`` live table (append-only), and
* the ``harden_events`` management command → all ``*event`` tables.
"""
from __future__ import annotations

import pghistory
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AccessEvent(models.TextChoices):
    """Types of access event recorded in the log."""

    LOGIN = "LOGIN", _("Inicio de sesión")
    LOGOUT = "LOGOUT", _("Cierre de sesión")
    LOGIN_FAILED = "LOGIN_FAILED", _("Intento fallido de inicio de sesión")


@pghistory.track(pghistory.InsertEvent())
class AccessLog(models.Model):
    """Append-only log of access events (login/logout/failure).

    Append-only by design: rows are only created, never modified or deleted.
    DB-level hardening is applied by the ``0002`` migration.

    :ivar evento: event type (see :class:`AccessEvent`).
    :ivar usuario: associated user (``NULL`` on failures without a valid user).
    :ivar email_intento: email used in the attempt (key on failures where the
        user does not exist; attributable without false attribution).
    :ivar ip: source IP address.
    :ivar user_agent: client user-agent.
    :ivar ts: server timestamp in UTC.
    """

    evento = models.CharField(
        _("evento"), max_length=16, choices=AccessEvent.choices
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_logs",
        verbose_name=_("usuario"),
    )
    email_intento = models.EmailField(
        _("email del intento"), blank=True, default=""
    )
    ip = models.GenericIPAddressField(_("IP"), null=True, blank=True)
    user_agent = models.TextField(_("user agent"), blank=True, default="")
    ts = models.DateTimeField(_("timestamp"), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("evento de acceso")
        verbose_name_plural = _("eventos de acceso")
        ordering = ["-ts"]
        indexes = [
            models.Index(fields=["evento", "ts"]),
            models.Index(fields=["usuario", "ts"]),
        ]

    def __str__(self) -> str:
        """:returns: readable representation of the event. :rtype: str"""
        quien = self.usuario.email if self.usuario else self.email_intento
        return f"{self.ts:%Y-%m-%d %H:%M:%S} {self.evento} {quien}"
