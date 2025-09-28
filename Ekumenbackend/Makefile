.PHONY: help build up down logs clean migrate migration backup restore test format lint

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose --profile development up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs for all services
	docker-compose logs -f

logs-api: ## Show API logs
	docker-compose logs -f api

logs-worker: ## Show worker logs
	docker-compose logs -f worker

logs-db: ## Show database logs
	docker-compose logs -f postgres

clean: ## Clean up containers and volumes
	docker-compose down -v --remove-orphans
	docker system prune -f

migrate: ## Run database migrations
	docker-compose exec api poetry run alembic upgrade head

migration: ## Create new migration (usage: make migration name="migration_name")
	docker-compose exec api poetry run alembic revision --autogenerate -m "$(name)"

backup: ## Backup database
	docker-compose exec postgres pg_dump -U agri_user agri_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restore database (usage: make restore file=backup.sql)
	docker-compose exec -T postgres psql -U agri_user agri_db < $(file)

test: ## Run tests
	docker-compose exec api poetry run pytest

format: ## Format code with black and isort
	docker-compose exec api poetry run black .
	docker-compose exec api poetry run isort .

lint: ## Run linting
	docker-compose exec api poetry run flake8 .
	docker-compose exec api poetry run mypy .

shell: ## Open shell in API container
	docker-compose exec api bash

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U agri_user agri_db

redis-shell: ## Open Redis shell
	docker-compose exec redis redis-cli

seed: ## Seed database with initial data
	docker-compose exec api poetry run python scripts/seed_data.py

sync-mesparcelles: ## Sync data from MesParcelles (usage: make sync-mesparcelles siret=12345678901234)
	curl -X POST "http://localhost:8000/api/v1/tasks/sync/exploitation/$(siret)?millesime=2024"

import-ephy: ## Import EPHY data from ZIP file
	curl -X POST "http://localhost:8000/api/v1/tasks/ephy/import-zip" \
		-H "Content-Type: application/json" \
		-d '{"zip_path": "/app/data/ephy/decisionamm-intrant-format-csv-20250923-windows-1252.zip"}'

test-ephy: ## Test EPHY import functionality
	docker-compose exec api python scripts/test_ephy_import.py

health: ## Check API health
	curl http://localhost:8000/health

docs: ## Open API documentation
	@echo "API Documentation: http://localhost:8000/docs"
	@echo "ReDoc: http://localhost:8000/redoc"
	@echo "Flower (Celery): http://localhost:5555"

dev: ## Start development environment
	docker-compose --profile development up -d
	@echo "Development environment started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Flower: http://localhost:5555"

prod: ## Start production environment
	docker-compose --profile production up -d
	@echo "Production environment started!"
