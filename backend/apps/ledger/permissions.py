"""DRF permissions for the Ledger certificates (RBAC).

Reuses the base pattern of :mod:`apps.accounts.permissions`:

* **Auditor** is read-only across the system (``SAFE_METHODS``).
* **Elaborador / Admin** create and edit draft certificates.
* Only **Firmante / Admin** may **sign** — the ``sign`` action is gated by
  ``SIGN_ROLES``, not by draft-write authority.

Segregation of duties: the Elaborador drafts but cannot sign; the Firmante
signs but does not draft. Because signing is an HTTP POST, the permission must
route the ``sign`` action to ``SIGN_ROLES`` instead of the generic write gate.
"""
from __future__ import annotations

from apps.accounts import roles
from apps.accounts.permissions import ReadAllWriteByRole, _user_in_any
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class CertificatePermission(ReadAllWriteByRole):
    """Permission for certificates.

    Read for any authenticated user (including Auditor); create/edit for
    Elaborador/Admin; the ``sign`` action for Firmante/Admin.
    """

    write_roles: frozenset = roles.WRITE_ROLES
    message = (
        "Se requiere el rol Elaborador o Administrador para crear o editar "
        "certificados; el Auditor es de solo lectura."
    )

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Route authorization by action (segregation of duties).

        Read is open to any authenticated user; the ``sign`` action requires
        signing authority (``SIGN_ROLES``); other writes require the draft
        write roles (``WRITE_ROLES``).\n
        :param request: incoming request.\n
        :param view: target view.\n
        :returns: ``True`` if the operation is allowed for the user.\n
        """
        if not getattr(request.user, "is_authenticated", False):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        if getattr(view, "action", None) in {"sign", "supersede"}:
            return _user_in_any(request.user, roles.SIGN_ROLES)
        return _user_in_any(request.user, self.write_roles)

    def can_sign(self, request: Request, view: APIView) -> bool:
        """Whether the user has signing authority (Firmante or Admin).\n
        :param request: incoming request.\n
        :param view: target view.\n
        :returns: ``True`` if the user may sign.\n
        """
        return _user_in_any(request.user, roles.SIGN_ROLES)
