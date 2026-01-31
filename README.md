# ISW Company Similarity

A Python service for discovering similar public companies across jurisdictions using vector embeddings, revenue data, and PostgreSQL with pgvector.

## Overview

This service collects public company data from regulatory filings (SEC EDGAR for US, ESEF/XBRL for EU/UK), extracts business descriptions and revenue figures, generates embeddings, and enables semantic similarity search across entities.

### Key Capabilities

- **Multi-Jurisdiction Collection**: Automatically fetch entities from SEC EDGAR (US) and ESEF filings (EU/UK)
- **Intelligent Description Extraction**: Extract business descriptions from 10-K filings and annual reports, with LLM synthesis and web search fallback
- **Revenue Normalization**: Parse XBRL financial data with automatic currency conversion to USD using historical exchange rates
- **Semantic Search**: Find similar companies using OpenAI embeddings and pgvector cosine similarity
- **Resumable Operations**: Skip already-enriched entities; resume interrupted enrichment jobs

## Quick Start

### Prerequisites

- Python 3.12+
- Docker Desktop (for PostgreSQL + pgvector)
- API Keys: OpenAI (required), Perplexity/Firecrawl (optional, for web search fallback)

### Installation

```bash
# Clone and install dependencies
git clone https://github.com/TextLayer/isw-company-similarity.git
cd isw-company-similarity
uv sync

# Start PostgreSQL with pgvector extension
docker-compose up -d

# Run database migrations
uv run alembic upgrade head

# Verify database connection
uv run isw-cli database status
```

### Configuration

Create a `.env` file in the project root:

```bash
# Database (default works with docker-compose)
DATABASE_URL=postgresql://insight_user:insight_password@localhost:5432/insight_db

# Required - SEC requires a user agent string
SEC_USER_AGENT="YourCompany admin@yourcompany.com"

# Required - for generating embeddings
OPENAI_API_KEY=sk-...

# Optional - enables web search fallback for description extraction
PERPLEXITY_API_KEY=pplx-...
FIRECRAWL_API_KEY=fc-...

# Flask configuration
FLASK_APP=isw.applications.api:app
FLASK_CONFIG=DEV
```

## Usage

### 1. Collect Entities

Fetch company records from regulatory registries:

```bash
# Collect from SEC EDGAR (US public companies with recent 10-K filings)
uv run isw-cli entities collect --source edgar --limit 100

# Collect from ESEF (EU/UK companies with XBRL filings)
uv run isw-cli entities collect --source esef --limit 100

# Collect from both sources
uv run isw-cli entities collect --source all --limit 200
```

**What this does:**
- EDGAR: Queries SEC submissions API for companies with 10-K filings in the last 3 years
- ESEF: Fetches from filings.xbrl.org index, filtering for annual financial reports
- Deduplicates by identifier (CIK for US, LEI for EU/UK)
- Stores basic entity records (identifier, name, jurisdiction)

### 2. Enrich Entities

Populate entities with descriptions, embeddings, and revenue data:

```bash
# Enrich all entities (only fills missing data by default)
uv run isw-cli entities enrich

# Enrich specific jurisdiction
uv run isw-cli entities enrich --jurisdiction US
uv run isw-cli entities enrich --jurisdiction EU

# Limit number of entities to process
uv run isw-cli entities enrich --limit 50

# Force re-enrichment (overwrite existing data)
uv run isw-cli entities enrich --force

# Skip specific enrichment steps
uv run isw-cli entities enrich --skip-descriptions
uv run isw-cli entities enrich --skip-embeddings
uv run isw-cli entities enrich --skip-revenue

# Disable LLM processing (use raw filing content)
uv run isw-cli entities enrich --no-llm
```

**Enrichment Pipeline:**

1. **Description Extraction**
   - For US (CIK): Extracts Item 1 "Business" section from 10-K filings
   - For EU/UK (LEI): Extracts business description fields from XBRL JSON
   - LLM synthesizes a structured 2-3 paragraph description
   - Falls back to web search (Perplexity/Firecrawl) if filing content unavailable

2. **Embedding Generation**
   - Generates OpenAI `text-embedding-3-small` vectors (1536 dimensions)
   - Truncates descriptions to 8000 characters before embedding

3. **Revenue Extraction**
   - Parses XBRL facts for revenue tags (US-GAAP or IFRS)
   - Converts to USD using historical exchange rates from Frankfurter API
   - Stores raw amount, currency, USD equivalent, period end date, and source tags

### 3. Normalize Revenue (Optional)

Calculate percentile buckets for revenue-based similarity scoring:

```bash
uv run isw-cli entities normalize-revenue
```

This assigns each entity a `norm_tot_rev` value (1-100) based on their revenue percentile across all entities with USD revenue data.

### 4. Search Similar Entities

Use the API or direct database queries to find similar entities:

```bash
# Start the API server
uv run flask run

# Search for entities similar to Apple (CIK 0000320193)
curl "http://127.0.0.1:5000/v1/entities/0000320193/search?similarity_threshold=0.6&max_results=10"
```

## API Reference

Base URL: `http://127.0.0.1:5000/v1/entities`

### List Entities

```bash
GET /entities?page=1&page_size=20
```

Returns paginated list of all entities.

### Get Entity

```bash
GET /entities/{identifier}
```

Returns single entity by CIK or LEI.

### Search Similar Entities

```bash
GET /entities/{identifier}/search
```

Query parameters:
- `similarity_threshold` (float, default 0.7): Minimum cosine similarity score
- `max_results` (int, default 10): Maximum results to return
- `filter_community` (bool, default true): Only return entities in same Leiden community

Returns entities ranked by embedding similarity.

### Create Entity

```bash
POST /entities
Content-Type: application/json

{
  "identifier": "0000001234",
  "identifier_type": "CIK",
  "jurisdiction": "US",
  "name": "Example Corporation"
}
```

### Update Entity

```bash
PATCH /entities/{identifier}
Content-Type: application/json

{
  "description": "Updated business description...",
  "revenue_raw": 1000000000,
  "revenue_currency": "USD"
}
```

### Delete Entity

```bash
DELETE /entities/{identifier}
```

## Architecture

```
isw/
├── applications/              # Entry points
│   ├── api.py                # Flask application factory
│   ├── cli.py                # Click CLI entry point
│   └── worker.py             # Celery worker (background tasks)
│
├── core/
│   ├── commands/             # Business logic (command pattern)
│   │   └── entity/           # CRUD: add, update, delete, get, search
│   ├── controllers/          # Request dispatchers
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Marshmallow validation schemas
│   ├── services/
│   │   ├── database/         # PostgreSQL connection & session management
│   │   ├── embeddings/       # OpenAI embedding generation
│   │   ├── entities/         # Core entity domain
│   │   │   ├── extractors/   # Description & revenue extraction logic
│   │   │   ├── registry/     # EDGAR & ESEF entity discovery
│   │   │   └── storage/      # Filing data retrieval adapters
│   │   ├── exchange_rate/    # Currency conversion (Frankfurter API)
│   │   ├── llm/              # LLM service wrapper (OpenAI)
│   │   ├── similarity/       # Embedding & revenue similarity algorithms
│   │   └── web_search/       # Perplexity & Firecrawl providers
│   └── utils/                # Shared utilities (prompts, text processing)
│
├── interfaces/
│   ├── api/                  # Flask HTTP layer
│   │   ├── middleware/       # Logging, proxy fixes
│   │   └── routes/           # Route definitions
│   └── cli/                  # Click command definitions
│       └── commands/
│           └── entities/     # collect, enrich, normalize-revenue
│
└── shared/
    ├── config/               # Configuration management & adapters
    └── logging/              # Structured logging setup
```

## Data Model

### Entity Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer | Auto-increment primary key |
| `identifier` | string(20) | CIK (10 digits) or LEI (20 chars), unique |
| `identifier_type` | string(10) | `"CIK"` or `"LEI"` |
| `jurisdiction` | string(10) | `"US"`, `"EU"`, or `"UK"` |
| `name` | string(500) | Company legal name |
| `description` | text | LLM-synthesized business description |
| `embedded_description` | vector(1536) | OpenAI embedding for similarity search |
| `revenue_raw` | float | Revenue in original currency |
| `revenue_currency` | string(10) | ISO currency code (USD, EUR, GBP, etc.) |
| `revenue_usd` | float | Revenue converted to USD |
| `revenue_period_end` | string(20) | Fiscal period end (YYYY-MM-DD) |
| `revenue_source_tags` | array[string] | XBRL tags used (e.g., `["us-gaap:Revenues"]`) |
| `norm_tot_rev` | integer | Revenue percentile bucket (1-100) |
| `leiden_community` | integer | Cluster assignment from community detection |
| `created_at` | timestamp | Record creation time |
| `updated_at` | timestamp | Last modification time |

## Data Sources

### SEC EDGAR (United States)

- **Registry**: SEC EDGAR company submissions API
- **Identifier**: CIK (Central Index Key) - 10-digit numeric
- **Filings**: 10-K annual reports
- **Revenue Tags**: US-GAAP taxonomy
  - `us-gaap:Revenues`
  - `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`
  - `us-gaap:SalesRevenueNet`
- **Description Source**: Item 1 "Business" section of 10-K

### ESEF (European Union / United Kingdom)

- **Registry**: filings.xbrl.org index API
- **Identifier**: LEI (Legal Entity Identifier) - 20-character alphanumeric
- **Filings**: Annual Financial Reports (AFR)
- **Revenue Tags**: IFRS taxonomy
  - `ifrs-full:Revenue`
  - `ifrs-full:RevenueFromContractsWithCustomers`
- **Description Source**: XBRL text blocks (DescriptionOfNatureOfEntitysOperationsAndPrincipalActivities, etc.)

## Currency Conversion

Revenue amounts are automatically converted to USD for cross-jurisdiction comparison:

- **Provider**: Frankfurter API (free, no API key required)
- **Rate Selection**: Uses historical rate from fiscal period end date
- **Caching**: Rates cached locally (24h TTL for latest, indefinite for historical)
- **Supported Currencies**: USD, EUR, GBP, CHF, SEK, NOK, DKK, PLN, JPY, CAD, AUD

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=isw --cov-report=html

# Run specific test file
uv run pytest tests/unit/core/services/entities/test_models.py -v
```

### Linting

```bash
# Check for issues
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

### Database Operations

```bash
# Start PostgreSQL container
docker-compose up -d

# Stop container (preserves data)
docker-compose down

# Reset database (removes all data)
docker-compose down -v

# Connect to database directly
docker exec -it insight-postgres-pgvector psql -U insight_user -d insight_db

# View logs
docker logs insight-postgres-pgvector -f
```

### Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Add new column"

# Apply all pending migrations
uv run alembic upgrade head

# Rollback last migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

## Troubleshooting

### "No entities to enrich"

Entities must be collected before enrichment:
```bash
uv run isw-cli entities collect --source all --limit 50
uv run isw-cli entities enrich
```

### Currency conversion fails

The Frankfurter API may not have rates for very recent dates. Revenue will still be stored in the original currency; only `revenue_usd` will be null.

### Web search fallback not working

Ensure you have configured either `PERPLEXITY_API_KEY` or `FIRECRAWL_API_KEY` in your `.env` file. The service will use Perplexity first, then fall back to Firecrawl.

### Embedding generation fails

Verify your `OPENAI_API_KEY` is valid and has sufficient credits. Descriptions are truncated to 8000 characters before embedding to stay within token limits.
