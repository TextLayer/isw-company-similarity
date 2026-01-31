# ISW Company Similarity

A Python service for discovering similar public companies across jurisdictions using vector embeddings, revenue data, and PostgreSQL with pgvector.

## Features

- **Multi-Jurisdiction Entity Collection**: Collect entities from SEC EDGAR (US) and ESEF (EU/UK)
- **Automated Enrichment**: Extract business descriptions from filings, web search fallback with LLM synthesis
- **Revenue Extraction**: Parse XBRL data with automatic currency conversion to USD
- **Vector Similarity Search**: Find similar entities using OpenAI embeddings and pgvector
- **Community Detection**: Leiden clustering for grouping similar entities
- **RESTful API**: CRUD operations with pagination and search
- **Resumable Operations**: Skip already-enriched entities, resume interrupted jobs

## Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop
- API Keys: OpenAI, Perplexity (optional), Firecrawl (optional)

### Installation

```bash
# Install dependencies
uv sync

# Start PostgreSQL with pgvector
docker-compose up -d

# Run migrations
uv run alembic upgrade head

# Check database status
uv run isw-cli database status
```

### Configuration

Create a `.env` file:

```bash
# Database
DATABASE_URL=postgresql://insight_user:insight_password@localhost:5432/insight_db

# Required
SEC_USER_AGENT="YourCompany admin@yourcompany.com"
OPENAI_API_KEY=sk-...

# Optional (for web search fallback)
PERPLEXITY_API_KEY=pplx-...
FIRECRAWL_API_KEY=fc-...

# Flask
FLASK_APP=isw.applications.api:app
FLASK_CONFIG=DEV
```

## CLI Usage

### Collect Entities

```bash
# Collect from SEC EDGAR (US companies)
uv run isw-cli entities collect --source edgar --limit 100

# Collect from ESEF (EU/UK companies)
uv run isw-cli entities collect --source esef --limit 100
```

### Enrich Entities

```bash
# Enrich all entities (descriptions, embeddings, revenue)
uv run isw-cli entities enrich

# Enrich specific jurisdiction
uv run isw-cli entities enrich --jurisdiction US --limit 50

# Force re-enrich (overwrite existing data)
uv run isw-cli entities enrich --force

# Skip specific enrichment steps
uv run isw-cli entities enrich --skip-descriptions --skip-embeddings
uv run isw-cli entities enrich --skip-revenue
```

### Normalize Revenue

```bash
# Calculate revenue percentile buckets for similarity scoring
uv run isw-cli entities normalize-revenue
```

## API Endpoints

### List Entities

```bash
curl "http://127.0.0.1:5000/v1/entities?page=1&page_size=10"
```

### Get Entity

```bash
curl "http://127.0.0.1:5000/v1/entities/0000001800"
```

### Search Similar Entities

```bash
# Find entities similar to a given entity
curl "http://127.0.0.1:5000/v1/entities/0000001800/search?similarity_threshold=0.5&max_results=10"

# Search across all communities
curl "http://127.0.0.1:5000/v1/entities/0000001800/search?filter_community=false"
```

### Create Entity

```bash
curl -X POST "http://127.0.0.1:5000/v1/entities" \
  -H "Content-Type: application/json" \
  -d '{"identifier": "0000001234", "name": "Example Corp", "jurisdiction": "US"}'
```

### Update Entity

```bash
curl -X PATCH "http://127.0.0.1:5000/v1/entities/0000001234" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated description"}'
```

### Delete Entity

```bash
curl -X DELETE "http://127.0.0.1:5000/v1/entities/0000001234"
```

## Architecture

```
isw/
├── applications/           # Entry points
│   ├── api.py             # Flask API
│   ├── cli.py             # CLI interface
│   └── worker.py          # Celery worker
├── core/
│   ├── commands/          # CRUD commands (command pattern)
│   │   └── entity/        # add, update, delete, get, search
│   ├── controllers/       # Request dispatchers
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Marshmallow validation
│   ├── services/
│   │   ├── database/      # PostgreSQL + pgvector
│   │   ├── embeddings/    # OpenAI embeddings
│   │   ├── entities/      # Entity domain
│   │   │   ├── extractors/  # Description & revenue extraction
│   │   │   ├── registry/    # EDGAR & ESEF registries
│   │   │   └── storage/     # Filing data access
│   │   ├── exchange_rate/ # Currency conversion (Frankfurter API)
│   │   ├── llm/           # LLM service (OpenAI)
│   │   ├── similarity/    # Embedding & revenue similarity
│   │   └── web_search/    # Perplexity & Firecrawl
│   └── utils/             # Shared utilities
├── interfaces/
│   ├── api/               # Flask routes & middleware
│   │   └── routes/        # entity_routes.py
│   └── cli/               # Click commands
│       └── commands/      # entities/, database.py
└── shared/
    ├── config/            # Configuration adapters
    └── logging/           # Logging setup
```

## Data Model

### Entity Fields

| Field | Type | Description |
|-------|------|-------------|
| `identifier` | string | CIK (US) or LEI (EU/UK) |
| `name` | string | Company name |
| `jurisdiction` | string | US, EU, or UK |
| `description` | text | Business description |
| `embedded_description` | vector(1536) | OpenAI embedding |
| `revenue_raw` | float | Revenue in source currency |
| `revenue_currency` | string | Source currency (USD, EUR, GBP, etc.) |
| `revenue_usd` | float | Revenue converted to USD |
| `revenue_period_end` | string | Fiscal period end date |
| `revenue_source_tags` | array | XBRL tags used for extraction |
| `norm_tot_rev` | int | Percentile bucket (1-100) |
| `leiden_community` | int | Cluster assignment |

## Development

### Running Tests

```bash
uv run pytest

# With coverage
uv run pytest --cov=isw
```

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

### Database Commands

```bash
# Start database
docker-compose up -d

# Stop database
docker-compose down

# Reset database (removes all data)
docker-compose down -v

# Connect directly
docker exec -it insight-postgres-pgvector psql -U insight_user -d insight_db
```

### Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

## Data Sources

### SEC EDGAR (US)
- Source: SEC company submissions API
- Identifier: CIK (Central Index Key)
- Filings: 10-K annual reports
- Revenue: US-GAAP XBRL tags

### ESEF (EU/UK)
- Source: XBRL.org filings index
- Identifier: LEI (Legal Entity Identifier)
- Filings: Annual Financial Reports
- Revenue: IFRS XBRL tags

## Currency Conversion

Revenue amounts are automatically converted to USD using the Frankfurter API:
- Historical rates based on fiscal period end date
- Rates cached locally (24h for latest, indefinite for historical)
- Supported currencies: USD, EUR, GBP, CHF, SEK, NOK, DKK, PLN, JPY, CAD, AUD
