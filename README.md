# ISW Company Similarity

A Python backend service for company similarity search using vector embeddings and PostgreSQL with pgvector.

## Features

- **Vector Similarity Search**: Find similar companies using embeddings
- **Community-Based Clustering**: Leiden community detection
- **RESTful API**: Clean API with pagination and search
- **PostgreSQL + pgvector**: High-performance vector operations

## Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop
- PostgreSQL (via Docker)

### Installation

```bash
# Install dependencies
uv sync

# Start PostgreSQL with pgvector
docker-compose up -d

# Run Alembic migrations
source .venv/bin/activate
alembic upgrade head

# Check status
isw-company-similarity-cli database status
```

### Run API Server

```bash
export FLASK_APP=isw.applications.api:app
flask run
```

API will be available at `http://127.0.0.1:5000/v1/`

## API Endpoints

### 1. Get Companies (Paginated)

```bash
curl -X GET http://127.0.0.1:5000/v1/company_routes/ \
  -H "Content-Type: application/json" \
  -d '{"page": 1, "page_size": 10}'
```

### 2. Get Company by CIK

```bash
curl -X GET http://127.0.0.1:5000/v1/company_routes/1961
```

### 3. Find Similar Companies

```bash
# Within same community
curl -X GET http://127.0.0.1:5000/v1/company_routes/1961/similar \
  -H "Content-Type: application/json" \
  -d '{"similarity_threshold": 0.5, "max_results": 10, "filter_community": true}'

# Across all communities
curl -X GET http://127.0.0.1:5000/v1/company_routes/1961/similar \
  -H "Content-Type: application/json" \
  -d '{"filter_community": false}'
```

## Database

### PostgreSQL with pgvector

The application uses PostgreSQL 17 with the pgvector extension for efficient vector similarity search.

**Connection**: `postgresql://insight_user:insight_password@localhost:5432/insight_db`

**Tables**:
- `companies`

### Database CLI Commands

```bash
# Initialize tables
isw-company-similarity-cli database init

# Check status
isw-company-similarity-cli database status
```

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Architecture

```
isw/
├── applications/          # Application entry points
│   ├── api.py            # Flask API
│   ├── cli.py            # CLI interface
│   └── worker.py         # Celery worker
├── core/
│   ├── commands/         # Business logic (command pattern)
│   │   └── company/
│   ├── controllers/      # Request handlers
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Marshmallow validation
│   └── services/         # Core services
│       ├── database/     # Database connection & queries
│       └── vector_search.py  # pgvector similarity search
├── interfaces/
│   ├── api/              # Flask routes & middleware
│   └── cli/              # Click CLI commands
└── shared/
    ├── config/           # Configuration management
    └── logging/          # Logging setup
```

## Development

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check .
ruff format .
```

### Docker Commands

```bash
# Start database
docker-compose up -d

# Stop database
docker-compose down

# Reset database (removes all data)
docker-compose down -v

# View logs
docker logs insight-postgres-pgvector

# Connect to database
docker exec -it insight-postgres-pgvector psql -U insight_user -d insight_db
```

## Configuration

Environment variables (set in `.env` or export):

```bash
# Database
DATABASE_URL=postgresql://insight_user:insight_password@localhost:5432/insight_db

# Flask
FLASK_APP=isw.applications.api:app
FLASK_CONFIG=DEV
SECRET_KEY=your-secret-key

# Logging
DEBUG=true
```
