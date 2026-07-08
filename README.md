# AgentFlow Desk

**Production-grade Python backend for AI-powered support workflow automation.**

AgentFlow Desk is a microservices-based intelligent workflow platform that combines FastAPI, asynchronous task queues, vector retrieval, and pluggable LLM providers (OpenAI, Claude, or local models) to automate support ticket classification, sentiment analysis, knowledge retrieval, response drafting, and intelligent routing through deterministic, auditable workflows.

---

## Core Capabilities

- **Multi-provider LLM integration** — OpenAI, Claude, or local models via unified adapter with fallback, retry, and cost tracking
- **Intelligent ticket classification** — Automated category, priority, sentiment, and urgency scoring
- **RAG-powered knowledge retrieval** — PostgreSQL + pgvector or ChromaDB for semantic search over FAQ, SOP, and historical solutions
- **Deterministic workflow orchestration** — State-machine-based execution for auditability and reproducibility
- **Async background processing** — Celery + Redis for decoupled classification, embedding, and LLM operations
- **Multi-tenant REST API** — FastAPI services with tenant isolation, rate limiting, and audit logging
- **Cloud-ready deployment** — Docker Compose for local dev, GitHub Actions CI/CD, AWS ECS/RDS/Redis production architecture

---

## Why This Architecture

This project demonstrates production-grade patterns for intelligent automation:

✓ **Deterministic over black-box** — Replaces free-form agent execution with auditable state machines  
✓ **Provider-agnostic LLM layer** — Swap models without changing business logic  
✓ **Async-first backend** — FastAPI + Celery decouples user requests from heavy AI operations  
✓ **Vector-native retrieval** — pgvector embeddings for enterprise knowledge base integration  
✓ **SaaS-ready design** — Multi-tenancy, audit trails, and usage metrics built in  

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **API Framework** | FastAPI, Pydantic v2 |
| **LLM Integration** | OpenAI SDK, Anthropic SDK, custom provider abstraction |
| **Workflow Engine** | Custom state machine with event sourcing |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL 15+ with pgvector extension |
| **Vector Store** | pgvector (production) / ChromaDB (dev) |
| **Deployment** | Docker, Docker Compose, GitHub Actions |
| **Cloud** | AWS ECS Fargate, RDS, ElastiCache, S3 |
| **Testing** | pytest, pytest-asyncio, coverage |
| **Code Quality** | ruff, mypy, pre-commit |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ with pgvector (or use Docker Compose stack)

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/agentflow-desk.git
cd agentflow-desk

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Start infrastructure (PostgreSQL, Redis, pgvector)
docker-compose up -d db redis

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000

# In another terminal: start Celery worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Run with Docker Compose

```bash
docker-compose up --build
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/docs`

---

## API Endpoints

### Ticket Operations

```http
POST   /api/v1/tickets              Create new ticket
GET    /api/v1/tickets/{id}         Get ticket details
POST   /api/v1/tickets/{id}/classify    Trigger classification
POST   /api/v1/tickets/{id}/draft-reply Draft AI response
POST   /api/v1/tickets/{id}/route       Route to team
GET    /api/v1/tickets                  List tickets (paginated)
```

### Knowledge Base

```http
POST   /api/v1/knowledge/index      Index documents
POST   /api/v1/knowledge/search     Semantic search
GET    /api/v1/knowledge/documents  List indexed documents
```

### Workflow Management

```http
GET    /api/v1/workflows/{id}       Get workflow execution details
GET    /api/v1/workflows/{id}/events   Retrieve event log
POST   /api/v1/workflows/{id}/retry    Retry failed workflow
```

### Metrics & Monitoring

```http
GET    /api/v1/metrics              System health and usage stats
GET    /api/v1/health               Health check endpoint
```

---

## Architecture Overview

```
┌─────────────┐
│   FastAPI   │  ← REST API Gateway
│   Gateway   │
└──────┬──────┘
       │
       ├─────────────────┬─────────────────┐
       ↓                 ↓                 ↓
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Workflow   │   │  LLM Svc    │   │ Retrieval   │
│   Engine    │   │  Adapter    │   │   Service   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         ↓
                  ┌─────────────┐
                  │   Celery    │  ← Async Workers
                  │   Workers   │
                  └──────┬──────┘
                         │
       ┌─────────────────┼─────────────────┐
       ↓                 ↓                 ↓
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ PostgreSQL  │   │    Redis    │   │  pgvector   │
│  (Business) │   │   (Queue)   │   │   (RAG)     │
└─────────────┘   └─────────────┘   └─────────────┘
```

### Data Flow

1. **Ingestion** — Client POST ticket → API persists to PostgreSQL → returns 202 Accepted
2. **Classification** — Celery worker pulls ticket → LLM classifies category/priority/sentiment → updates DB
3. **Retrieval** — Worker queries pgvector for relevant knowledge → retrieves top-k documents
4. **Draft Generation** — LLM generates response draft using ticket + retrieved context
5. **Routing** — Rule engine routes ticket to appropriate team based on classification
6. **Audit** — All state transitions logged to event store for replay and debugging

---

## Configuration

### Environment Variables

```bash
# LLM Provider
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=openai          # openai | anthropic | local
LLM_MODEL=gpt-4o-mini        # Model identifier

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agentflow
VECTOR_STORE=pgvector        # pgvector | chromadb

# Task Queue
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Feature Flags
ENABLE_AUDIT_LOG=true
ENABLE_COST_TRACKING=true
ENABLE_AUTO_ROUTING=true
```

---

## Development

### Run Tests

```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Code Quality

```bash
# Lint and format
ruff check app/ tests/
ruff format app/ tests/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Deployment

### Docker Production Build

```bash
docker build -t agentflow-desk:latest .
docker run -p 8000:8000 --env-file .env agentflow-desk:latest
```

### AWS ECS Deployment

See `docs/deployment/aws-ecs.md` for detailed instructions.

**Architecture:**
- ECS Fargate for API and Worker services
- RDS PostgreSQL with pgvector extension
- ElastiCache Redis for task queue
- Application Load Balancer
- S3 for attachments and audit snapshots
- CloudWatch for logging and metrics

### CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push:

1. Run tests with pytest
2. Check code quality with ruff and mypy
3. Build Docker image
4. Push to ECR (on `main` branch)
5. Deploy to staging environment

---

## Design Principles

### 1. Deterministic Workflows

Workflows are state machines, not free-form agents. Each state transition is:
- **Explicit** — Defined in code, not emergent from prompts
- **Auditable** — Logged with timestamp, inputs, outputs, and decisions
- **Reproducible** — Same inputs produce same state transitions

### 2. Provider-Agnostic LLM Layer

`LLMProvider` abstraction isolates business logic from model APIs:
- Unified interface for chat completion and embeddings
- Automatic retry with exponential backoff
- Fallback to alternative providers on failure
- Cost tracking per request

### 3. Async-First Architecture

FastAPI + Celery decouples:
- **Synchronous API** — Returns immediately with 202 Accepted
- **Async processing** — Heavy AI operations run in background workers
- **Event-driven updates** — Clients poll or subscribe to webhooks

### 4. Multi-Tenancy from Day One

Every database table includes `tenant_id`:
- Row-level security enforced in ORM
- API keys scoped to tenant
- Usage metrics and rate limits per tenant

---

## Roadmap

**Phase 1: MVP (Current)**
- [x] Project structure and documentation
- [x] Core API endpoints
- [x] LLM provider abstraction
- [x] Basic workflow engine
- [ ] PostgreSQL + pgvector integration
- [ ] Celery worker implementation
- [ ] Docker Compose stack

**Phase 2: Production Readiness**
- [ ] GitHub Actions CI/CD pipeline
- [ ] AWS ECS deployment templates
- [ ] Comprehensive test coverage (>80%)
- [ ] Performance benchmarking
- [ ] Multi-tenant API authentication
- [ ] Webhook notifications

**Phase 3: Advanced Features**
- [ ] Multi-agent workflow orchestration
- [ ] Custom prompt templates per tenant
- [ ] A/B testing framework for prompts
- [ ] Real-time metrics dashboard
- [ ] GraphQL API alternative

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Project Context

This project demonstrates production-grade patterns for the role:

> **Senior Python & AI Engineer — Intelligent Workflow Automation & Model Integration**

It showcases:
- ✓ Python 3.10+ with async/await and SOLID principles
- ✓ LLM integration (OpenAI, Claude) with prompt engineering
- ✓ Workflow automation via state machines and task queues
- ✓ REST API development with FastAPI
- ✓ Database design with SQL and vector embeddings
- ✓ Docker containerization and CI/CD setup
- ✓ Multi-tenant SaaS architecture
- ✓ AI-driven sentiment analysis and ticket classification

Built to demonstrate end-to-end ownership of intelligent backend services that are scalable, deterministic, and production-ready.
