#!/bin/bash
set -e

echo "=== Guard-IA Development Setup ==="

# Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi

# Backend setup
echo "Setting up backend..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cd ..

# Frontend setup
echo "Setting up frontend..."
cd frontend
npm install
cd ..

# Start DB and MLflow
echo "Starting Docker services..."
docker compose up -d db mlflow

# Wait for DB
echo "Waiting for PostgreSQL..."
sleep 5

# Run migrations
echo "Running migrations..."
cd backend
alembic upgrade head
cd ..

echo "=== Setup complete! ==="
echo "Run 'make dev' to start development servers."
