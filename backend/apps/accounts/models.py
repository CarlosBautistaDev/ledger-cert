"""Models for the ``accounts`` app.

Implements the identity of the Ledger's people:

* :class:`User` — custom user (``AbstractUser``) with **email as the login**.
  Roles are modeled with Django ``Group`` (the fixed roles, see
  :mod:`apps.accounts.roles`), so this model does not add its own role field.
"""
from __future__ import annotations

from typing import List, Optional

import pghistory
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from . import roles as role_defs


class UserManager(BaseUserManager):
    """Custom user manager with email login (no ``username``)."""

    use_in_migrations = True

    def normalize_email(self, email: Optional[str]) -> str:
        """Normalize the email to full lowercase (local part + domain).

        Django only lowercases the domain by default; here we also lowercase
        the local part so the case-insensitive uniqueness of the email is
        consistent between INSERT and lookup.\n
        :param email: email to normalize (may be ``None``/empty).\n
        :returns: the lowercased email, or empty string if there is no value.\n
        """
        email = super().normalize_email(email)
        return email.lower() if email else email

    def _create_user(
        self, email: str, password: Optional[str], **extra_fields: object
    ) -> "User":
        """Create and persist a user with a normalized email.\n
        :param email: email address (unique login).\n
        :param password: plain password (hashed by Django); may be ``None``.\n
        :param extra_fields: additional model fields.\n
        :returns: the created user instance.\n
        :raises ValueError: if no email is provided.\n
        """
        if not email:
            raise ValueError(_("El correo electrónico es obligatorio."))
        email = self.normalize_email(email)
        user: "User" = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields: object
    ) -> "User":
        """Create a standard user (not staff, not superuser).\n
        :param email: email address (unique login).\n
        :param password: plain password.\n
        :param extra_fields: additional model fields.\n
        :returns: the created user.\n
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self, email: str, password: Optional[str] = None, **extra_fields: object
    ) -> "User":
        """Create a superuser (full Django admin access).\n
        :param email: email address (unique login).\n
        :param password: plain password.\n
        :param extra_fields: additional model fields.\n
        :returns: the created superuser.\n
        :raises ValueError: if ``is_staff``/``is_superuser`` are not ``True``.\n
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("El superusuario debe tener is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("El superusuario debe tener is_superuser=True."))
        return self._create_user(email, password, **extra_fields)


@pghistory.track(
    pghistory.InsertEvent(),
    pghistory.UpdateEvent(),
    pghistory.DeleteEvent(),
)
class User(AbstractUser):
    """Ledger user with email login.

    ``username`` is dropped as a credential; the login is the ``email``. Roles
    are modeled with Django ``Group`` (native RBAC).\n
    :ivar email: unique email, used as ``USERNAME_FIELD``.\n
    :ivar nombre: full name of the person.\n
    :ivar activo: business alias of ``is_active`` (account soft-disable).\n
    """

    username = None  # type: ignore[assignment]

    email = models.EmailField(_("correo electrónico"), unique=True)
    nombre = models.CharField(_("nombre completo"), max_length=160)
    activo = models.BooleanField(_("activo"), default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: List[str] = ["nombre"]

    objects = UserManager()

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")
        ordering = ["email"]

    def __str__(self) -> str:
        """Readable representation: ``nombre <email>``.\n
        :returns: string with name and email.\n
        """
        return f"{self.nombre} <{self.email}>"

    def save(self, *args: object, **kwargs: object) -> None:
        """Keep ``is_active`` in sync with the business field ``activo``."""
        self.is_active = self.activo
        super().save(*args, **kwargs)

    @property
    def roles(self) -> List[str]:
        """List of role keys (Group names) the user belongs to.\n
        :returns: names of the groups the user belongs to.\n
        """
        return list(self.groups.values_list("name", flat=True))

    @property
    def es_admin(self) -> bool:
        """Whether the user is an organization admin (Django superuser).\n
        :returns: ``True`` if the user is a superuser.\n
        """
        return bool(self.is_superuser)
