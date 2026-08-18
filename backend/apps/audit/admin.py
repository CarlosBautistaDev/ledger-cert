"""Register the access log in the Django admin (read-only)."""
from __future__ import annotations

from django.contrib import admin

from .models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    """Admin for the append-only access log (read-only)."""

    list_display = ["ts", "evento", "usuario", "email_intento", "ip"]
    list_filter = ["evento", "ts"]
    search_fields = ["email_intento", "usuario__email", "ip"]
    readonly_fields = [f.name for f in AccessLog._meta.fields]
    date_hierarchy = "ts"

    def has_add_permission(self, request: object) -> bool:
        """Block manual creation. :rtype: bool"""
        return False

    def has_change_permission(self, request: object, obj: object = None) -> bool:
        """Block editing (append-only). :rtype: bool"""
        return False

    def has_delete_permission(self, request: object, obj: object = None) -> bool:
        """Block deletion (append-only). :rtype: bool"""
        return False
