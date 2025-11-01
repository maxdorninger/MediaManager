SHELL := /bin/bash

# Docker Compose command (override if needed)
COMPOSE ?= docker compose
DC := $(COMPOSE) -f docker-compose.dev.yaml

# Log args passthrough, e.g.:
# make logs ARGS="--follow --tail=100"
ARGS ?=

# Service names (override if your compose uses different names)
APP_SVC ?= mediamanager
FRONTEND_SVC ?= frontend

.PHONY: help up down logs ps restartapp frontend

help:
	@echo "Usage:"
	@echo "  All commands run using the dev docker compose file ($(DEV_FILE))"
	@echo ""
	@echo "  make up                     # Development environment up, runs with --build flag to rebuild if necessary"
	@echo "  make down                   # Development environment down"
	@echo "  make logs ARGS=\"...\"        # (Optional) Set ARGS like \"--follow --tail=100\""
	@echo "  make ps | restart           # Check status or restart containers"
	@echo "  make app                    # Shell into $(APP_SVC) container"
	@echo "  make frontend               # Shell into $(FRONTEND_SVC) container"

# Core lifecycle
up:
	$(DC) up -d --build

down:
	$(DC) down

logs:
	$(DC) logs $(ARGS)

ps:
	$(DC) ps

restart:
	$(DC) restart

# Interactive shells (prefer bash, fallback to sh)
app:
	@$(DC) exec -it $(APP_SVC) bash 2>/dev/null || $(DC) exec -it $(APP_SVC) sh

frontend:
	@$(DC) exec -it $(FRONTEND_SVC) bash 2>/dev/null || $(DC) exec -it $(FRONTEND_SVC) sh