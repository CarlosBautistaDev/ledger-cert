"""DRF views for the ``accounts`` app: authentication, users and roles.

Endpoints:

* ``POST /api/auth/login``   — obtain token pair (``TokenObtainPair``).
* ``POST /api/auth/refresh`` — rotate the refresh token.
* ``POST /api/auth/logout``  — blacklist the refresh (real revocation).
* ``GET  /api/auth/me``      — profile of the authenticated user.
* ``/api/users/``            — user CRUD (Admin only).
* ``GET  /api/roles/``       — catalog of the fixed roles.
"""
from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .permissions import IsAdmin
from .serializers import (
    LedgerTokenObtainPairSerializer,
    RoleSerializer,
    UserSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    """JWT login for the Ledger.

    Reuses SimpleJWT's view with the custom serializer that adds the user's
    roles to the token and response body, and emits ``user_logged_in`` so the
    access log records the sign-in (JWT issuance does not fire that signal on
    its own).
    """

    serializer_class = LedgerTokenObtainPairSerializer

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Authenticate, issue the token and record the successful login.

        Integrates the ``django-axes`` lockout: when (user, IP) exceeds the
        failure threshold, the ``AxesStandaloneBackend`` raises
        ``PermissionDenied`` before validating the password. Here it is
        translated into a 403 with a generic message that does not reveal
        whether the user exists.\n
        :param request: request with ``{"email", "password"}`` in the body.\n
        :returns: response with ``access``, ``refresh`` and ``user`` (200), the
            authentication error (401), or account locked (403).\n
        """
        try:
            response = super().post(request, *args, **kwargs)
        except (DjangoPermissionDenied, DRFPermissionDenied):
            self._log_lockout(request=request)
            return Response(
                {
                    "detail": _(
                        "Cuenta bloqueada temporalmente por demasiados "
                        "intentos fallidos. Intente de nuevo más tarde."
                    ),
                    "code": "account_locked",
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        if response.status_code == status.HTTP_200_OK:
            email = request.data.get("email")
            if email:
                user = User.objects.filter(email__iexact=email).first()
                if user is not None:
                    user_logged_in.send(
                        sender=user.__class__, request=request, user=user
                    )
        return response

    @staticmethod
    def _log_lockout(request: Request) -> None:
        """Record a lockout as an auditable failed-access event.\n
        :param request: request of the blocked attempt.\n
        """
        from apps.audit.models import AccessEvent, AccessLog

        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = (
            forwarded.split(",")[0].strip()
            if forwarded
            else request.META.get("REMOTE_ADDR")
        )
        AccessLog.objects.create(
            evento=AccessEvent.LOGIN_FAILED,
            usuario=None,
            email_intento=request.data.get("email", "") or "",
            ip=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )


class LogoutView(APIView):
    """Log out by blacklisting the refresh token (real revocation)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "properties": {"refresh": {"type": "string"}},
                "required": ["refresh"],
            }
        },
        responses={205: OpenApiResponse(description="Sesión cerrada.")},
    )
    def post(self, request: Request) -> Response:
        """Blacklist the received refresh token.\n
        :param request: request with ``{"refresh": "<token>"}`` in the body.\n
        :returns: 205 if revoked, 400 if the token is invalid.\n
        """
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detail": "Falta el campo 'refresh'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response(
                {"detail": "Token de refresco inválido o ya revocado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_logged_out.send(
            sender=request.user.__class__, request=request, user=request.user
        )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """Return the profile of the authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request: Request) -> Response:
        """Return the authenticated user serialized."""
        return Response(UserSerializer(request.user).data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only user listing — restricted to the Admin.

    NOTE (candidate task): user and role management — creating users, assigning
    roles and soft-delete — is intentionally NOT implemented here. Building it,
    reusing the project's conventions (``roles.py`` as the source of truth,
    ``IsAdmin``, the audit trail via ``PGHistoryContextMixin`` and a read/write
    serializer pair), is part of the assessment. See the README.
    """

    queryset = User.objects.all().order_by("email")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    search_fields = ["email", "nombre"]
    ordering_fields = ["email", "nombre", "date_joined"]


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only catalog of the fixed roles (Django Groups)."""

    queryset = Group.objects.all().order_by("name")
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
