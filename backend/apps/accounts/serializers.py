"""Serializers for the ``accounts`` app: JWT, users and roles.

NOTE (candidate task): the write serializer for user/role management (creating
users, assigning roles) is intentionally absent. Building it — following the
``UserSerializer`` read shape and validating role keys against ``roles.py`` —
is part of the assessment. See the README.
"""
from __future__ import annotations

from typing import Any, Dict, List

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from . import roles as role_defs

User = get_user_model()


class LedgerTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login serializer that includes the user's roles in the token/response."""

    @classmethod
    def get_token(cls, user: Any) -> Any:
        """Build the token with identity and role claims.\n
        :param user: authenticated user.\n
        :returns: refresh token with extra claims.\n
        """
        token = super().get_token(user)
        token["email"] = user.email
        token["nombre"] = user.nombre
        token["roles"] = list(user.groups.values_list("name", flat=True))
        return token

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credentials and attach the serialized user.\n
        :param attrs: incoming credentials (email + password).\n
        :returns: payload with ``access``, ``refresh`` and ``user``.\n
        """
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class RoleSerializer(serializers.ModelSerializer):
    """Serialize a role (Django ``Group``) with bilingual labels."""

    clave = serializers.CharField(source="name", read_only=True)
    nombre_es = serializers.SerializerMethodField()
    nombre_en = serializers.SerializerMethodField()
    descripcion_es = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ["id", "clave", "nombre_es", "nombre_en", "descripcion_es"]

    def _spec(self, obj: Group) -> Dict[str, str]:
        """Retrieve the bilingual spec of the role.\n
        :param obj: group (role) to describe.\n
        :returns: role spec, or empty dict if unknown.\n
        """
        return role_defs.role_label_map().get(obj.name, {})

    def get_nombre_es(self, obj: Group) -> str:
        """Return the role's Spanish label."""
        return self._spec(obj).get("nombre_es", obj.name)

    def get_nombre_en(self, obj: Group) -> str:
        """Return the role's English label."""
        return self._spec(obj).get("nombre_en", obj.name)

    def get_descripcion_es(self, obj: Group) -> str:
        """Return the role's Spanish description."""
        return self._spec(obj).get("descripcion_es", "")


class UserSerializer(serializers.ModelSerializer):
    """Read serializer for a user (includes its roles)."""

    roles = serializers.SerializerMethodField()
    ultimo_login = serializers.DateTimeField(source="last_login", read_only=True)
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nombre",
            "activo",
            "roles",
            "is_superuser",
            "ultimo_login",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "is_superuser",
            "ultimo_login",
            "created_at",
        ]

    def get_roles(self, obj: Any) -> List[str]:
        """Return the user's role keys."""
        return list(obj.groups.values_list("name", flat=True))


class UserWriteSerializer(serializers.ModelSerializer):
    """Alta y mantenimiento basico de usuarios desde Administracion."""

    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=sorted(role_defs.ASSIGNABLE_ROLES)),
        min_length=1,
        max_length=1,
    )
    password = serializers.CharField(
        write_only=True,
        min_length=10,
        required=False,
        trim_whitespace=False,
    )

    class Meta:
        model = User
        fields = ["id", "email", "nombre", "activo", "roles", "password"]
        read_only_fields = ["id"]

    def validate_email(self, value: str) -> str:
        """Normaliza el correo igual que el modelo antes de revisar duplicados."""
        email = value.lower()
        existe = User.objects.filter(email__iexact=email)
        if self.instance is not None:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise serializers.ValidationError("Ya existe un usuario con ese correo.")
        return email

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Pide contraseña al dar de alta y evita mezclar funciones."""
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "La contraseña es obligatoria."})
        password = attrs.get("password")
        if password:
            candidate = User(
                email=attrs.get("email", getattr(self.instance, "email", "")),
                nombre=attrs.get("nombre", getattr(self.instance, "nombre", "")),
            )
            validate_password(password, user=candidate)
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> User:
        """Crea la cuenta y agrega su unico rol operativo."""
        roles = validated_data.pop("roles")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        group, _ = Group.objects.get_or_create(name=roles[0])
        user.groups.set([group])
        return user

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        """Actualiza los datos permitidos sin borrar el historial de la cuenta."""
        roles = validated_data.pop("roles", None)
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            group, _ = Group.objects.get_or_create(name=roles[0])
            instance.groups.set([group])
        return instance
