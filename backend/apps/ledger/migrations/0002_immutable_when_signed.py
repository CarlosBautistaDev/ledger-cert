"""DB-level immutability of a signed certificate.

The immutability is **conditional on the signature**: a certificate in BORRADOR
(``firmada = false``) is still editable; once **signed** (``firmada = true``)
the row becomes immutable and a ``BEFORE UPDATE OR DELETE`` trigger rejects any
mutation. A post-signature correction is done by **supersession** (a new
certificate by supersession), never by editing.

The guard evaluates ``OLD.firmada`` (previous state): a signed row cannot
mutate, while a draft can — including the very transition that sets
``firmada = true``.

Idempotent and defensive: ``CREATE OR REPLACE FUNCTION`` + ``DROP TRIGGER IF
EXISTS`` before create; ``reverse_sql`` cleanly reverts.
"""
from __future__ import annotations

from django.db import migrations

_CREATE_GUARD = """
CREATE OR REPLACE FUNCTION ledger_certificate_immutable_when_signed()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF (TG_OP = 'DELETE' OR TG_OP = 'UPDATE') AND OLD.firmada IS TRUE THEN
        RAISE EXCEPTION
            'certificado firmado es inmutable: % on % no permitido',
            TG_OP, TG_TABLE_NAME
            USING ERRCODE = 'restrict_violation';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;
"""

_DROP_GUARD = (
    "DROP FUNCTION IF EXISTS ledger_certificate_immutable_when_signed();"
)

_APPLY_TRIGGER = """
DROP TRIGGER IF EXISTS ledger_certificate_immutable_guard
    ON ledger_certificate;
CREATE TRIGGER ledger_certificate_immutable_guard
    BEFORE UPDATE OR DELETE ON ledger_certificate
    FOR EACH ROW EXECUTE FUNCTION ledger_certificate_immutable_when_signed();
"""

_REVERSE_TRIGGER = """
DROP TRIGGER IF EXISTS ledger_certificate_immutable_guard
    ON ledger_certificate;
"""


class Migration(migrations.Migration):
    """Install the immutable-when-signed guard on ``ledger_certificate``."""

    dependencies = [
        ("ledger", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=_CREATE_GUARD, reverse_sql=_DROP_GUARD),
        migrations.RunSQL(sql=_APPLY_TRIGGER, reverse_sql=_REVERSE_TRIGGER),
    ]
