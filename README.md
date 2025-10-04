# Insight Software Backend

A Python backend service for company similarity search and XBRL tag anomaly detection using vector embeddings and PostgreSQL with pgvector.

## Features

- **Vector Similarity Search**: Find similar companies using 1536-dimensional embeddings
- **Community-Based Clustering**: Leiden and Louvain community detection
- **XBRL Anomaly Detection**: Identify missing or extra financial reporting tags
- **Company Financial Data**: 49M+ financial facts from SEC filings
- **RESTful API**: Clean API with pagination, filtering, and search
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

# Load company data
insight-software-backend-cli database load-companies data/security.csv

# Load financial facts (takes ~5 minutes)
insight-software-backend-cli database load-facts data/companyfacts.csv

# Check status
insight-software-backend-cli database status
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

### 4. Get Company Reports

```bash
# All reports
curl -X GET http://127.0.0.1:5000/v1/company_routes/1961/reports \
  -H "Content-Type: application/json" \
  -d '{}'

# Filtered by fiscal year and form type
curl -X GET http://127.0.0.1:5000/v1/company_routes/1961/reports \
  -H "Content-Type: application/json" \
  -d '{"fiscal_year": "2019", "filing_period": "FY", "form_type": "10-K"}'
```

### 5. Detect Report Anomalies

```bash
curl -X GET http://127.0.0.1:5000/v1/company_routes/1961/reports/anomalies \
  -H "Content-Type: application/json" \
  -d '{"form_type": "10-K"}'
```

Detects missing XBRL tags (common in peers but absent in target) and extra tags (rare in peers but present in target).

## Database

### PostgreSQL with pgvector

The application uses PostgreSQL 17 with the pgvector extension for efficient vector similarity search.

**Connection**: `postgresql://insight_user:insight_password@localhost:5432/insight_db`

**Tables**:
- `companies` - 5,973 companies with vector embeddings
- `company_facts` - 49M+ financial facts from SEC filings

### Database CLI Commands

```bash
# Initialize tables
insight-software-backend-cli database init

# Load data
insight-software-backend-cli database load-companies security.csv
insight-software-backend-cli database load-facts companyfacts.csv

# Check status
insight-software-backend-cli database status
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
│       ├── vector_search.py  # pgvector similarity search
│       └── anomaly_detection/  # XBRL tag anomaly detection
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

## Key Technologies

- **Flask** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL 17** - Database
- **pgvector** - Vector similarity search
- **Marshmallow** - Schema validation
- **Click** - CLI framework
- **Alembic** - Database migrations
- **NumPy** - Statistical computations

## Data Sources

Place your data files in the `data/` directory (gitignored):

- **data/security.csv**: Company profiles with vector embedding
- **data/companyfacts.csv**: Financial facts from SEC filings