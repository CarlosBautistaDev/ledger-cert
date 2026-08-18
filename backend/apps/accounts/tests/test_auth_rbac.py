"""Tests for authentication and RBAC in the ``accounts`` app."""
from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


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
