"""Models for the ``ledger`` app: the Certificate of Conformity.

The :class:`Certificate` is the core domain record. It follows a compliance
lifecycle: **DRAFT -> SIGNED -> SUPERSEDED**. Once signed it becomes immutable
(enforced by a PostgreSQL trigger, see migration ``0002``); a correction is
done by **supersession** (a new certificate that supersedes the original),
never by editing.

Audit trail: ``@pghistory.track()`` (DB-level ``*event`` table populated by
triggers) + ``HistoricalRecords()`` (ORM version history).
"""
from __future__ import annotations

import pghistory
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class EstadoCertificado(models.TextChoices):
    """Lifecycle state of a certificate."""

    BORRADOR = "BORRADOR", _("Borrador")
    FIRMADO = "FIRMADO", _("Firmado")
    REEMPLAZADO = "REEMPLAZADO", _("Reemplazado")


class Veredicto(models.TextChoices):
    """Conformity verdict of a certificate."""

    CONFORME = "CONFORME", _("Conforme")
    NO_CONFORME = "NO_CONFORME", _("No conforme")


@pghistory.track()
class Certificate(models.Model):
    """Certificate of conformity — signed, immutable record.\n
    :ivar codigo: unique human-readable code (e.g. ``CERT-0001``).\n
    :ivar asunto: what the certificate certifies (subject).\n
    :ivar emitido_a: recipient / party the certificate is issued to.\n
    :ivar veredicto: conformity verdict (CONFORME / NO_CONFORME).\n
    :ivar observaciones: free-text notes.\n
    :ivar estado: lifecycle state (BORRADOR / FIRMADO / REEMPLAZADO).\n
    :ivar firmada: whether the certificate has been signed (turns it immutable).\n
    :ivar firmante: user who signed it.\n
    :ivar firma_ts: signature timestamp (UTC).\n
    :ivar firma_hash: SHA-256 hash of the canonical content bound by the signature.\n
    :ivar creado_por: user who created it.\n
    :ivar actualizado_por: user who last updated it (while draft).\n
    """

    codigo = models.CharField(_("código"), max_length=40, unique=True)
    asunto = models.CharField(_("asunto"), max_length=200)
    emitido_a = models.CharField(_("emitido a"), max_length=200, blank=True, default="")
    veredicto = models.CharField(
        _("veredicto"),
        max_length=16,
        choices=Veredicto.choices,
        default=Veredicto.CONFORME,
    )
    observaciones = models.TextField(_("observaciones"), blank=True, default="")

    estado = models.CharField(
        _("estado"),
        max_length=16,
        choices=EstadoCertificado.choices,
        default=EstadoCertificado.BORRADOR,
    )

    firmada = models.BooleanField(_("firmada"), default=False)
    firmante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="certificados_firmados",
        verbose_name=_("firmante"),
    )
    firma_ts = models.DateTimeField(_("fecha de firma"), null=True, blank=True)
    firma_hash = models.CharField(_("hash de firma"), max_length=64, blank=True, default="")

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name="certificados_creados",
        verbose_name=_("creado por"),
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="certificados_actualizados",
        verbose_name=_("actualizado por"),
    )
    created_at = models.DateTimeField(_("creado"), auto_now_add=True)
    updated_at = models.DateTimeField(_("actualizado"), auto_now=True)

    history = HistoricalRecords(inherit=False)

    class Meta:
        verbose_name = _("certificado")
        verbose_name_plural = _("certificados")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Readable representation: ``codigo — estado``."""
        return f"{self.codigo} — {self.estado}"

    def canonical_payload(self) -> dict:
        """Build the canonical content bound by the signature.\n
        :returns: mapping of the fields that the signature seals.\n
        """
        return {
            "codigo": self.codigo,
            "asunto": self.asunto,
            "emitido_a": self.emitido_a,
            "veredicto": self.veredicto,
            "observaciones": self.observaciones,
        }
