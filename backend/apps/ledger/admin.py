"""Register the Certificate in the Django admin (read-oriented)."""
from __future__ import annotations

from django.contrib import admin

from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin for certificates.

    Signed certificates are immutable at the DB level; the admin is mostly for
    inspection. Deletion is disabled (records are never physically removed).
    """

    list_display = ["codigo", "asunto", "estado", "veredicto", "firmada", "created_at"]
    list_filter = ["estado", "veredicto", "firmada"]
    search_fields = ["codigo", "asunto", "emitido_a"]
    readonly_fields = ["firma_hash", "firma_ts", "firmante", "created_at", "updated_at"]

    def has_delete_permission(self, request: object, obj: object = None) -> bool:
        """Disable deletion (records are never physically removed)."""
        return False
