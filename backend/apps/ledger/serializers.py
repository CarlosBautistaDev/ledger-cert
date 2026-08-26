"""Serializers for the ``ledger`` app (Certificate)."""
from __future__ import annotations

from typing import Any, Dict

from rest_framework import serializers

from .models import Certificate, Veredicto


class CertificateSerializer(serializers.ModelSerializer):
    """Read serializer for a certificate (FKs exposed as ``*_id``)."""

    firmante_id = serializers.PrimaryKeyRelatedField(source="firmante", read_only=True)
    creado_por_id = serializers.PrimaryKeyRelatedField(source="creado_por", read_only=True)
    reemplaza_id = serializers.PrimaryKeyRelatedField(source="reemplaza", read_only=True)
    reemplazado_por_id = serializers.PrimaryKeyRelatedField(
        source="reemplazado_por", read_only=True
    )
    esta_vigente = serializers.BooleanField(read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id",
            "codigo",
            "asunto",
            "emitido_a",
            "veredicto",
            "observaciones",
            "estado",
            "firmada",
            "firmante_id",
            "firma_ts",
            "firma_hash",
            "reemplaza_id",
            "reemplazado_por_id",
            "esta_vigente",
            "creado_por_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CertificateWriteSerializer(serializers.ModelSerializer):
    """Write serializer for creating/editing a draft certificate.

    Only draft-editable business fields are writable; lifecycle and signature
    fields are managed by the viewset actions.
    """

    class Meta:
        model = Certificate
        fields = ["id", "codigo", "asunto", "emitido_a", "veredicto", "observaciones"]

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        """Return the read representation of the certificate.\n
        :param instance: serialized certificate.\n
        :returns: read payload.\n
        """
        return CertificateSerializer(instance, context=self.context).data


class CertificateSupersedeSerializer(serializers.Serializer):
    """Datos del certificado nuevo que corrige a uno ya firmado."""

    codigo = serializers.CharField(max_length=40)
    asunto = serializers.CharField(max_length=200)
    emitido_a = serializers.CharField(max_length=200, allow_blank=True, required=False)
    veredicto = serializers.ChoiceField(choices=Veredicto.choices)
    observaciones = serializers.CharField(allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_codigo(self, value: str) -> str:
        """Evita que la correccion reutilice un codigo que ya existe."""
        if Certificate.objects.filter(codigo=value).exists():
            raise serializers.ValidationError("Ya existe un certificado con ese código.")
        return value
