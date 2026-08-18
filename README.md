# Ledger de Certificados de Conformidad

> Sistema de **registros firmados e inmutables**: un ledger de *certificados de
> conformidad*. Es un proyecto de base para una prueba técnica.

Aplicación **construida a medida, dockerizada y standalone** (local). Registra
certificados de conformidad, su firma electrónica y su ciclo de vida, con
control de usuarios/roles (RBAC) y un audit trail a nivel de base de datos.

El dominio es deliberadamente sencillo; lo importante son sus **invariantes de
cumplimiento** (alineadas con **ISO 10012:2026** y el principio **ALCOA+**): un
certificado **firmado** es evidencia regulatoria — queda **inmutable** y **no se
elimina ni se edita**; cualquier corrección se hace por **supersesión** (una
versión nueva que reemplaza a la anterior), nunca tocando el original.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.12 · Django 5.2 LTS · Django REST Framework · SimpleJWT (access 15 min + refresh rotado + blacklist) · psycopg 3 · django-pghistory (triggers PostgreSQL) · django-simple-history · django-axes · Argon2id · Gunicorn |
| **Base de datos** | PostgreSQL 17 |
| **Frontend** | Node 20 · React 18 · Vite 5 · TypeScript · TailwindCSS + shadcn/ui (Radix) · TanStack Query · react-router-dom v6 · react-hook-form + Zod · axios · react-i18next |
| **Infra** | docker compose · **4 contenedores** (db, api, web, proxy=Caddy con TLS interno) |

---

## Arquitectura (4 contenedores)

Solo el **proxy** expone puertos al host. `db`, `api` y `web` viven en la red
interna `ledger` y no publican puertos.

```
Navegador ──HTTPS──> proxy (Caddy, TLS interno)
                       ├── /api, /admin, /static ──> api (Django + Gunicorn) ──> db (PostgreSQL 17)
                       └── /*                    ──> web (SPA React/Vite, nginx-unprivileged)
```

| Contenedor | Imagen | Rol | Puerto |
|------------|--------|-----|--------|
| `db` | `postgres:17` | Datos del ledger (volumen `pgdata`). | interno 5432 |
| `api` | build `./backend` | API REST + Django Admin. | interno 8000 |
| `web` | build `./frontend` | SPA estática React/Vite. | interno 8080 |
| `proxy` | `caddy:2-alpine` | Reverse proxy + TLS interno. | **8080 / 8443 al host** |

---

## Cómo levantarlo (local)

Requisitos: **Docker** + **Docker Compose v2**.

```bash
cp .env.example .env        # (necesario la primera vez)
make up                     # build + arranque en segundo plano
```

Luego abre **https://localhost:8443** (acepta el aviso de certificado — es la
CA interna de Caddy en dev) e inicia sesión con las credenciales del seed.

> Sin `make`: `cp .env.example .env && docker compose up -d --build`.

El arranque es automático (`backend/entrypoint.sh`): espera a Postgres →
`migrate` → `harden_events` (endurece las tablas de auditoría) → `seed_initial`
→ Gunicorn.

### Usuario del seed

| Rol | Email | Contraseña | Puede |
|-----|-------|-----------|-------|
| Admin (superusuario) | `admin@ledger.local` | `changeme-admin` (de `.env`) | todo |

El sistema arranca **solo con el Admin**. Dar de alta a los demás usuarios y
roles (Elaborador, Firmante, Auditor) requiere la **gestión de usuarios**, que
está **pendiente de implementar** (ver «Pendiente de implementar»).

### Comandos útiles

| Comando | Acción |
|---------|--------|
| `make up` / `make down` | Levanta / detiene el stack |
| `make logs` | Sigue los logs |
| `make ps` | Estado de los contenedores |
| `make sh-api` | Shell en el contenedor `api` |
| `make test-backend` | Pruebas backend (pytest) |
| `make test-frontend` | Typecheck + lint + build del frontend |

---

## Roles (RBAC)

Los roles son el **contrato del dominio** (definidos en
`backend/apps/accounts/roles.py`), con **segregación de funciones**:

| Rol | Alcance |
|-----|---------|
| **Admin** | Acceso total: gestión de usuarios/roles; además crea y firma. |
| **Elaborador** | Crea y edita certificados en **borrador**. **No firma.** |
| **Firmante** | **Firma** certificados (autoridad de aceptación). No elabora. |
| **Auditor** | **Solo lectura** en todo el sistema. |

> El seed materializa **solo el rol Admin**. Crear los grupos Elaborador /
> Firmante / Auditor y los usuarios que los tengan es parte de la gestión que
> hay que implementar (ver «Pendiente de implementar»).

---

## Ciclo de vida del certificado

```
BORRADOR ──(firmar: re-autenticación + hash)──> FIRMADO ──(supersesión)──> [nuevo] ; el original queda REEMPLAZADO
```

- **BORRADOR**: editable.
- **FIRMADO**: **inmutable** a nivel de base de datos (un trigger de PostgreSQL
  rechaza `UPDATE`/`DELETE` de una fila firmada).
- La corrección de un certificado firmado se hace por **supersesión**.

> La corrección por supersesión está **pendiente de implementar** (hoy la acción
> devuelve `501` y el botón «Corregir» está deshabilitado): es una de las tareas
> de la prueba — ver **«Tareas de la prueba técnica»** al final.

---

## API (prefijo `/api`)

- `POST /api/auth/login/` · `POST /api/auth/refresh/` · `POST /api/auth/logout/` · `GET /api/auth/me/`
- `GET /api/roles/` · `GET /api/users/` (listado, solo Admin — la gestión CRUD está pendiente)
- `/api/ledger/certificates/` (list, create) · `GET /api/ledger/certificates/{id}/`
- `POST /api/ledger/certificates/{id}/sign/` · `POST /api/ledger/certificates/{id}/supersede/` (pendiente)
- OpenAPI: `GET /api/schema/` · Swagger UI: `/api/docs/`

---

## Auditoría e integridad

- **Audit trail DB-level** con `django-pghistory` (triggers → tablas `*event`)
  + `django-simple-history` (tablas `Historical*`).
- **Append-only**: las tablas de eventos y el log de accesos rechazan
  `UPDATE`/`DELETE` (REVOKE + trigger).
- **Inmutabilidad al firmar**: trigger sobre `ledger_certificate`.
- **Firma electrónica básica**: SHA-256 del contenido canónico + re-autenticación.
- **Login endurecido**: Argon2id + lockout con `django-axes`.

---

## Tareas de la prueba técnica


### 1. Corrección de un certificado firmado

Implementa la corrección de un certificado **firmado**. Hoy
`POST /api/ledger/certificates/{id}/supersede/` devuelve `501` y el botón
«Corregir» del frontend está deshabilitado.

Un certificado firmado **no se edita ni se elimina**. Ante un error, se emite un
certificado **corregido** que pasa a ser el **único válido y vigente**; el
original se conserva íntegro como registro histórico, sin alterarse. Todo el
diseño —modelo, estados, permisos, endpoint y frontend— lo decides tú. Deja el
botón «Corregir» funcional para quien corresponda.

### 2. Gestión de usuarios y roles (backend + frontend)

El sistema arranca **solo con el Admin**. Implementa la gestión que permita al
Admin **crear usuarios y asignarles los roles** del sistema (Elaborador,
Firmante, Auditor), tanto en el **backend** (API) como en el **frontend** (una
pantalla de administración).

Los roles y su alcance ya están definidos como contrato del dominio en
`backend/apps/accounts/roles.py`; tu tarea es la **gestión** (altas de usuarios,
asignación de roles), integrada con lo que el proyecto ya trae.

### 3. Una situación (pregunta abierta)

El área encargada del control de certificados te solicita **eliminar el
certificado `CERT-0002`** (el certificado firmado del seed). La petición te llega
por un ticket, o te la piden durante una llamada. **¿Cómo procedes?**

Responde en `DECISIONS.md`: qué haces, qué preguntas o verificas, y por qué.

### Entregable

- El repositorio con tus cambios (una rama o commits claros); que **levante** y
  las pruebas pasen.
