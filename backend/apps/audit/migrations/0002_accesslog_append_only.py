"""DB-level append-only hardening of the access log live table.

Creates the shared guard function ``ledger_audit_append_only()`` and a
``BEFORE UPDATE OR DELETE`` trigger on ``audit_accesslog`` that rejects any
mutation (INSERT stays allowed — the only way to grow the trail).

The same guard is applied to the pghistory ``*event`` tables by the
``harden_events`` management command (idempotent), which runs after migrate so
the event tables already exist.

Idempotent and defensive: ``CREATE OR REPLACE FUNCTION`` + ``DROP TRIGGER IF
EXISTS`` before create; ``reverse_sql`` cleanly reverts.
"""
from __future__ import annotations

from django.db import migrations

_CREATE_GUARD_FUNCTION = """
CREATE OR REPLACE FUNCTION ledger_audit_append_only()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit log is append-only: % on % is not allowed',
        TG_OP, TG_TABLE_NAME
        USING ERRCODE = 'restrict_violation';
END;
$$;
"""

_DROP_GUARD_FUNCTION = "DROP FUNCTION IF EXISTS ledger_audit_append_only();"

_APPLY_TO_ACCESSLOG = """
REVOKE UPDATE, DELETE ON public.audit_accesslog FROM current_user;
DROP TRIGGER IF EXISTS ledger_audit_append_only_guard ON public.audit_accesslog;
CREATE TRIGGER ledger_audit_append_only_guard
    BEFORE UPDATE OR DELETE ON public.audit_accesslog
    FOR EACH ROW EXECUTE FUNCTION ledger_audit_append_only();
"""

_REVERSE_FROM_ACCESSLOG = """
DROP TRIGGER IF EXISTS ledger_audit_append_only_guard ON public.audit_accesslog;
GRANT UPDATE, DELETE ON public.audit_accesslog TO current_user;
"""


class Migration(migrations.Migration):
    """Apply the append-only guard to ``audit_accesslog``."""

    dependencies = [
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_CREATE_GUARD_FUNCTION, reverse_sql=_DROP_GUARD_FUNCTION
        ),
        migrations.RunSQL(
            sql=_APPLY_TO_ACCESSLOG, reverse_sql=_REVERSE_FROM_ACCESSLOG
        ),
    ]
