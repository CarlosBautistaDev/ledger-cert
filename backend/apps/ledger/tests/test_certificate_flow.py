"""Tests for the certificate lifecycle, signing, RBAC and immutability."""
from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction
from rest_framework import status

from apps.ledger.models import Certificate, EstadoCertificado

pytestmark = pytest.mark.django_db


def _create_draft(client, codigo: str = "CERT-T1") -> int:
    """Create a draft certificate via the API and return its id.\n
    :param client: authenticated DRF client (must have write authority).\n
    :param codigo: certificate code.\n
    :returns: the created certificate id.\n
    """
    resp = client.post(
        "/api/ledger/certificates/",
        {"codigo": codigo, "asunto": "Prueba", "veredicto": "CONFORME"},
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data
    return resp.data["id"]


def test_elaborador_creates_draft(auth_client, elaborador_user) -> None:
    """An Elaborador can create a certificate; it starts in BORRADOR.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param elaborador_user: seeded Elaborador user.\n
    """
    client = auth_client(elaborador_user)
    cert_id = _create_draft(client, codigo="CERT-DRAFT")
    cert = Certificate.objects.get(id=cert_id)
    assert cert.estado == EstadoCertificado.BORRADOR
    assert cert.firmada is False


def test_firmante_cannot_create_draft(auth_client, firmante_user) -> None:
    """Segregation of duties: a Firmante cannot draft certificates (403).\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param firmante_user: seeded Firmante user.\n
    """
    client = auth_client(firmante_user)
    resp = client.post(
        "/api/ledger/certificates/",
        {"codigo": "CERT-NODRAFT", "asunto": "x", "veredicto": "CONFORME"},
        format="json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_firmante_signs_certificate(
    auth_client, elaborador_user, firmante_user
) -> None:
    """A Firmante signs a draft elaborated by someone else; it becomes FIRMADO.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param elaborador_user: seeded Elaborador user (drafts).\n
    :param firmante_user: seeded Firmante user (signs).\n
    """
    cert_id = _create_draft(auth_client(elaborador_user), codigo="CERT-SIGN")
    resp = auth_client(firmante_user).post(
        f"/api/ledger/certificates/{cert_id}/sign/",
        {"password": "Ledger-Test-12345!"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK, resp.data
    cert = Certificate.objects.get(id=cert_id)
    assert cert.firmada is True
    assert cert.estado == EstadoCertificado.FIRMADO
    assert len(cert.firma_hash) == 64


def test_elaborador_cannot_sign(auth_client, elaborador_user) -> None:
    """Segregation of duties: an Elaborador lacks signing authority (403).\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param elaborador_user: seeded Elaborador user.\n
    """
    client = auth_client(elaborador_user)
    cert_id = _create_draft(client, codigo="CERT-NOSIGN")
    resp = client.post(
        f"/api/ledger/certificates/{cert_id}/sign/",
        {"password": "Ledger-Test-12345!"},
        format="json",
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_signed_certificate_is_immutable_at_db_level(
    auth_client, admin_user
) -> None:
    """A direct SQL UPDATE on a signed certificate is rejected by the trigger.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param admin_user: seeded admin (can create and sign).\n
    """
    client = auth_client(admin_user)
    cert_id = _create_draft(client, codigo="CERT-IMMUT")
    client.post(
        f"/api/ledger/certificates/{cert_id}/sign/",
        {"password": "Ledger-Test-12345!"},
        format="json",
    )

    from django.db import connection

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE ledger_certificate SET asunto = %s WHERE id = %s",
                    ["hacked", cert_id],
                )


def test_draft_certificate_is_editable(auth_client, elaborador_user) -> None:
    """A draft (unsigned) certificate can still be edited via the API.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param elaborador_user: seeded Elaborador user.\n
    """
    client = auth_client(elaborador_user)
    cert_id = _create_draft(client, codigo="CERT-EDIT")
    resp = client.patch(
        f"/api/ledger/certificates/{cert_id}/",
        {"asunto": "Asunto corregido"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK, resp.data
    assert Certificate.objects.get(id=cert_id).asunto == "Asunto corregido"


def test_admin_supersedes_a_signed_certificate_without_changing_the_original(
    auth_client, admin_user
) -> None:
    """Crea la correccion firmada sin tocar el certificado original.\n
    :param auth_client: factory that authenticates the client as a user.\n
    :param admin_user: seeded admin (can create and sign).\n
    """
    client = auth_client(admin_user)
    cert_id = _create_draft(client, codigo="CERT-SUP")
    client.post(
        f"/api/ledger/certificates/{cert_id}/sign/",
        {"password": "Ledger-Test-12345!"},
        format="json",
    )
    original = Certificate.objects.get(id=cert_id)
    original_asunto = original.asunto
    original_hash = original.firma_hash
    resp = client.post(
        f"/api/ledger/certificates/{cert_id}/supersede/",
        {
            "codigo": "CERT-SUP-OK",
            "asunto": "Asunto ya corregido",
            "emitido_a": "Cliente corregido",
            "veredicto": "NO_CONFORME",
            "observaciones": "Se corrigio el dato del asunto.",
            "password": "Ledger-Test-12345!",
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED, resp.data

    original.refresh_from_db()
    reemplazo = Certificate.objects.get(id=resp.data["id"])
    assert original.estado == EstadoCertificado.FIRMADO
    assert original.asunto == original_asunto
    assert original.firma_hash == original_hash
    assert original.esta_vigente is False
    assert reemplazo.reemplaza_id == original.id
    assert reemplazo.estado == EstadoCertificado.FIRMADO
    assert reemplazo.firmada is True
    assert reemplazo.esta_vigente is True


def test_supersede_rejects_a_second_correction(auth_client, admin_user) -> None:
    """No deja crear dos correcciones directas del mismo certificado."""
    client = auth_client(admin_user)
    cert_id = _create_draft(client, codigo="CERT-SUP-ONCE")
    client.post(
        f"/api/ledger/certificates/{cert_id}/sign/",
        {"password": "Ledger-Test-12345!"},
        format="json",
    )
    datos = {
        "codigo": "CERT-SUP-ONCE-1",
        "asunto": "Correccion",
        "veredicto": "CONFORME",
        "password": "Ledger-Test-12345!",
    }
    assert client.post(
        f"/api/ledger/certificates/{cert_id}/supersede/", datos, format="json"
    ).status_code == status.HTTP_201_CREATED

    datos["codigo"] = "CERT-SUP-ONCE-2"
    resp = client.post(
        f"/api/ledger/certificates/{cert_id}/supersede/", datos, format="json"
    )
    assert resp.status_code == status.HTTP_409_CONFLICT
