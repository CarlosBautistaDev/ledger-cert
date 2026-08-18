"""Register the custom user in the Django admin."""
from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for the custom user (email login, no ``username``)."""

    ordering = ["email"]
    list_display = ["email", "nombre", "activo", "is_staff"]
    list_filter = ["activo", "is_staff", "is_superuser", "groups"]
    search_fields = ["email", "nombre"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Información personal"), {"fields": ("nombre",)}),
        (
            _("Permisos"),
            {
                "fields": (
                    "activo",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Fechas"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "nombre",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
