"""DRF views for the ``ledger`` app: the Certificate lifecycle.

* ``GET  /api/ledger/certificates/``            — list.
* ``POST /api/ledger/certificates/``            — create (state BORRADOR).
* ``GET  /api/ledger/certificates/{id}/``       — retrieve.
* ``POST /api/ledger/certificates/{id}/sign/``  — sign (re-auth + hash).
* ``POST /api/ledger/certificates/{id}/supersede/`` — correction (TODO: candidate).
"""
from __future__ import annotations

from typing import Any, Optional

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from apps.audit.pghistory_drf import PGHistoryContextMixin

from .models import Certificate, EstadoCertificado
from .permissions import CertificatePermission
from .serializers import (
    CertificateSerializer,
    CertificateSupersedeSerializer,
    CertificateWriteSerializer,
)
from .signatures import BasicSignatureProvider


class CertificateViewSet(PGHistoryContextMixin, viewsets.ModelViewSet):
    """Certificate CRUD + lifecycle actions (sign, supersede).

    Read for any authenticated user; create/edit for Elaborador/Admin; signing
    restricted to Firmante/Admin. Once signed, a certificate is immutable at
    the DB level (trigger); corrections go through supersession.
    """

    queryset = Certificate.objects.all().order_by("-created_at")
    permission_classes = [CertificatePermission]
    search_fields = ["codigo", "asunto", "emitido_a"]
    ordering_fields = ["codigo", "created_at", "estado"]

    def get_serializer_class(self) -> type:
        """Select the serializer based on the action.\n
        :returns: write serializer for create/update, read serializer otherwise.\n
        """
        if self.action in {"create", "update", "partial_update"}:
            return CertificateWriteSerializer
        if self.action == "supersede":
            return CertificateSupersedeSerializer
        return CertificateSerializer

    def perform_create(self, serializer: Any) -> None:
        """Create the certificate in BORRADOR state, attributed to the actor.\n
        :param serializer: validated write serializer.\n
        """
        serializer.save(
            creado_por=self.request.user,
            estado=EstadoCertificado.BORRADOR,
        )

    @action(detail=True, methods=["post"])
    def sign(self, request: Request, pk: Optional[str] = None) -> Response:
        """Sign a draft certificate (re-authentication + hash binding).

        Requires the ``Firmante`` role (or Admin). Re-authenticates the signer
        with their password, computes the signature hash, and flips the
        certificate to FIRMADO — which makes it immutable via the DB trigger.\n
        :param request: request with ``{"password": "..."}`` in the body.\n
        :param pk: id of the certificate to sign.\n
        :returns: the signed certificate (200), or an error (403/400/409).\n
        """
        permiso = CertificatePermission()
        if not permiso.can_sign(request=request, view=self):
            return Response(
                {"detail": _("Se requiere el rol Firmante para firmar.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        certificado = self.get_object()

        if certificado.firmada:
            return Response(
                {"detail": _("El certificado ya está firmado.")},
                status=status.HTTP_409_CONFLICT,
            )

        password = request.data.get("password")
        if not password:
            raise ValidationError(
                {"password": _("Requerido para firmar (re-autenticación).")}
            )
        if not request.user.check_password(password):
            return Response(
                {"detail": _("Contraseña incorrecta.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        provider = BasicSignatureProvider()
        firma = provider.sign(
            payload=certificado.canonical_payload(),
            meaning=f"Certificado de conformidad: {certificado.veredicto}",
        )

        certificado.firmada = True
        certificado.firmante = request.user
        certificado.firma_ts = timezone.now()
        certificado.firma_hash = firma.hash
        certificado.estado = EstadoCertificado.FIRMADO
        certificado.save()

        return Response(
            CertificateSerializer(certificado, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def supersede(self, request: Request, pk: Optional[str] = None) -> Response:
        """Correct a signed certificate by issuing a replacement (SUPERSEDE).

        Un certificado firmado no se edita. La correccion crea otro registro
        firmado y enlazado al original, asi el original queda intacto como
        historial y solo el nuevo se considera vigente.\n
        :param request: request with the corrected fields in the body.\n
        :param pk: id of the signed certificate to supersede.\n
        :returns: el certificado corregido (201), o un error (403/400/409).\n
        """
        permiso = CertificatePermission()
        if not permiso.can_sign(request=request, view=self):
            return Response(
                {"detail": _("Se requiere el rol Firmante para corregir.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.pop("password")
        if not request.user.check_password(password):
            return Response(
                {"detail": _("Contraseña incorrecta.")},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            certificado = Certificate.objects.select_for_update().get(pk=pk)
            if not certificado.firmada:
                return Response(
                    {"detail": _("Solo se puede corregir un certificado firmado.")},
                    status=status.HTTP_409_CONFLICT,
                )
            if Certificate.objects.filter(reemplaza=certificado).exists():
                return Response(
                    {"detail": _("El certificado ya tiene una corrección vigente.")},
                    status=status.HTTP_409_CONFLICT,
                )

            datos = serializer.validated_data
            nuevo = Certificate(
                **datos,
                reemplaza=certificado,
                creado_por=request.user,
                estado=EstadoCertificado.FIRMADO,
                firmada=True,
                firmante=request.user,
                firma_ts=timezone.now(),
            )
            provider = BasicSignatureProvider()
            firma = provider.sign(
                payload=nuevo.canonical_payload(),
                meaning=f"Corrección de certificado: {nuevo.veredicto}",
            )
            nuevo.firma_hash = firma.hash
            nuevo.save()

        return Response(
            CertificateSerializer(nuevo, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
