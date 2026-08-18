"""Startup (fail-fast) validations for production.

Aborts startup if any secret is still a known insecure/example value. Critical
because ``SECRET_KEY`` is the JWT ``SIGNING_KEY`` (HS256): if production boots
with the development default, that key is public and would allow forging JWTs
for any user (full auth/RBAC bypass).

The logic lives in a pure, testable function (not in the body of ``prod.py``)
so it can be covered by a unit test without importing the prod settings module.
"""
from __future__ import annotations

from typing import List

from django.core.exceptions import ImproperlyConfigured

#: Minimum acceptable length for ``SECRET_KEY`` (HS256 JWT signing).
MIN_SECRET_KEY_LENGTH: int = 32

#: Known insecure values that must never reach production.
INSECURE_SECRET_KEYS = {"", "dev-insecure-change-me"}
INSECURE_DB_PASSWORDS = {"", "changeme"}
INSECURE_ADMIN_PASSWORDS = {"", "Admin12345!", "changeme-admin"}


def require_secure_secrets(
    *, secret_key: str, db_password: str, admin_password: str
) -> None:
    """Abort startup if any secret is still an insecure/example value.

    :param secret_key: effective ``SECRET_KEY`` value (JWT signing).
    :type secret_key: str
    :param db_password: database password (``POSTGRES_PASSWORD``).
    :type db_password: str
    :param admin_password: seed admin password (``ADMIN_PASSWORD``).
    :type admin_password: str
    :returns: ``None`` if all secrets are secure.
    :rtype: None
    :raises django.core.exceptions.ImproperlyConfigured: if any is an
        example/insecure value or ``SECRET_KEY`` is too short.
    """
    problems: List[str] = []

    sk = (secret_key or "").strip()
    if sk in INSECURE_SECRET_KEYS:
        problems.append("DJANGO_SECRET_KEY (example value)")
    elif len(sk) < MIN_SECRET_KEY_LENGTH:
        problems.append(
            f"DJANGO_SECRET_KEY (too short, min {MIN_SECRET_KEY_LENGTH} chars)"
        )

    if (db_password or "").strip() in INSECURE_DB_PASSWORDS:
        problems.append("POSTGRES_PASSWORD (example value)")

    if (admin_password or "").strip() in INSECURE_ADMIN_PASSWORDS:
        problems.append("ADMIN_PASSWORD (example value)")

    if problems:
        raise ImproperlyConfigured(
            "Production startup aborted: set secure (non-example) values in "
            "the environment for -> " + "; ".join(problems)
        )
