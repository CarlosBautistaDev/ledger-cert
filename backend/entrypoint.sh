#!/usr/bin/env bash
# =============================================================================
# Ledger de Certificados — Backend entrypoint
#
# Orquesta el arranque del contenedor `api` sin pasos manuales:
#   1. Espera a que PostgreSQL acepte conexiones.
#   2. makemigrations (dev) + migrate.
#   3. harden_events: instala el REVOKE + trigger append-only sobre las tablas
#      de eventos de pghistory (idempotente; corre tras migrate para que las
#      tablas *event ya existan).
#   4. Seed idempotente (roles, admin, certificados de ejemplo).
#   5. collectstatic (solo en producción) y arranque del CMD (gunicorn).
# =============================================================================
set -euo pipefail

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_USER="${POSTGRES_USER:-ledger}"
SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.prod}"
export DJANGO_SETTINGS_MODULE="${SETTINGS_MODULE}"

echo "[entrypoint] Settings: ${DJANGO_SETTINGS_MODULE}"

# --- 1) Esperar a PostgreSQL -------------------------------------------------
echo "[entrypoint] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} ..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" >/dev/null 2>&1; do
    echo "[entrypoint]   ...Postgres not ready yet, retrying in 1s."
    sleep 1
done
echo "[entrypoint] PostgreSQL is up."

# --- 2) Migraciones ----------------------------------------------------------
# En dev generamos las migraciones de tracking (pghistory/simple_history) al
# vuelo; en prod solo aplicamos las ya versionadas.
if [ "${DJANGO_SETTINGS_MODULE}" = "config.settings.dev" ]; then
    echo "[entrypoint] makemigrations (dev) ..."
    python manage.py makemigrations accounts audit ledger --noinput
fi

echo "[entrypoint] migrate ..."
python manage.py migrate --noinput

# --- 3) Endurecimiento append-only de las tablas de eventos ------------------
echo "[entrypoint] harden_events (append-only *event tables) ..."
python manage.py harden_events

# --- 4) Seed idempotente -----------------------------------------------------
echo "[entrypoint] seed_initial ..."
python manage.py seed_initial

# --- 5) Estáticos (prod) + arranque -----------------------------------------
if [ "${DJANGO_SETTINGS_MODULE}" = "config.settings.prod" ]; then
    echo "[entrypoint] collectstatic ..."
    python manage.py collectstatic --noinput
fi

echo "[entrypoint] Starting: $*"
exec "$@"
