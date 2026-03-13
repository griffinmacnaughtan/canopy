# Canopy

**Climate Risk Intelligence Platform for Institutional Finance**

A production-grade portfolio analytics platform that quantifies climate transition risk, models scenario stress tests, and delivers AI-powered investment insights. Built for finance teams who need to operationalize TCFD, CSRD, and ISSB disclosure requirements.

[Live Demo](https://griffinmacnaughtan.github.io/esg-copilot/) | [API Docs](http://localhost:8000/docs)

---

## Problem Statement

Institutional investors face a **$4.5 trillion annual climate investment gap**<sup>[1]</sup>. Portfolio managers need to:

1. **Quantify exposure** - Translate Scope 1/2 emissions into financial risk metrics
2. **Stress test** - Model portfolio impact under NGFS climate scenarios ($75-250/tCO2e carbon pricing)
3. **Report** - Generate TCFD/CSRD-compliant narratives for board and regulatory disclosure
4. **Act** - Identify transition leaders and laggards for engagement or divestment

Canopy addresses this problem by combining production-grade data pipelines, quantitative risk scoring, and LLM-powered analysis into a single deployable platform.

<sub>[1] International Energy Agency, *World Energy Investment 2023*: "Clean energy investment needs to reach $4.5 trillion annually by 2030 for net zero by 2050." [iea.org/reports/world-energy-investment-2023](https://www.iea.org/reports/world-energy-investment-2023)</sub>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CANOPY ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NOAA Climate  │     │   EPA GHGRP     │     │  World Bank     │
│   Data API      │     │   Emissions     │     │  Climate API    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   PREFECT ORCHESTRATOR  │
                    │  ┌──────────────────┐   │
                    │  │ Extract → Validate│   │
                    │  │ Transform → Load  │   │
                    │  └──────────────────┘   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      POSTGRESQL         │
                    │  ┌────────────────────┐ │
                    │  │ emissions_data     │ │
                    │  │ climate_data       │ │
                    │  │ portfolios         │ │
                    │  │ scenarios          │ │
                    │  └────────────────────┘ │
                    └────────────┬────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Risk Engine  │  │  Scenario    │  │   Claude/GPT RAG     │   │
│  │  - Scoring   │  │  Stress Test │  │   - Context Build    │   │
│  │  - Intensity │  │  - NGFS      │  │   - Streaming SSE    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   REACT/TYPESCRIPT UI   │
                    │  ┌────────────────────┐ │
                    │  │ Dashboard          │ │
                    │  │ Scenario Engine    │ │
                    │  │ AI Copilot         │ │
                    │  │ Portfolio Builder  │ │
                    │  └────────────────────┘ │
                    └─────────────────────────┘
```

---

## Key Features

### 1. Portfolio Risk Scoring
- **Transition Risk**: Carbon price exposure based on emissions intensity (tCO2e/$M revenue)
- **Physical Risk**: Sector-weighted exposure to chronic and acute climate hazards
- **Opportunity Score**: Green revenue percentage and low-carbon product pipeline

### 2. NGFS Scenario Engine
- Pre-configured scenarios: Net Zero 2050, Delayed Transition, Current Policies
- Custom scenario builder with adjustable carbon price and revenue shock parameters
- EBITDA impact modeling and emissions delta projections

### 3. AI-Powered Copilot
- RAG pipeline injecting portfolio context and uploaded documents
- Streaming responses via Server-Sent Events
- Source attribution and confidence scoring
- Multi-provider support (Claude Sonnet 4, GPT-4o)

### 4. Climate Data Pipeline
- Automated ingestion from NOAA, EPA GHGRP, World Bank Climate API
- Prefect-orchestrated ETL with validation, staging, and incremental loading
- Schema validation and anomaly detection

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18, TypeScript, Vite | SPA with SSR-ready architecture |
| **UI** | Tailwind CSS, Radix UI, Framer Motion | Accessible design system |
| **State** | TanStack Query, React Context | Server state + local state |
| **Backend** | FastAPI, Pydantic, SQLAlchemy 2.0 | Async API with type safety |
| **Database** | PostgreSQL 16, Alembic | Relational store with migrations |
| **LLM** | Anthropic Claude, OpenAI GPT | Multi-provider abstraction |
| **Pipeline** | Prefect 2.x, httpx | Orchestrated data ingestion |
| **Observability** | structlog | Structured JSON logging |
| **Testing** | pytest, Vitest, MSW | Unit + integration coverage |
| **Deployment** | Docker, GitHub Actions | Multi-stage builds, CI/CD |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (optional, SQLite default for local dev)

### 1. Clone and Setup Backend

```bash
git clone https://github.com/griffinmacnaughtan/esg-copilot.git
cd esg-copilot/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --port 8000
```

### 2. Setup Frontend

```bash
cd ../frontend
npm install
npm run dev
```

### 3. Run with Docker (Full Stack)

```bash
docker compose up --build
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Data Pipeline

The pipeline extracts climate and emissions data from multiple sources:

```bash
# Run pipeline manually
cd backend
python -m app.pipeline.flows --no-epa  # Skip EPA if testing

# Schedule with Prefect
prefect deployment build app/pipeline/flows.py:climate_data_flow \
  --name daily-climate \
  --cron "0 6 * * *"
prefect deployment apply climate_data_flow-deployment.yaml
```

### Data Sources

| Source | Data Type | Update Frequency |
|--------|-----------|------------------|
| NOAA CDO | Temperature, precipitation, extreme events | Daily |
| EPA GHGRP | Facility-level GHG emissions | Annual |
| World Bank | Climate projections (RCP scenarios) | Static |

---

## Project Structure

```
esg-copilot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── config.py            # Pydantic settings
│   │   ├── exceptions.py        # Custom error handling
│   │   ├── routes/              # API route modules
│   │   │   ├── health.py
│   │   │   ├── portfolios.py
│   │   │   ├── scoring.py
│   │   │   ├── documents.py
│   │   │   └── copilot.py
│   │   ├── database/            # SQLAlchemy models & connection
│   │   ├── llm/                 # LLM provider abstraction
│   │   ├── pipeline/            # Prefect ETL pipeline
│   │   │   ├── extractors/      # NOAA, EPA, World Bank
│   │   │   ├── transformers/    # Climate, emissions
│   │   │   ├── validators/      # Schema, quality checks
│   │   │   ├── loaders/         # Staging, PostgreSQL
│   │   │   └── flows.py         # Prefect orchestration
│   │   └── risk.py              # Scoring algorithms
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── alembic/                 # Database migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client + mock data
│   │   ├── components/          # React components
│   │   │   ├── dashboard/
│   │   │   ├── copilot/
│   │   │   ├── portfolio/
│   │   │   └── ui/
│   │   ├── hooks/               # Custom React hooks
│   │   └── contexts/            # State management
│   ├── Dockerfile
│   └── vite.config.ts
├── .github/workflows/           # CI/CD
├── docker-compose.yml
└── .env.example
```

---

## Design Decisions

### Why FastAPI over Flask/Django?
- Native async support for LLM streaming and concurrent API calls
- Automatic OpenAPI documentation
- Pydantic validation reduces boilerplate

### Why Prefect over Airflow?
- Pythonic API with native async support
- Simpler deployment (no separate scheduler daemon)
- Better local development experience
- Lower operational overhead for this scale

### Why separate extractors/transformers/loaders?
- **Testability**: Each component can be unit tested in isolation
- **Reusability**: Transformers work across multiple sources
- **Observability**: Clear logging at each pipeline stage
- **Maintainability**: Single responsibility principle

### Why SQLAlchemy 2.0 with asyncpg?
- Async queries don't block during LLM streaming
- Type-safe query building with ORM
- Alembic migrations for schema versioning

### Why RAG without vector embeddings?
For the current portfolio scale (5-20 assets, <10 documents), full-text context injection is sufficient. The entire portfolio context + documents fit within Claude's 100k token window. Vector embeddings would be overkill and add complexity without benefit.

---

## Testing

```bash
# Backend tests
cd backend
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Liveness check |
| `/health/ready` | GET | Readiness with dependency checks |
| `/portfolios` | GET | List all portfolios |
| `/portfolios` | POST | Create custom portfolio |
| `/portfolio` | GET | Get portfolio with assets |
| `/score` | GET | Calculate portfolio risk scores |
| `/scenarios` | GET | List NGFS scenarios |
| `/scenario` | POST | Run scenario stress test |
| `/upload` | POST | Upload PDF for RAG context |
| `/copilot` | POST | Non-streaming copilot |
| `/copilot/stream` | POST | Streaming SSE copilot |
| `/pipeline/stats` | GET | Pipeline data statistics |
| `/pipeline/emissions` | GET | EPA facility emissions data |
| `/pipeline/emissions/top-emitters` | GET | Top emitting facilities |
| `/pipeline/climate` | GET | Climate observations & projections |
| `/pipeline/runs` | GET | Pipeline run history |
| `/pipeline/sectors` | GET | Sectors with emissions data |

Full OpenAPI spec available at `/docs` when running locally.

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Claude API key | Yes* |
| `OPENAI_API_KEY` | GPT-4o API key | Yes* |
| `LLM_PROVIDER` | `anthropic` or `openai` | No (default: anthropic) |
| `DATABASE_URL` | PostgreSQL connection string | No (SQLite default) |
| `NOAA_API_TOKEN` | NOAA Climate Data Online token | No |
| `APP_ENV` | `development` / `production` | No |

*At least one LLM API key required for copilot functionality.

---

## Deployment

### GitHub Pages (Frontend Only)
The frontend deploys automatically to GitHub Pages on push to main.
Demo mode uses mock data when backend is unavailable.

### Full Stack (Docker)
```bash
docker compose -f docker-compose.yml up -d
```

### Production Considerations
- Set `APP_ENV=production` to disable debug mode and API docs
- Use PostgreSQL instead of SQLite
- Configure rate limiting thresholds
- Set up log aggregation (structlog outputs JSON)
- Consider Redis for session/cache layer

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

MIT

---

## Contact

Built by [Griffin MacNaughtan](https://github.com/griffinmacnaughtan).

- GitHub: [github.com/griffinmacnaughtan](https://github.com/griffinmacnaughtan)
- LinkedIn: [linkedin.com/in/griffinmacnaughtan](https://linkedin.com/in/griffinmacnaughtan)
