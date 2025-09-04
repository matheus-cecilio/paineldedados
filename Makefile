# Optional Makefile shortcuts (Unix-like)
.PHONY: fmt lint test up migrate

fmt:
	black backend/app && isort backend/app

lint:
	flake8 backend/app

test:
	pytest -q

up:
	docker compose -f infra/docker-compose.dev.yml up --build

migrate:
	alembic -c backend/alembic.ini upgrade head
