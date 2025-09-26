# TextLayer Core New

A new architectural pattern for Python services with improved modularity and separation of concerns.

## Architecture

This project follows a new architectural pattern with the following structure:

- **applications/**: Entry points for different application types (API, CLI, Worker)
- **interfaces/**: Interface adapters for different protocols and frameworks
- **core/**: Core business logic, services, and domain models
- **shared/**: Shared utilities, configuration, and common functionality

## Setup

### Prerequisites

- Python 3.12
- pip
- make
- Doppler CLI

### Quick Start

1. **Create virtual environment:**
   ```bash
   make setup-venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   make install
   ```

3. **Set up Doppler:**
   ```bash
   doppler setup
   ```

4. **Run the application:**
   ```bash
   make run
   ```

## Development

### Available Commands

- `make help` - Show available commands
- `make setup-venv` - Create Python 3.12 virtual environment
- `make install` - Install production dependencies
- `make dev` - Install development dependencies
- `make lint` - Run linting checks
- `make format` - Format code
- `make test` - Run tests with Doppler
- `make run` - Run Flask application with Doppler
- `make clean` - Clean build artifacts

### Development Setup

1. Install development dependencies:
   ```bash
   make dev
   ```

2. Run tests:
   ```bash
   make test
   ```

## Project Structure

```
textlayer/
├── applications/          # Application entry points
│   ├── api.py           # Flask API application
│   ├── cli.py           # CLI application
│   └── worker.py        # Celery worker application
├── interfaces/           # Interface adapters
│   ├── api/             # API-specific interfaces
│   ├── cli/             # CLI-specific interfaces
│   └── worker/          # Worker-specific interfaces
├── core/                # Core business logic
│   ├── commands/        # Command handlers
│   ├── controllers/     # Controllers
│   ├── errors/          # Error handling
│   └── services/        # Business services
├── shared/              # Shared utilities
│   ├── config/          # Configuration management
│   ├── logging/         # Logging setup
│   └── utils/           # Common utilities
└── tests/               # Test suite
```

## Configuration

The application uses Doppler for configuration management. Set up your Doppler project and configure the necessary environment variables.

## Testing

Run tests with Doppler:
```bash
make test
```

## Linting and Formatting

Format code:
```bash
make format
```

Check linting:
```bash
make lint
```

## Dependencies

This project starts with minimal dependencies and adds more as needed:

- **Flask** - Web framework
- **Flask-CORS** - CORS support
- **Pydantic** - Data validation
- **Click** - CLI framework
- **Python-dotenv** - Environment variable loading
