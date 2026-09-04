# ==========================================
# Configuration
# ==========================================
COMPOSE = docker compose
DEV_FILES = --env-file ./video-api/.env -f docker-compose.yml -f docker-compose.dev.yml

PROD_FILES = --env-file ./video-api/.env.production -f docker-compose.yml -f docker-compose.prod.yml

# ==========================================
# Development
# ==========================================
.PHONY: dev
dev:
	$(COMPOSE) $(DEV_FILES) up

.PHONY: dev-d
dev-d:
	$(COMPOSE) $(DEV_FILES) up -d

.PHONY: build
build:
	$(COMPOSE) $(DEV_FILES) build

.PHONY: rebuild
rebuild:
	$(COMPOSE) $(DEV_FILES) build --no-cache

.PHONY: down
down:
	$(COMPOSE) $(DEV_FILES) down

.PHONY: logs
logs:
	$(COMPOSE) $(DEV_FILES) logs -f

.PHONY: backend-logs
backend-logs:
	$(COMPOSE) $(DEV_FILES) logs -f backend

# ==========================================
# Alembic
# ==========================================
.PHONY: migrate
migrate:
	$(COMPOSE) $(DEV_FILES) exec backend alembic upgrade head

.PHONY: migration
migration:
	@test -n "$(msg)" || (echo "Usage: make migration msg=\"add email to users\"" && exit 1)
	$(COMPOSE) $(DEV_FILES) exec backend alembic revision --autogenerate -m "$(msg)"

.PHONY: migration-history
migration-history:
	$(COMPOSE) $(DEV_FILES) exec backend alembic history

.PHONY: migration-current
migration-current:
	$(COMPOSE) $(DEV_FILES) exec backend alembic current

# ==========================================
# Backend
# ==========================================
.PHONY: shell
shell:
	$(COMPOSE) $(DEV_FILES) exec backend bash

.PHONY: test
test:
	$(COMPOSE) $(DEV_FILES) exec backend pytest

# ==========================================
# Production
# ==========================================
.PHONY: prod-build
prod-build:
	$(COMPOSE) $(PROD_FILES) build

.PHONY: prod-up
prod-up:
	$(COMPOSE) $(PROD_FILES) up -d

.PHONY: prod-down
prod-down:
	$(COMPOSE) $(PROD_FILES) down

.PHONY: prod-migrate
prod-migrate:
	$(COMPOSE) $(PROD_FILES) run --rm migrate

.PHONY: prod-logs
prod-logs:
	$(COMPOSE) $(PROD_FILES) logs -f


# ======================================
# Help
# ======================================
.PHONY: help
help:
	@echo "Development:"
	@echo "  make dev                     Start development environment"
	@echo "  make dev-d                   Start development in background"
	@echo "  make build                   Build development images"
	@echo "  make rebuild                 Rebuild without cache"
	@echo "  make down                    Stop development environment"
	@echo "  make logs                    Follow all logs"
	@echo "  make backend-logs            Follow backend logs"
	@echo "  make shell                   Open backend shell"
	@echo "  make test                    Run tests"
	@echo ""
	@echo "Alembic:"
	@echo "  make migration msg=\"...\"   Generate migration"
	@echo "  make migrate                 Apply migrations"
	@echo "  make migration-current       Show current revision"
	@echo "  make migration-history       Show migration history"
	@echo ""
	@echo "Production:"
	@echo "  make prod-build              Build production images"
	@echo "  make deploy                  Deploy"
	@echo "  make prod-migrate            Run production migrations"
	@echo "  make prod-down               Stop production"
	@echo "  make prod-logs               Follow production logs"
    