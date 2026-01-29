.PHONY: help install dev lint format test clean db-up db-down db-reset run cli

help:
	@echo "ISW Company Similarity - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Install dev dependencies"
	@echo ""
	@echo "Database:"
	@echo "  make db-up         - Start PostgreSQL container"
	@echo "  make db-down       - Stop PostgreSQL container"
	@echo "  make db-reset      - Reset database (removes all data)"
	@echo ""
	@echo "Development:"
	@echo "  make lint          - Check code with ruff"
	@echo "  make format        - Format code with ruff"
	@echo "  make test          - Run tests"
	@echo "  make run           - Start Flask API server"
	@echo "  make cli           - Show CLI commands"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Remove build artifacts"

install:
	uv sync

dev:
	uv sync --dev

lint:
	uv run ruff format --check .
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest tests/unit/ -v
	uv run pytest tests/integration/ -v

clean:
	rm -rf .ruff_cache .pytest_cache .coverage htmlcov __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

db-up:
	docker-compose up -d

db-down:
	docker-compose down

db-reset:
	docker-compose down -v
	docker-compose up -d

run:
	@echo "Starting Flask API on http://127.0.0.1:5000/v1/"
	uv run flask run

cli:
	@echo "Database commands:"
	@echo "  isw-company-similarity-cli database init"
	@echo "  isw-company-similarity-cli database load-companies data/security.csv"
	@echo "  isw-company-similarity-cli database load-facts data/companyfacts.csv"
	@echo "  isw-company-similarity-cli database status"
