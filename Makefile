.PHONY: help lint format test clean install dev run setup-venv

# Display help information by default
help:
	@echo "Available commands:"
	@echo "  make help          - Show this help message"
	@echo "  make setup-venv    - Create Python 3.12 virtual environment"
	@echo "  make install       - Install production dependencies"
	@echo "  make dev           - Install development dependencies"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Run code formatters"
	@echo "  make test          - Run unit tests"
	@echo "  make run           - Run the Flask application with Doppler"
	@echo "  make clean         - Clean up build artifacts"

# Create Python 3.12 virtual environment
setup-venv:
	@echo "Creating Python 3.12 virtual environment..."
	python3.12 -m venv .venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  source .venv/bin/activate"
	@echo "Then run: make install"

# Run linting checks with Ruff
lint:
	@echo "Running Ruff linter..."
	uv run ruff format --check .
	uv run ruff check .

# Run code formatting with Ruff
format:
	@echo "Running Ruff linter with auto-fix..."
	uv run ruff format .
	uv run ruff check --fix .

# Run all tests
test:
	@echo "Running tests..."
	uv run pytest -m "not integration" --ignore=tests/evaluations/ --ignore=tests/integration/ -n auto

# Clean up build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Install production dependencies
install:
	@echo "Installing production dependencies..."
	uv sync

# Install development dependencies
dev:
	@echo "Installing development dependencies..."
	uv sync --dev

# Run the Flask application with Doppler
run:
	@echo "Starting Flask application with Doppler..."
	uv run flask run

run-worker:
	@echo "Starting worker..."
	uv run celery -A textlayer.applications.worker.app worker --loglevel=info
