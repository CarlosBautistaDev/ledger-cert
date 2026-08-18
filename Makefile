# ===========================================================================
# Ledger de Certificados de Conformidad — Makefile
# Orquesta el stack docker compose de 4 contenedores (db/api/web/proxy).
# ===========================================================================

COMPOSE ?= docker compose

.DEFAULT_GOAL := help

.PHONY: help up down build rebuild logs migrate makemigrations seed \
        createsuperuser restart ps sh-api sh-web test-backend test-frontend ci

help: ## Muestra esta ayuda
	@echo "Ledger de Certificados — comandos disponibles:"
	@echo ""
	@echo "  make up               Levanta el stack (build + arranque en segundo plano)"
	@echo "  make down             Detiene y elimina los contenedores"
	@echo "  make build            Construye las imágenes (api, web)"
	@echo "  make rebuild          Reconstruye sin caché y reinicia"
	@echo "  make logs             Sigue los logs de todos los servicios"
	@echo "  make migrate          Aplica migraciones de Django"
	@echo "  make makemigrations   Genera nuevas migraciones de Django"
	@echo "  make seed             Ejecuta el seed idempotente (seed_initial)"
	@echo "  make createsuperuser  Crea un superusuario interactivo"
	@echo "  make restart          Reinicia todos los servicios"
	@echo "  make ps               Estado de los contenedores"
	@echo "  make sh-api           Shell dentro del contenedor api"
	@echo "  make sh-web           Shell dentro del contenedor web"
	@echo "  make test-backend     Pruebas backend (pytest)"
	@echo "  make test-frontend    Typecheck + lint + build del frontend"
	@echo ""
	@echo "Arranque rápido:  cp .env.example .env && make up   ->  https://localhost:8443"

up: ## Levanta el stack completo
	$(COMPOSE) up -d --build

down: ## Detiene y elimina contenedores
	$(COMPOSE) down

build: ## Construye las imágenes
	$(COMPOSE) build

rebuild: ## Reconstruye sin caché y reinicia
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

logs: ## Sigue los logs de todos los servicios
	$(COMPOSE) logs -f

migrate: ## Aplica migraciones de Django
	$(COMPOSE) exec api python manage.py migrate

makemigrations: ## Genera nuevas migraciones de Django
	$(COMPOSE) exec api python manage.py makemigrations

seed: ## Ejecuta el seed idempotente (roles + admin + certificados de ejemplo)
	$(COMPOSE) exec api python manage.py seed_initial

createsuperuser: ## Crea un superusuario interactivo
	$(COMPOSE) exec api python manage.py createsuperuser

restart: ## Reinicia todos los servicios
	$(COMPOSE) restart

ps: ## Estado de los contenedores
	$(COMPOSE) ps

sh-api: ## Shell dentro del contenedor api
	$(COMPOSE) exec api sh

sh-web: ## Shell dentro del contenedor web
	$(COMPOSE) exec web sh

test-backend: ## Pruebas backend (pytest) sobre el árbol de trabajo
	MSYS_NO_PATHCONV=1 $(COMPOSE) run --rm -v "$(CURDIR)/backend:/app" \
		-e DJANGO_SETTINGS_MODULE=config.settings.dev --entrypoint python api \
		manage.py makemigrations accounts audit ledger --noinput
	MSYS_NO_PATHCONV=1 $(COMPOSE) run --rm -v "$(CURDIR)/backend:/app" \
		-e DJANGO_SETTINGS_MODULE=config.settings.dev --entrypoint python api \
		-m pytest -q --no-cov

test-frontend: ## Typecheck + lint + build del frontend (host)
	cd frontend && npm run typecheck && npm run lint && npm run build

ci: test-backend test-frontend ## Gate de CI completo (backend + frontend)
	@echo "CI local OK."
