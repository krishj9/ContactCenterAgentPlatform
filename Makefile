.PHONY: help up up-mock down seed test lint format migrate

help:
	@echo "Available commands:"
	@echo "  make up        - Start full Docker Compose stack (postgres pgvector, redis, api, web)"
	@echo "  make up-mock   - Start local mock platform with in-memory adapters and dev servers"
	@echo "  make down      - Tear down Docker Compose containers and volumes"
	@echo "  make seed      - Execute database migrations and seed baseline corpus"
	@echo "  make test      - Run offline test suite via pytest"
	@echo "  make lint      - Run linters and typecheckers (ruff, mypy)"
	@echo "  make format    - Autoformat backend and frontend code"
	@echo "  make migrate   - Run Alembic database migrations"

up:
	docker compose -f infra/compose/docker-compose.yml up -d --build

up-mock:
	@echo "Starting Contact Center platform in mock mode (APP_PROFILE=test)..."
	@if command -v docker >/dev/null 2>&1; then \
		docker compose -f infra/compose/docker-compose.yml up -d postgres redis fake-gcs-server; \
	fi
	@echo "Running backend on http://localhost:8000 and frontend on http://localhost:3000..."

down:
	@if command -v docker >/dev/null 2>&1; then \
		docker compose -f infra/compose/docker-compose.yml down; \
	fi

migrate:
	CC_APP_PROFILE=local uv run alembic -c backend/alembic.ini upgrade head

seed:
	@echo "Validating taxonomy..."
	uv run python -m pipeline.taxonomy validate
	@echo "Tagging FAQs..."
	uv run python -m pipeline.jobs.tag_faq_intents
	@echo "Generating corpus manifest..."
	uv run python -m pipeline.manifest
	@echo "Running quality assertions..."
	uv run python -m pipeline.quality.coverage_check
	uv run python -m pipeline.quality.pii_check
	@echo "Running baseline intent evaluation..."
	uv run python eval/baseline_intent_eval.py

test:
	uv run pytest backend/tests/ -v

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy backend/app backend/tests eval
	cd apps/web && npm run build

format:
	uv run ruff check --fix .
	uv run ruff format .
