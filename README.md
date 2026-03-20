# Canopy

**Climate Risk Intelligence Platform for Institutional Finance**

A production-grade portfolio analytics platform that quantifies climate transition risk, models scenario stress tests, and delivers AI-powered investment insights. Built for finance teams who need to operationalize TCFD, CSRD, and ISSB disclosure requirements.

[Live Demo](https://griffinmacnaughtan.github.io/esg-copilot/) | [API Docs](http://localhost:8000/docs)

---

## Problem Statement

Institutional investors face a **$4.5 trillion annual climate investment gap**<sup>[1]</sup>. Portfolio managers need to:

1. **Quantify exposure** — Translate Scope 1/2 emissions into financial risk metrics
2. **Stress test** — Model portfolio impact under NGFS climate scenarios ($75–250/tCO2e carbon pricing)
3. **Report** — Generate TCFD/CSRD-compliant narratives for board and regulatory disclosure
4. **Act** — Identify transition leaders and laggards for engagement or divestment

Canopy combines production-grade data pipelines, quantitative risk scoring, agentic AI, and LLM-powered analysis into a single deployable platform.

<sub>[1] International Energy Agency, *World Energy Investment 2023*</sub>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CANOPY ARCHITECTURE                            │
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
                    │  Extract → Validate     │
                    │  Transform → Load       │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │      POSTGRESQL         │
                    │  emissions_data         │
                    │  climate_data           │
                    │  portfolios / scenarios │
                    └────────────┬────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Risk Engine  │  │  Scenario    │  │  ReAct Agent         │   │
│  │  - Scoring   │  │  Stress Test │  │  - Tool use          │   │
│  │  - Intensity │  │  - NGFS      │  │  - Multi-step plan   │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Vector Store │  │  LLM Copilot │  │  Eval Framework      │   │
│  │  - Chunking  │  │  - RAG       │  │  - Rubric scorer     │   │
│  │  - Cosine    │  │  - Streaming │  │  - LLM-as-judge      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   REACT/TYPESCRIPT UI   │
                    │  Dashboard              │
                    │  Scenario Engine        │
                    │  AI Copilot + Evals     │
                    │  Portfolio Builder      │
                    └─────────────────────────┘
```

---

## Key Features

### 1. Portfolio Risk Scoring
- **Transition Risk** — Carbon price exposure based on emissions intensity (tCO2e/$M revenue)
- **Physical Risk** — Sector-weighted exposure to chronic and acute climate hazards
- **Opportunity Score** — Green revenue percentage and low-carbon product pipeline
- Per-sector breakdown, top risks, quick wins

### 2. NGFS Scenario Engine
- Pre-configured scenarios: Net Zero 2050, Delayed Transition, Current Policies
- Custom scenario builder with adjustable carbon price and revenue shock
- EBITDA impact modeling and emissions delta projections

### 3. Agentic AI Analyst
An autonomous **ReAct (Reasoning + Acting)** agent that plans multi-step analyses, selects tools, and iterates until it can deliver a comprehensive answer.

- **5 registered tools**: portfolio analysis, scenario stress tests, EPA emissions queries, semantic document search, portfolio comparison
- Streaming SSE endpoint exposes thought → action → observation in real time
- Low-temperature tool calling for reliable structured output
- Configurable iteration limits with graceful degradation

### 4. Vector Store & Semantic RAG
Embedding-based retrieval replaces naive text concatenation with proper chunking and cosine similarity search.

- **Sentence-aware chunker** with configurable overlap to preserve cross-boundary context
- **Pluggable embedding providers**: OpenAI `text-embedding-3-small` for production, deterministic hash for testing
- **In-memory vector store** with numpy — designed for fast prototyping, swappable with pgvector

### 5. LLM Evaluation Framework
Systematic quality assessment — not anecdotal prompt testing. 17 curated eval cases across 4 categories:

| Category | What it tests |
|---|---|
| ✅ Good prompts | Should produce data-driven, actionable, well-structured responses |
| ❌ Bad prompts | Off-topic, empty, or informal inputs handled gracefully |
| 🛡️ Adversarial | Prompt injection, jailbreaking, credential exfiltration, XSS |
| 🔲 Edge cases | Zero-emission portfolios, CSRD×ISSB regulatory cross-references |

- **Dual scoring**: fast rubric scorer for CI + LLM-as-judge for deep semantic evaluation
- **Keyword enforcement**: expected/forbidden keywords with automatic score penalties
- **Three entry points**: CLI (`python -m evals.run_evals`), HTTP API (`POST /evals/run`), frontend Evals tab with visual drill-down

### 6. AI-Powered Copilot
- RAG pipeline injecting portfolio context, uploaded documents, and vector search results
- Streaming responses via Server-Sent Events
- Source attribution and confidence scoring
- Multi-provider support (Claude Sonnet 4, GPT-4o)

### 7. Climate Data Pipeline
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
| **Embeddings** | OpenAI text-embedding-3-small, numpy | Vector search for RAG |
| **Pipeline** | Prefect 2.x, httpx | Orchestrated data ingestion |
| **Observability** | structlog | Structured JSON logging |
| **Testing** | pytest, Vitest, MSW | Unit + integration + eval coverage |
| **Deployment** | Docker, GitHub Actions | Multi-stage builds, CI/CD |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 (optional — SQLite default for local dev)

### 1. Clone and Setup Backend

```bash
git clone https://github.com/griffinmacnaughtan/canopy.git
cd canopy/backend

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

## LLM Evaluations

Run the eval suite to measure copilot response quality:

```bash
cd backend

# Run all eval datasets with the rubric scorer
python -m evals.run_evals

# Run a specific dataset
python -m evals.run_evals --dataset safety --scorer rubric

# Use LLM-as-judge for deeper semantic scoring
python -m evals.run_evals --dataset climate_copilot --scorer llm

# Limit cases for quick iteration
python -m evals.run_evals --max-cases 5
```

Or trigger via the HTTP API:

```bash
curl -X POST http://localhost:8000/evals/run \
  -H "Content-Type: application/json" \
  -d '{"dataset": "climate_copilot"}'
```

Or use the **Evals tab** in the copilot workspace for a visual dashboard with score heatmaps and per-case drill-down.

---

## Project Structure

```
canopy/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── config.py            # Pydantic settings
│   │   ├── risk.py              # Scoring algorithms
│   │   ├── routes/              # API route modules
│   │   │   ├── health.py
│   │   │   ├── portfolios.py
│   │   │   ├── scoring.py
│   │   │   ├── copilot.py
│   │   │   ├── agents.py       # Agentic AI endpoints
│   │   │   └── evals.py        # Eval framework endpoint
│   │   ├── agents/              # ReAct agent framework
│   │   │   ├── base.py         # Agent executor + ReAct loop
│   │   │   ├── tools.py        # Tool definitions
│   │   │   └── climate_agent.py
│   │   ├── vectorstore/         # Semantic search
│   │   │   ├── chunker.py      # Document chunking
│   │   │   ├── embeddings.py   # Embedding providers
│   │   │   └── store.py        # Cosine similarity store
│   │   ├── database/            # SQLAlchemy models & connection
│   │   ├── llm/                 # LLM provider abstraction
│   │   └── pipeline/            # Prefect ETL pipeline
│   │       ├── extractors/      # NOAA, EPA, World Bank
│   │       ├── transformers/
│   │       ├── validators/
│   │       └── loaders/
│   ├── evals/                   # LLM evaluation framework
│   │   ├── framework.py         # EvalRunner, EvalCase, EvalResult
│   │   ├── scorers.py           # RubricScorer, LLMJudgeScorer
│   │   ├── run_evals.py         # CLI entry point
│   │   └── datasets/            # Curated test cases
│   │       ├── climate_copilot.py
│   │       └── safety.py
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_risk.py
│   │   │   ├── test_agents.py
│   │   │   ├── test_vectorstore.py
│   │   │   └── test_evals.py
│   │   └── integration/
│   ├── alembic/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client + mock data
│   │   ├── components/
│   │   │   ├── dashboard/
│   │   │   ├── copilot/
│   │   │   │   ├── CopilotWorkspace.tsx
│   │   │   │   ├── EvalPanel.tsx    # Eval visualization
│   │   │   │   └── StreamingResponse.tsx
│   │   │   ├── portfolio/
│   │   │   └── ui/
│   │   ├── hooks/
│   │   └── contexts/
│   ├── Dockerfile
│   └── vite.config.ts
├── .github/workflows/
├── docker-compose.yml
└── .env.example
```

---

## Design Decisions

### Why FastAPI over Flask/Django?
- Native async for LLM streaming and concurrent API calls
- Automatic OpenAPI documentation
- Pydantic validation reduces boilerplate

### Why Prefect over Airflow?
- Pythonic API with native async support
- No separate scheduler daemon — simpler deployment
- Better local dev experience at this scale

### Why a ReAct agent instead of a chain?
- Multi-step analysis needs dynamic tool selection — a fixed chain can't decide at runtime whether to run a scenario, query emissions, or search documents
- The thought → action → observation loop is self-correcting: the agent sees tool errors and tries alternatives
- Streaming the reasoning trace builds user trust in the AI's analysis

### Why an in-memory vector store?
- For the current document scale (< 100k chunks), numpy cosine similarity is fast and simple
- The `EmbeddingProvider` abstraction makes it trivial to swap in pgvector or Pinecone when scale demands it
- Hash-based test embeddings mean the full vector store test suite runs in < 1s with zero API calls

### Why a rubric scorer + LLM judge?
- Rubric scoring is deterministic and fast — runs in CI without LLM API keys or costs
- LLM-as-judge catches semantic issues (tone, reasoning quality) that keyword heuristics miss
- Auto-fallback: if the judge LLM errors out, the rubric scorer takes over gracefully

### Why separate extractors/transformers/loaders?
- **Testability**: Each component can be unit tested in isolation
- **Reusability**: Transformers work across multiple sources
- **Observability**: Clear logging at each pipeline stage

---

## Testing

```bash
# Backend tests
cd backend
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Run LLM evals (rubric scorer, no API keys needed)
python -m evals.run_evals --scorer rubric

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
| `/agent` | POST | Agentic analyst (sync) |
| `/agent/stream` | POST | Agentic analyst (streaming SSE) |
| `/evals/run` | POST | Run LLM evaluation suite |
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

*At least one LLM API key required for copilot and agent functionality.

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
