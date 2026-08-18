"""Idempotent seed for the Ledger.

Creates ONLY:

* the Admin role (Django Group) and the admin superuser (from ``ADMIN_EMAIL`` /
  ``ADMIN_PASSWORD``), added to the Admin group,
* two example certificates (one BORRADOR, one FIRMADO) created and signed by the
  admin, so there is data to see.

The remaining roles (Elaborador / Firmante / Auditor) and the user/role
management are **not** seeded on purpose: building that management — so an Admin
can create those users and roles — is a candidate task (see README).

Idempotent (``get_or_create`` by natural key): re-running does not duplicate.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts import roles as role_defs
from apps.ledger.models import Certificate, EstadoCertificado, Veredicto
from apps.ledger.signatures import BasicSignatureProvider

User = get_user_model()


class Command(BaseCommand):
    """Seed the Admin role, the admin user and example certificates."""

    help = "Seed the Admin role, admin user and example certificates (idempotent)."

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the idempotent seed.\n
        :param args: positional command args (unused).\n
        :param options: command options (unused).\n
        """
        admin = self._seed_admin()
        self._seed_certificates(admin=admin)
        self.stdout.write(self.style.SUCCESS("Seed inicial completado."))

    def _seed_admin(self) -> "User":
        """Create the Admin group and the admin superuser (member of it).

        The other roles are intentionally not created here — that is the
        candidate's task.\n
        :returns: the admin user.\n
        """
        admin_group, _ = Group.objects.get_or_create(name=role_defs.ROLE_ADMIN)
        email = settings.ADMIN_EMAIL
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            user = User.objects.create_superuser(
                email=email,
                password=settings.ADMIN_PASSWORD,
                nombre="Administrador",
            )
            self.stdout.write(self.style.SUCCESS(f"  Admin {email}: creado."))
        else:
            self.stdout.write(f"  Admin {email}: ya existe.")
        user.groups.add(admin_group)
        return user

    def _seed_certificates(self, admin: "User") -> None:
        """Create one draft and one signed example certificate (by the admin).\n
        :param admin: admin user (creator and signer of the examples).\n
        """
        Certificate.objects.get_or_create(
            codigo="CERT-0001",
            defaults=dict(
                asunto="Certificado de conformidad de ejemplo (borrador)",
                emitido_a="Cliente Demo S.A.",
                veredicto=Veredicto.CONFORME,
                observaciones="Ejemplo en estado BORRADOR (editable).",
                estado=EstadoCertificado.BORRADOR,
                creado_por=admin,
            ),
        )

        signed = Certificate.objects.filter(codigo="CERT-0002").first()
        if signed is None:
            provider = BasicSignatureProvider()
            payload = {
                "codigo": "CERT-0002",
                "asunto": "Certificado de conformidad de ejemplo (firmado)",
                "emitido_a": "Cliente Demo S.A.",
                "veredicto": Veredicto.CONFORME,
                "observaciones": "Ejemplo ya FIRMADO (inmutable).",
            }
            firma = provider.sign(
                payload=payload, meaning="Certificado de conformidad: CONFORME"
            )
            # Insert directly as signed: the immutability trigger fires on
            # UPDATE/DELETE, not INSERT, so a born-signed row is allowed.
            Certificate.objects.create(
                codigo=payload["codigo"],
                asunto=payload["asunto"],
                emitido_a=payload["emitido_a"],
                veredicto=payload["veredicto"],
                observaciones=payload["observaciones"],
                estado=EstadoCertificado.FIRMADO,
                firmada=True,
                firmante=admin,
                firma_ts=timezone.now(),
                firma_hash=firma.hash,
                creado_por=admin,
            )
        self.stdout.write(
            f"  Certificados: {Certificate.objects.count()} en BD."
        )
