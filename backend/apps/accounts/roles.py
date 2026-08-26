"""Central definition of the fixed roles of the Ledger.

Roles are materialized as Django ``Group`` (native RBAC). This module is the
source of truth for their keys and bilingual labels, consumed by:

* the ``seed_initial`` management command (creates the groups),
* the DRF permission classes (``permissions.py``),
* the serializers that expose ``/api/roles/``.

Capability matrix (segregation of duties: whoever drafts does not sign):

============  ==========================================================
Role          Capability
============  ==========================================================
Admin         Full access: user management, plus create and sign.
Elaborador    Create/edit draft certificates; cannot sign.
Firmante      Sign certificates (acceptance authority); does not draft.
Auditor       Read-only (GET) across the whole system.
============  ==========================================================

A Django superuser also bypasses the role checks (operational break-glass).
"""
from __future__ import annotations

from typing import Dict, List, TypedDict

# Canonical role keys (== Group name in the DB).
ROLE_ADMIN: str = "Admin"
ROLE_ELABORADOR: str = "Elaborador"
ROLE_FIRMANTE: str = "Firmante"
ROLE_AUDITOR: str = "Auditor"


class RoleSpec(TypedDict):
    """Bilingual specification of a Ledger role.\n
    :ivar clave: canonical key (Group name).\n
    :ivar nombre_es: Spanish label.\n
    :ivar nombre_en: English label.\n
    :ivar descripcion_es: functional description in Spanish.\n
    """

    clave: str
    nombre_es: str
    nombre_en: str
    descripcion_es: str


#: Order and metadata of the fixed roles.
ROLES: List[RoleSpec] = [
    {
        "clave": ROLE_ADMIN,
        "nombre_es": "Administrador",
        "nombre_en": "Admin",
        "descripcion_es": (
            "Acceso total: administra usuarios y roles; puede crear y firmar "
            "certificados."
        ),
    },
    {
        "clave": ROLE_ELABORADOR,
        "nombre_es": "Elaborador",
        "nombre_en": "Drafter",
        "descripcion_es": (
            "Crea y edita certificados en borrador; no puede firmar."
        ),
    },
    {
        "clave": ROLE_FIRMANTE,
        "nombre_es": "Firmante",
        "nombre_en": "Signer",
        "descripcion_es": (
            "Firma certificados (autoridad de aceptación); no elabora "
            "borradores."
        ),
    },
    {
        "clave": ROLE_AUDITOR,
        "nombre_es": "Auditor",
        "nombre_en": "Auditor",
        "descripcion_es": "Acceso de solo lectura a todo el sistema.",
    },
]

#: Roles allowed to create/edit draft certificates.
WRITE_ROLES: frozenset = frozenset({ROLE_ADMIN, ROLE_ELABORADOR})

#: Roles with signing authority (acceptance authority) over a certificate.
SIGN_ROLES: frozenset = frozenset({ROLE_ADMIN, ROLE_FIRMANTE})

#: Roles allowed to manage users.
USER_ADMIN_ROLES: frozenset = frozenset({ROLE_ADMIN})

# Roles que un administrador puede asignar desde la gestion diaria. Admin se
# reserva para la cuenta principal y no se entrega desde la pantalla.
ASSIGNABLE_ROLES: frozenset = frozenset(
    {ROLE_ELABORADOR, ROLE_FIRMANTE, ROLE_AUDITOR}
)


def role_label_map() -> Dict[str, RoleSpec]:
    """Return a ``key -> RoleSpec`` index for fast lookups.\n
    :returns: dictionary indexed by role key.\n
    """
    return {role["clave"]: role for role in ROLES}
