"""DRF permissions based on the fixed roles of the Ledger (RBAC).

Authorization is decided by **Django ``Group`` membership** (role). These
classes encapsulate the capability matrix.

Cross-cutting rule: the **Auditor role is read-only** (only ``SAFE_METHODS``:
GET/HEAD/OPTIONS) across the whole system; a Django superuser always passes
(operational break-glass).
"""
from __future__ import annotations

from typing import Iterable

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from . import roles


def _user_in_any(user: object, role_keys: Iterable[str]) -> bool:
    """Whether the user belongs to any of the given roles.\n
    :param user: request user (``request.user``).\n
    :param role_keys: role keys to check.\n
    :returns: ``True`` if the user is in at least one of the groups (or superuser).\n
    """
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    user_roles = set(user.groups.values_list("name", flat=True))
    return bool(user_roles & set(role_keys))


class IsAdmin(permissions.BasePermission):
    """Allow access only to the Admin role (or a Django superuser).

    Used by user management (``/api/users/``).
    """

    message = "Se requiere el rol Administrador."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check Admin-role (or superuser) membership.\n
        :param request: incoming request.\n
        :param view: target view.\n
        :returns: ``True`` if the user is an Admin or superuser.\n
        """
        return _user_in_any(request.user, roles.USER_ADMIN_ROLES)


class ReadAllWriteByRole(permissions.BasePermission):
    """Read for any authenticated user; write only for the given roles.

    All authenticated users can **read** (including Auditor), but only the
    write roles can create/edit.\n
    :cvar write_roles: role keys with write permission.\n
    """

    write_roles: frozenset = roles.WRITE_ROLES
    message = "Se requiere el rol Elaborador o Administrador para escribir."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Open read to authenticated users; restrict write by role.\n
        :param request: incoming request.\n
        :param view: target view.\n
        :returns: ``True`` if the operation is allowed for the user.\n
        """
        if not getattr(request.user, "is_authenticated", False):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return _user_in_any(request.user, self.write_roles)
