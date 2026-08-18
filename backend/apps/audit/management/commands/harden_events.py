"""Management command: harden pghistory ``*event`` tables as append-only.

Runs after ``migrate`` (from the entrypoint), once the pghistory event tables
already exist. For every ``public.*event`` table it:

1. ``REVOKE UPDATE, DELETE`` from the application role, and
2. installs a ``BEFORE UPDATE OR DELETE`` trigger using the shared guard
   function ``ledger_audit_append_only`` (created by ``audit/0002``).

Idempotent: uses ``DROP TRIGGER IF EXISTS`` before create and a dynamic
catalog-driven loop, so it can run on every boot without error.
"""
from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db import connection

_HARDEN_EVENT_TABLES = """
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

DO $$
DECLARE
    t text;
BEGIN
    FOR t IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename LIKE '%event'
    LOOP
        EXECUTE format(
            'REVOKE UPDATE, DELETE ON public.%I FROM %I', t, current_user
        );
        EXECUTE format(
            'DROP TRIGGER IF EXISTS ledger_audit_append_only_guard ON public.%I',
            t
        );
        EXECUTE format(
            'CREATE TRIGGER ledger_audit_append_only_guard '
            'BEFORE UPDATE OR DELETE ON public.%I '
            'FOR EACH ROW EXECUTE FUNCTION ledger_audit_append_only()', t
        );
    END LOOP;
END;
$$;
"""


class Command(BaseCommand):
    """Install the append-only guard on all pghistory ``*event`` tables."""

    help = "Harden pghistory *event tables as append-only (REVOKE + trigger)."

    def handle(self, *args: Any, **options: Any) -> None:
        """Run the idempotent hardening SQL block.

        :param args: positional command args (unused).
        :param options: command options (unused).
        :rtype: None
        """
        with connection.cursor() as cursor:
            cursor.execute(_HARDEN_EVENT_TABLES)
        self.stdout.write(
            self.style.SUCCESS("Append-only guard applied to *event tables.")
        )
