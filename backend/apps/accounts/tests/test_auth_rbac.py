"""Tests for authentication and RBAC in the ``accounts`` app."""
from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_login_returns_tokens_and_user(api_client, firmante_user) -> None:
    """A valid login returns access/refresh tokens and the user payload.\n
    :param api_client: unauthenticated DRF client.\n
    :param firmante_user: seeded Firmante user.\n
    """
    url = reverse("auth-login")
    resp = api_client.post(
        url,
        {"email": firmante_user.email, "password": "Ledger-Test-12345!"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "access" in resp.data
    assert "refresh" in resp.data
    assert resp.data["user"]["email"] == firmante_user.email
    assert "Firmante" in resp.data["user"]["roles"]


def test_me_returns_authenticated_user(auth_client, elaborador_user) -> None:
    """``/auth/me`` returns the authenticated user's profile.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param elaborador_user: seeded Elaborador user.\n
    """
    client = auth_client(elaborador_user)
    resp = client.get(reverse("auth-me"))
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["email"] == elaborador_user.email


def test_auditor_cannot_create_certificate(auth_client, auditor_user) -> None:
    """The Auditor role is read-only: creating a certificate is forbidden.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param auditor_user: seeded Auditor user.\n
    """
    client = auth_client(auditor_user)
    resp = client.post(
        "/api/ledger/certificates/",
        {"codigo": "CERT-AUD", "asunto": "x", "veredicto": "CONFORME"},
        format="json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_auditor_can_read_certificates(auth_client, auditor_user) -> None:
    """The Auditor role can read the certificate list.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param auditor_user: seeded Auditor user.\n
    """
    client = auth_client(auditor_user)
    resp = client.get("/api/ledger/certificates/")
    assert resp.status_code == status.HTTP_200_OK


def test_admin_creates_user_and_assigns_role(auth_client, admin_user) -> None:
    """El Admin puede dar de alta una cuenta con un rol operativo."""
    client = auth_client(admin_user)
    resp = client.post(
        "/api/users/",
        {
            "email": "nuevo@ledger.local",
            "nombre": "Usuario Nuevo",
            "password": "Clave-Nueva-12345!",
            "roles": ["Elaborador"],
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    user = User.objects.get(email="nuevo@ledger.local")
    assert user.check_password("Clave-Nueva-12345!")
    assert list(user.groups.values_list("name", flat=True)) == ["Elaborador"]


def test_admin_can_change_an_operational_role(
    auth_client, admin_user, elaborador_user
) -> None:
    """El Admin puede mover una cuenta a otro rol sin crearla de nuevo."""
    client = auth_client(admin_user)
    resp = client.patch(
        f"/api/users/{elaborador_user.id}/",
        {"roles": ["Firmante"]},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK, resp.data
    elaborador_user.refresh_from_db()
    assert list(elaborador_user.groups.values_list("name", flat=True)) == ["Firmante"]


def test_non_admin_cannot_manage_users(auth_client, elaborador_user) -> None:
    """Un rol operativo no puede crear cuentas ni cambiar permisos."""
    client = auth_client(elaborador_user)
    resp = client.post(
        "/api/users/",
        {
            "email": "prohibido@ledger.local",
            "nombre": "No permitido",
            "password": "Clave-Nueva-12345!",
            "roles": ["Auditor"],
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_user_creation_rejects_admin_and_mixed_roles(
    auth_client, admin_user
) -> None:
    """No deja entregar Admin ni juntar funciones que deben estar separadas."""
    client = auth_client(admin_user)
    base = {
        "email": "roles@ledger.local",
        "nombre": "Roles",
        "password": "Clave-Nueva-12345!",
    }
    resp = client.post(
        "/api/users/", {**base, "roles": ["Admin"]}, format="json"
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    resp = client.post(
        "/api/users/", {**base, "roles": ["Elaborador", "Firmante"]}, format="json"
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
