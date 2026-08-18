"""Integration of ``django-axes`` with the DRF JWT login.

``django-axes`` is designed for Django form logins (reads ``request.POST``).
The Ledger login uses DRF + SimpleJWT with a JSON body, so ``request.POST`` is
empty and axes cannot extract the ``username``. This module bridges that gap:

* :func:`get_username` — ``AXES_USERNAME_CALLABLE``: extracts the email from the
  body / credentials so the lockout applies per (user, IP).
* :func:`raise_permission_denied` — ``user_locked_out`` receiver that raises a
  DRF ``PermissionDenied`` (403) so the view returns a generic "account locked"
  response without revealing whether the user exists.

The receiver is registered in :meth:`apps.accounts.apps.AccountsConfig.ready`.
"""
from __future__ import annotations

from typing import Any, Optional

from axes.signals import user_locked_out
from django.dispatch import receiver
from django.http import HttpRequest
from rest_framework.exceptions import PermissionDenied


def get_username(
    request: Optional[HttpRequest], credentials: Optional[dict] = None
) -> str:
    """Extract the email-username of the login attempt for axes.\n
    :param request: request of the attempt (may be ``None``).\n
    :param credentials: credentials passed to ``authenticate`` (if any).\n
    :returns: the attempt email, or empty string if undeterminable.\n
    """
    if credentials:
        value = credentials.get("email") or credentials.get("username")
        if value:
            return str(value)
    if request is not None:
        data = getattr(request, "data", None)
        if isinstance(data, dict):
            value = data.get("email") or data.get("username")
            if value:
                return str(value)
        value = request.POST.get("email") or request.POST.get("username")
        if value:
            return str(value)
    return ""


@receiver(user_locked_out)
def raise_permission_denied(*args: Any, **kwargs: Any) -> None:
    """Translate the axes lockout into a DRF ``PermissionDenied``.\n
    :raises rest_framework.exceptions.PermissionDenied: always (account locked).\n
    """
    raise PermissionDenied("account_locked")
