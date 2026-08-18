"""Access-audit signals.

Connects Django's authentication signals with the append-only access log
(``apps.audit.AccessLog``) so login/logout/failures land in the same audit
trail as domain changes.

The receivers are registered in :meth:`apps.accounts.apps.AccountsConfig.ready`.
"""
from __future__ import annotations

from typing import Any, Optional

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.http import HttpRequest


def _client_ip(request: Optional[HttpRequest]) -> Optional[str]:
    """Extract the client IP, honoring the Caddy proxy header.\n
    :param request: HTTP request (may be ``None`` in some signals).\n
    :returns: the client IP or ``None`` if it cannot be determined.\n
    """
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _user_agent(request: Optional[HttpRequest]) -> str:
    """Extract the request user-agent.\n
    :param request: HTTP request.\n
    :returns: user-agent string (empty if unavailable).\n
    """
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


@receiver(user_logged_in)
def on_user_logged_in(
    sender: Any, request: HttpRequest, user: Any, **kwargs: Any
) -> None:
    """Record a successful login event.\n
    :param sender: signal sender class.\n
    :param request: HTTP request of the login.\n
    :param user: authenticated user.\n
    """
    from apps.audit.models import AccessEvent, AccessLog

    AccessLog.objects.create(
        evento=AccessEvent.LOGIN,
        usuario=user,
        email_intento=getattr(user, "email", "") or "",
        ip=_client_ip(request),
        user_agent=_user_agent(request),
    )


@receiver(user_logged_out)
def on_user_logged_out(
    sender: Any, request: HttpRequest, user: Any, **kwargs: Any
) -> None:
    """Record a logout event.\n
    :param sender: signal sender class.\n
    :param request: HTTP request of the logout.\n
    :param user: user who logged out (may be ``None``).\n
    """
    from apps.audit.models import AccessEvent, AccessLog

    AccessLog.objects.create(
        evento=AccessEvent.LOGOUT,
        usuario=user,
        email_intento=getattr(user, "email", "") or "",
        ip=_client_ip(request),
        user_agent=_user_agent(request),
    )


@receiver(user_login_failed)
def on_user_login_failed(
    sender: Any,
    credentials: dict,
    request: Optional[HttpRequest] = None,
    **kwargs: Any,
) -> None:
    """Record a failed login attempt (no false attribution).\n
    :param sender: signal sender class.\n
    :param credentials: credentials used (password already masked by Django).\n
    :param request: HTTP request of the attempt.\n
    """
    from apps.audit.models import AccessEvent, AccessLog

    email = credentials.get("email") or credentials.get("username") or ""
    AccessLog.objects.create(
        evento=AccessEvent.LOGIN_FAILED,
        usuario=None,
        email_intento=email,
        ip=_client_ip(request),
        user_agent=_user_agent(request),
    )
