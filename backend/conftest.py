"""Base pytest fixtures for the Ledger de Certificados backend.

Provides a DRF API client, per-role users (Admin / Elaborador / Firmante /
Auditor) and a factory, so the test suite can exercise authentication, RBAC
and the certificate lifecycle.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from apps.accounts import roles as role_defs

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    """Unauthenticated DRF API client.\n
    :returns: a fresh APIClient instance.\n
    """
    return APIClient()


@pytest.fixture
def roles_seeded(db) -> None:
    """Ensure the fixed roles exist as Django Groups (idempotent).\n
    :param db: pytest-django database fixture.\n
    """
    for spec in role_defs.ROLES:
        Group.objects.get_or_create(name=spec["clave"])


@pytest.fixture
def user_factory(db, roles_seeded) -> Callable[..., "User"]:
    """Factory of users with role assignment.\n
    :param db: pytest-django database fixture.\n
    :param roles_seeded: ensures the role Groups exist.\n
    :returns: a callable ``(email, password, roles, **extra) -> User``.\n
    """

    def _make(
        email: str = "user@ledger.local",
        password: str = "Ledger-Test-12345!",
        roles: Optional[List[str]] = None,
        **extra: object,
    ) -> "User":
        """Create a user and assign the given roles.\n
        :param email: login email (unique).\n
        :param password: plain password (hashed with Argon2id).\n
        :param roles: role keys (Group names) to assign.\n
        :param extra: extra User model fields.\n
        :returns: the created user with its roles.\n
        """
        extra.setdefault("nombre", "Test User")
        user = User.objects.create_user(email=email, password=password, **extra)
        if roles:
            user.groups.set(Group.objects.filter(name__in=roles))
        return user

    return _make


@pytest.fixture
def admin_user(db, roles_seeded) -> "User":
    """Superuser in the Admin group (can create and sign).\n
    :param db: pytest-django database fixture.\n
    :param roles_seeded: ensures the role Groups exist.\n
    :returns: an admin superuser.\n
    """
    user = User.objects.create_superuser(
        email="admin@ledger.local",
        password="Ledger-Test-12345!",
        nombre="Admin Test",
    )
    user.groups.set(Group.objects.filter(name=role_defs.ROLE_ADMIN))
    return user


@pytest.fixture
def elaborador_user(user_factory) -> "User":
    """User with the Elaborador role (drafts, cannot sign).\n
    :returns: an Elaborador user.\n
    """
    return user_factory(
        email="elaborador@ledger.local", roles=[role_defs.ROLE_ELABORADOR]
    )


@pytest.fixture
def firmante_user(user_factory) -> "User":
    """User with the Firmante role (signs, does not draft).\n
    :returns: a Firmante user.\n
    """
    return user_factory(
        email="firmante@ledger.local", roles=[role_defs.ROLE_FIRMANTE]
    )


@pytest.fixture
def auditor_user(user_factory) -> "User":
    """User with the Auditor role (read-only).\n
    :returns: an Auditor user.\n
    """
    return user_factory(
        email="auditor@ledger.local", roles=[role_defs.ROLE_AUDITOR]
    )


@pytest.fixture
def auth_client(api_client) -> Callable[["User"], APIClient]:
    """Return a function that authenticates the api_client as a given user.\n
    :param api_client: unauthenticated DRF client.\n
    :returns: a callable ``(user) -> APIClient`` (authenticated).\n
    """

    def _login(user: "User") -> APIClient:
        """Authenticate the client as ``user``.\n
        :param user: user to authenticate.\n
        :returns: the authenticated client.\n
        """
        api_client.force_authenticate(user=user)
        return api_client

    return _login
