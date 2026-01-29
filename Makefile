.PHONY: dev dev-gateway dev-all stop setup test lint migrate train-model evaluate-model simulate

# Setup completo
setup:
	cp .env.example .env
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install
	docker compose up -d db mlflow
	cd backend && .venv/bin/alembic upgrade head
	@echo "Setup complete. Run 'make dev' to start."

# Dev servers
dev:
	docker compose up -d db mlflow
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev &

stop:
	-@lsof -ti :8000 | xargs kill 2>/dev/null; true
	-@lsof -ti :3000 | xargs kill 2>/dev/null; true
	@sleep 1
	@echo "Dev servers stopped."

dev-gateway:
	docker compose up -d db mlflow
	cd backend && .venv/bin/python -m app.gateway.server &

dev-all:
	docker compose up -d db mlflow
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000 &
	cd backend && .venv/bin/python -m app.gateway.server &
	cd frontend && npm run dev &

# Tests
test-backend:
	cd backend && .venv/bin/pytest -v

test-frontend:
	cd frontend && npm run test

test: test-backend test-frontend

# Linting
lint-backend:
	cd backend && .venv/bin/ruff check . && .venv/bin/mypy .

lint-frontend:
	cd frontend && npm run lint

lint: lint-backend lint-frontend

# Database
migrate:
	cd backend && .venv/bin/alembic upgrade head

migration:
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(msg)"

# ML Model
train-model:
	cd ml && python src/train.py

evaluate-model:
	cd ml && python src/evaluate.py

# Email Simulation (requires gateway running: make dev-gateway)
simulate:
	cd backend && .venv/bin/python -m scripts.simulate_email --all

simulate-clean:
	cd backend && .venv/bin/python -m scripts.simulate_email -t clean

simulate-phishing:
	cd backend && .venv/bin/python -m scripts.simulate_email -t phishing

simulate-bec:
	cd backend && .venv/bin/python -m scripts.simulate_email -t bec

simulate-malware:
	cd backend && .venv/bin/python -m scripts.simulate_email -t malware

simulate-spear:
	cd backend && .venv/bin/python -m scripts.simulate_email -t spear

simulate-load:
	cd backend && .venv/bin/python -m scripts.simulate_email --all --count 5 --delay 0.5

simulate-list:
	cd backend && .venv/bin/python -m scripts.simulate_email --list

# Docker
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build
