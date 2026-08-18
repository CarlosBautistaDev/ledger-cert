# =============================================================================
# Ledger de Certificados — Backend (Django 5.2 + gunicorn)
# =============================================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Cliente de Postgres para el wait del entrypoint.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependencias primero (capa cacheable). Por defecto SOLO producción;
# la imagen dev/CI añade el tooling de test con --build-arg INSTALL_DEV=true.
ARG INSTALL_DEV=false
COPY requirements.txt requirements-dev.txt /app/
RUN pip install -r /app/requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then pip install -r /app/requirements-dev.txt; fi

COPY . /app

RUN chmod +x /app/entrypoint.sh

# Usuario no-root (hardening).
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
